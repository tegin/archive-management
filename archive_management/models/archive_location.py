from odoo import api, fields, models


class ArchiveLocation(models.Model):
    _name = "archive.location"
    _description = "archive.location"
    _rec_name = "description"

    name = fields.Char(required=True, default="/", readonly=True)
    description = fields.Char(required=True)
    storage_ids = fields.One2many(
        "archive.storage", inverse_name="location_id", readonly=True
    )
    active = fields.Boolean(default=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.default_archive_name(vals)
        return super().create(vals_list)

    @api.model
    def default_archive_name(self, vals):
        return self.env["ir.sequence"].next_by_code("archive.location") or "/"
