from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ArchiveFile(models.Model):
    _name = 'archive.file'

    name = fields.Char(
        required=True,
        default='/',
        readonly=True,
        dependant_default='default_archive_name'
    )
    model = fields.Char(required=True, readonly=True)
    res_id = fields.Integer(required=True, readonly=True)
    parent_ids = fields.One2many(
        'archive.file.storage',
        inverse_name='file_id',
        readonly=True,
    )
    parent_id = fields.Many2one(
        'archive.file.storage',
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
    partner_id = fields.Many2one(
        'res.partner',
        compute='_compute_parent',
        store=True,
        readonly=True
    )
    repository_id = fields.Many2one(
        'archive.repository', required=True, readonly=True,
    )
    expected_destruction_date = fields.Datetime()
    destruction_date = fields.Datetime(readonly=True)

    _sql_constraints = [
        ('repository_record',
         'unique(repository_id, model, res_id)',
         _('File must be unique for a record and repository'))]

    @api.depends('parent_ids')
    def _compute_parent(self):
        for rec in self:
            parent = rec.parent_ids.filtered(lambda r: not r.end_date)
            rec.parent_id = parent
            rec.storage_id = parent.storage_id
            rec.partner_id = parent.partner_id

    @property
    def res(self):
        self.ensure_one()
        return self.env[self.model].browse(self.res_id)

    def default_archive_name(self, vals):
        return self.env['ir.sequence'].next_by_code(
            'archive.file') or '/'

    def _transfer(self, transfer):
        self.parent_id.close(transfer)
        if transfer:
            self.env['archive.file.storage'].create({
                'file_id': self.id,
                'transfer_id': transfer.id,
            })

    @api.model
    def _destroy_vals(self):
        return {
            'destruction_date': fields.Datetime.now()
        }

    def destroy(self):
        for rec in self:
            rec._transfer(False)
        self.write(self._destroy_vals())

    @api.model
    def create(self, vals):
        if not vals.get('parent_ids', False):
            vals['parent_ids'] = [(0, 0, {})]
        return super().create(vals)


class ArchiveFileStorage(models.Model):
    _name = 'archive.file.storage'

    file_id = fields.Many2one(
        'archive.file',
        required=True,
        readonly=True,
    )
    storage_id = fields.Many2one(
        'archive.storage',
        related='transfer_id.dest_storage_id',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='transfer_id.dest_partner_id',
        readonly=True,
    )
    start_date = fields.Datetime(
        readonly=True,
        default=lambda r: fields.Datetime.now()
    )
    transfer_id = fields.Many2one(
        'archive.file.transfer',
        readonly=True,
    )
    end_transfer_id = fields.Many2one(
        'archive.file.transfer',
        readonly=True,
    )
    end_date = fields.Datetime(readonly=True)

    @api.constrains('file_id', 'transfer_id')
    def _check_transfer(self):
        for rec in self.filtered(lambda r: r.transfer_id):
            if rec.transfer_id.file_id != rec.file_id:
                raise ValidationError(_(
                    'File of the transfer must coincide'))

    @api.constrains('file_id', 'end_transfer_id')
    def _check_end_transfer(self):
        if self.filtered(
            lambda r: r.end_transfer_id
            and r.end_transfer_id.file_id != r.file_id
        ):
            raise ValidationError(_(
                'File of the ending transfer must coincide'))

    @api.constrains('file_id', 'transfer_id', 'end_transfer_id')
    def _check_transfer_end_transfer(self):
        for rec in self.filtered(
            lambda r: r.end_transfer_id and r.transfer_id
        ):
            transfer = rec.transfer_id
            end = rec.end_transfer_id
            if end.src_storage_id != transfer.dest_storage_id:
                raise ValidationError(_(
                    'storage of the ending transfer must coincide'))
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
