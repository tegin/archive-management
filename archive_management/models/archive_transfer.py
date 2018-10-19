from odoo import fields, models


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
