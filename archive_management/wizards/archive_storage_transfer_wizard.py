from odoo import api, fields, models


class ArchiveStorageTransferWizard(models.TransientModel):
    _name = 'archive.storage.transfer.wizard'
    _description = 'archive.storage.transfer.wizard'

    storage_id = fields.Many2one(
        'archive.storage',
        required=True,
        readonly=True
    )
    repository_id = fields.Many2one(
        'archive.repository',
        related='storage_id.repository_id',
        readonly=True
    )
    min_level = fields.Integer(
        compute='_compute_level'
    )
    max_level = fields.Integer(
        compute='_compute_level'
    )
    transfer_type = fields.Selection([
        ('storage', 'storage'),
        ('location', 'Location'),
        ('partner', 'Partner'),
    ], required=True, default='storage')
    dest_storage_id = fields.Many2one(
        'archive.storage',
        domain="["
               "('repository_id', '=', repository_id), "
               "('state', '=', 'on_place'),"
               "('level', '<=', max_level),"
               "('level', '>=', min_level)]"
    )
    dest_location_id = fields.Many2one('archive.location')
    dest_partner_id = fields.Many2one('res.partner')

    @api.depends('storage_id', 'repository_id')
    def _compute_level(self):
        for r in self:
            r.min_level = r.storage_id.level + 1
            r.max_level = (
                r.storage_id.level + r.repository_id.level_max_difference)

    @api.onchange('transfer_type')
    def _onchange_transfer_type(self):
        for rec in self:
            rec.dest_storage_id = False
            rec.dest_location_id = False
            rec.dest_partner_id = False

    def _transfer_vals(self):
        return {
            'storage_id': self.storage_id.id,
            'src_storage_id': self.storage_id.storage_id.id or False,
            'src_location_id': self.storage_id.location_id.id or False,
            'src_partner_id': self.storage_id.partner_id.id or False,
            'dest_storage_id': self.dest_storage_id.id or False,
            'dest_location_id': self.dest_location_id.id or False,
            'dest_partner_id': self.dest_partner_id.id or False,
        }

    def _run(self):
        transfer = self.env['archive.storage.transfer'].create(
            self._transfer_vals())
        self.storage_id._transfer(transfer)
        return transfer

    def run(self):
        self.ensure_one()
        self._run()
