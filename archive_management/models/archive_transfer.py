from odoo import api, fields, models


class ArchiveFileTransfer(models.Model):
    _name = 'archive.file.transfer'

    file_id = fields.Many2one(
        'archive.file',
        required=True,
        readonly=True)
    src_storage_id = fields.Many2one('archive.storage', readonly=True)
    dest_storage_id = fields.Many2one('archive.storage', readonly=True)
    src_partner_id = fields.Many2one('res.partner', readonly=True)
    dest_partner_id = fields.Many2one('res.partner', readonly=True)

    @api.multi
    def get_transfer_report(self):
        self.ensure_one()
        res = {
            'source': self.file_id.name,
            'date': self.create_date,
            'user_id': self.create_uid.name,
            'partner_id': self.dest_partner_id.name or False,
            'location_id': False,
            'storage_id': False,
        }
        if self.dest_storage_id:
            res.update(self.dest_storage_id._position_vals(self.create_date))
        return res


class ArchiveStorageTransfer(models.Model):
    _name = 'archive.storage.transfer'

    storage_id = fields.Many2one(
        'archive.storage',
        required=True,
        readonly=True)
    src_storage_id = fields.Many2one('archive.storage', readonly=True)
    dest_storage_id = fields.Many2one('archive.storage', readonly=True)
    src_partner_id = fields.Many2one('res.partner', readonly=True)
    dest_partner_id = fields.Many2one('res.partner', readonly=True)
    src_location_id = fields.Many2one('archive.location', readonly=True)
    dest_location_id = fields.Many2one('archive.location', readonly=True)

    @api.multi
    def get_transfer_report(self):
        self.ensure_one()
        res = {
            'source': self.storage_id.name,
            'date': self.create_date,
            'user_id': self.create_uid.name,
            'storage_id': False,
            'partner_id': self.dest_partner_id.name or False,
            'location_id': self.dest_location_id.name or False,
        }
        if self.dest_storage_id:
            res.update(self.dest_storage_id._position_vals(self.create_date))
        return res
