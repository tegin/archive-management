from odoo import fields, models


class ArchiveLocation(models.Model):
    _name = 'archive.location'

    name = fields.Char(
        required=True,
        default='/',
        readonly=True,
        dependant_default='default_archive_name'
    )
    description = fields.Char(
        required=True
    )
    storage_ids = fields.One2many(
        'archive.storage',
        inverse_name='location_id',
        readonly=True,
    )
    active = fields.Boolean(default=True, readonly=True)

    def default_archive_name(self, vals):
        return self.env['ir.sequence'].next_by_code(
            'archive.location') or '/'
