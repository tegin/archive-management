from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ArchiveStorage(models.Model):
    _name = 'archive.storage'
    _parent_name = 'storage_id'

    name = fields.Char(
        required=True,
        default='/',
        readonly=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('on_place', 'On Place'),
        ('destroyed', 'Destroyed')
    ], default='draft')
    parent_ids = fields.One2many(
        'archive.storage.parent',
        inverse_name='child_id',
        readonly=True,
    )
    parent_id = fields.Many2one(
        'archive.storage.parent',
        compute='_compute_parent',
        store=True,
        readonly=True,
    )
    storage_id = fields.Many2one(
        'archive.storage',
        compute='_compute_parent',
        store=True,
        readonly=True,
    )
    parent_left = fields.Integer(
        'Left Parent',
        index=True,
    )
    parent_right = fields.Integer(
        'Right Parent',
        index=True,
    )
    child_ids = fields.One2many(
        'archive.storage',
        inverse_name='storage_id',
        readonly=True,
    )
    location_id = fields.Many2one(
        'archive.location',
        compute='_compute_parent',
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        compute='_compute_parent',
        store=True,
        readonly=True
    )
    current_partner_id = fields.Many2one(
        'res.partner',
        compute='_compute_current_partner',
        store=True,
        readonly=True
    )
    current_location_id = fields.Many2one(
        'archive.location',
        store=True,
        compute='_compute_current_location',
    )
    file_ids = fields.One2many(
        'archive.file',
        inverse_name='storage_id',
        readonly=True,
    )
    expected_destruction_date = fields.Datetime()
    destruction_date = fields.Datetime(readonly=True)
    destruction_user_id = fields.Many2one('res.users', readonly=True)
    repository_id = fields.Many2one(
        'archive.repository', readonly=True,
        related='repository_level_id.repository_id', store=True,
    )
    repository_level_id = fields.Many2one(
        'archive.repository.level',
        required=True, readonly=True,
        states={'draft': [('readonly', False)]}
    )
    level = fields.Integer(
        related='repository_level_id.level',
        readonly=True,
        store=True,
    )
    can_assign_files = fields.Boolean(
        related='repository_level_id.can_assign_files',
        readonly=True,
        store=True,
    )
    active = fields.Boolean(compute='_compute_active', store=True)

    @api.constrains('storage_id')
    def _check_recursion_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(
                _('Error! You are attempting to create a recursive storage.'))

    @api.depends('parent_ids')
    def _compute_parent(self):
        for rec in self:
            parent = rec.parent_ids.filtered(lambda r: not r.end_date)
            rec.parent_id = parent
            rec.storage_id = parent.parent_id
            rec.partner_id = parent.partner_id
            rec.location_id = parent.location_id

    @api.depends('location_id', 'storage_id.current_location_id')
    def _compute_current_location(self):
        for r in self:
            if r.location_id:
                r.current_location_id = r.location_id
            else:
                r.current_location_id = r.storage_id.current_location_id

    @api.depends('partner_id', 'storage_id.current_partner_id')
    def _compute_current_partner(self):
        for r in self:
            if r.partner_id:
                r.current_partner_id = r.partner_id
            else:
                r.current_partner_id = r.storage_id.current_partner_id

    @api.depends('destruction_date')
    def _compute_active(self):
        for r in self:
            r.active = not (r.state == 'destroyed')

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.default_archive_name(vals)
        if not vals.get('parent_ids', False):
            vals['parent_ids'] = [(0, 0, {})]
        return super().create(vals)

    @api.model
    def default_archive_name(self, vals):
        level = self.env['archive.repository.level'].browse(vals.get(
            'repository_level_id', False
        ))
        if level.sequence_id:
            return level.sequence_id._next()
        return self.env['ir.sequence'].next_by_code(
            'archive.storage') or '/'

    @api.constrains('repository_id', 'file_ids')
    def _check_repository_files(self):
        for rec in self:
            if rec.file_ids.filtered(
                lambda r: r.repository_id != rec.repository_id
            ):
                raise ValidationError(_(
                    'Repository cannot be changed if files are assigned'
                ))

    @api.constrains('repository_id', 'child_ids')
    def _check_repository_childs(self):
        for rec in self:
            if rec.child_ids.filtered(
                lambda r: r.repository_id != rec.repository_id
            ):
                raise ValidationError(_(
                    'Repository cannot be changed if files are assigned'
                ))

    @api.constrains('repository_id', 'storage_id')
    def _check_repository_storage(self):
        if self.filtered(
            lambda r: r.storage_id and
            r.storage_id.repository_id != r.repository_id
        ):
            raise ValidationError(_(
                'Repository cannot be changed if it is assigned to a storage'
            ))

    @api.model
    def _destroy_vals(self):
        return {
            'destruction_date': fields.Datetime.now(),
            'state': 'destroyed',
            'destruction_user_id': self.env.user.id,
        }

    def _transfer(self, transfer):
        self.parent_id.close(transfer)
        if self.state == 'draft':
            self.write({'state': 'on_place'})
        if transfer:
            self.env['archive.storage.parent'].create({
                'child_id': self.id,
                'transfer_id': transfer.id,
            })

    @api.multi
    def destroy(self):
        for rec in self:
            rec.file_ids.filtered(
                lambda r: not r.destruction_date).destroy()
            rec.parent_id.close()
            rec.child_ids.destroy()
        self.write(self._destroy_vals())

    @api.multi
    def get_transfers(self, start_date=False, end_date=False):
        self.ensure_one()
        data = []
        start = fields.Datetime.from_string(start_date or self.create_date)
        end = fields.Datetime.from_string(end_date or fields.Datetime.now())
        if not start_date:
            data.append({
                'source': self.name,
                'date': self.create_date,
                'message': _('Creation'),
                'user_id': self.create_uid.name
            })
        for p in self.parent_ids.filtered(
            lambda r: (
                not r.end_date or
                fields.Datetime.from_string(r.end_date) >= start
            ) and fields.Datetime.from_string(r.start_date) <= end

        ):
            if p.transfer_id and fields.Datetime.from_string(
                p.start_date
            ) >= start:
                data.append(p.transfer_id.get_transfer_report())
            if p.parent_id:
                data += p.parent_id.get_transfers(p.start_date, p.end_date)
        if not end_date and self.destruction_date:
            data.append({
                'source': self.name,
                'date': self.destruction_date,
                'message': _('Destruction'),
                'user_id': self.destruction_user_id.name,
            })
        return data

    def _position_vals(self, date):
        datetime = fields.Datetime.from_string(date)
        parent = self.parent_ids.filtered(
            lambda r: (
                not r.end_date or
                fields.Datetime.from_string(r.end_date) <= datetime
            ) and fields.Datetime.from_string(r.start_date) >= datetime
        )
        if parent.parent_id:
            res = parent.parent_id._position_vals(date)
            res['storage_id'] = '%s/%s' % (self.name, res['storage_id'])
        else:
            res = {
                'storage_id': self.name,
                'partner_id': parent.partner_id.name or False,
                'location_id': parent.location_id.name or False,
            }
        return res

    @api.multi
    def print_transfer_history(self):
        return self.env.ref(
            'archive_management.action_report_transfer_history_file'
        ).report_action(self.ids, data={'res_model': self._name})


class ArchiveStorageParent(models.Model):
    _name = 'archive.storage.parent'

    child_id = fields.Many2one(
        'archive.storage',
        required=True,
        readonly=True,
    )
    parent_id = fields.Many2one(
        'archive.storage',
        related='transfer_id.dest_storage_id',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='transfer_id.dest_partner_id',
        readonly=True,
    )
    location_id = fields.Many2one(
        'archive.location',
        related='transfer_id.dest_location_id',
        readonly=True,
    )
    start_date = fields.Datetime(
        readonly=True,
        default=lambda r: fields.Datetime.now()
    )
    transfer_id = fields.Many2one(
        'archive.storage.transfer',
        readonly=True,
    )
    end_transfer_id = fields.Many2one(
        'archive.storage.transfer',
        readonly=True,
    )
    end_date = fields.Datetime(readonly=True)

    @api.constrains('child_id', 'transfer_id')
    def _check_transfer(self):
        for rec in self.filtered(lambda r: r.transfer_id):
            if rec.transfer_id.storage_id != rec.child_id:
                raise ValidationError(_(
                    'Storage of the transfer must coincide'))

    @api.constrains('child_id', 'transfer_id', 'end_transfer_id')
    def _check_end_transfer(self):
        for rec in self.filtered(
            lambda r: r.end_transfer_id and r.transfer_id
        ):
            transfer = rec.transfer_id
            end = rec.end_transfer_id
            if end.src_storage_id != transfer.dest_storage_id:
                raise ValidationError(_(
                    'Storage of the ending transfer must coincide'))
            if end.src_location_id != transfer.dest_location_id:
                raise ValidationError(_(
                    'Location of the ending transfer must coincide'))
            if end.src_partner_id != transfer.dest_partner_id:
                raise ValidationError(_(
                    'Partner of the ending transfer must coincide'))

    def _close_vals(self, transfer):
        res = {'end_date': fields.Datetime.now()}
        if transfer:
            res['end_transfer_id'] = transfer.id
        return res

    @api.multi
    def close(self, transfer=False):
        self.write(self._close_vals(transfer))
