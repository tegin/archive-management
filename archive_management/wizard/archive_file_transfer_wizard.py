from odoo import api, fields, models


class ArchiveFileTransferWizard(models.TransientModel):
    _name = 'archive.file.transfer.wizard'

    file_id = fields.Many2one(
        'archive.file',
        required=True,
        readonly=True,
    )
    repository_id = fields.Many2one(
        'archive.repository',
        related='file_id.repository_id',
        readonly=True
    )
    transfer_type = fields.Selection([
        ('storage', 'storage'),
        ('partner', 'Partner'),
    ], required=True, default='storage')
    dest_storage_id = fields.Many2one(
        'archive.storage',
        domain="["
               "('repository_id', '=', repository_id), "
               "('state', '=', 'on_place')]"
    )
    dest_partner_id = fields.Many2one('res.partner')

    @api.onchange('transfer_type')
    def _onchange_transfer_type(self):
        for rec in self:
            rec.dest_storage_id = False
            rec.dest_partner_id = False

    def _transfer_vals(self):
        return {
            'file_id': self.file_id.id,
            'src_storage_id': self.file_id.storage_id.id or False,
            'src_partner_id': self.file_id.partner_id.id or False,
            'dest_storage_id': self.dest_storage_id.id or False,
            'dest_partner_id': self.dest_partner_id.id or False,
        }

    def _run(self):
        transfer = self.env['archive.file.transfer'].create(
            self._transfer_vals())
        self.file_id._transfer(transfer)
        return transfer

    def run(self):
        self.ensure_one()
        self._run()
