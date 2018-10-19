from odoo import fields, models


class ArchiveDocumentTransfer(models.Model):
    _name = 'archive.document.transfer'

    document_id = fields.Many2one(
        'archive.document',
        required=True,
        readonly=True)
    src_file_id = fields.Many2one('archive.file', readonly=True)
    dest_file_id = fields.Many2one('archive.file', readonly=True)
    src_partner_id = fields.Many2one('res.partner', readonly=True)
    dest_partner_id = fields.Many2one('res.partner', readonly=True)


class ArchiveFileTransfer(models.Model):
    _name = 'archive.file.transfer'

    file_id = fields.Many2one(
        'archive.file',
        required=True,
        readonly=True)
    src_file_id = fields.Many2one('archive.file', readonly=True)
    dest_file_id = fields.Many2one('archive.file', readonly=True)
    src_partner_id = fields.Many2one('res.partner', readonly=True)
    dest_partner_id = fields.Many2one('res.partner', readonly=True)
    src_location_id = fields.Many2one('archive.location', readonly=True)
    dest_location_id = fields.Many2one('archive.location', readonly=True)
