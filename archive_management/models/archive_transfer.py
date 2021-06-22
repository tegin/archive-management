from odoo import api, fields, models


class ArchiveFileTransfer(models.Model):
    _name = "archive.file.transfer"
    _description = "archive.file.transfer"

    file_id = fields.Many2one("archive.file", required=True, readonly=True)
    src_storage_id = fields.Many2one("archive.storage", readonly=True)
    dest_storage_id = fields.Many2one("archive.storage", readonly=True)
    src_partner_id = fields.Many2one("res.partner", readonly=True)
    dest_partner_id = fields.Many2one("res.partner", readonly=True)

    def get_transfer_report(self):
        self.ensure_one()
        res = {
            "source": self.file_id.name,
            "date": self.create_date,
            "user_id": self.create_uid.name,
            "partner_id": self.dest_partner_id.name or False,
            "location_id": False,
            "storage_id": False,
        }
        if self.dest_storage_id:
            res.update(self.dest_storage_id._position_vals(self.create_date))
        return res


class ArchiveMultiStorageTransfer(models.Model):
    _name = "archive.multi.storage.transfer"
    _description = "archive.multi.storage.transfer"

    name = fields.Char(required=True, default="/", readonly=True)
    transfer_ids = fields.One2many(
        "archive.storage.transfer",
        inverse_name="multi_transfer_id",
        readonly=True,
    )
    dest_location_id = fields.Many2one("archive.location", readonly=True)
    dest_partner_id = fields.Many2one("res.partner", readonly=True)
    dest_storage_id = fields.Many2one("archive.storage", readonly=True)

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = self.default_multi_storage_transfer_name(vals)
        return super().create(vals)

    @api.model
    def default_multi_storage_transfer_name(self, vals):
        return (
            self.env["ir.sequence"].next_by_code(
                "archive.multi.storage.transfer"
            )
            or "/"
        )


class ArchiveStorageTransfer(models.Model):
    _name = "archive.storage.transfer"
    _description = "archive.storage.transfer"

    multi_transfer_id = fields.Many2one(
        "archive.multi.storage.transfer", readonly=True, ondelete="restrict"
    )
    storage_id = fields.Many2one(
        "archive.storage", required=True, readonly=True
    )
    src_storage_id = fields.Many2one("archive.storage", readonly=True)
    dest_storage_id = fields.Many2one("archive.storage", readonly=True)
    src_partner_id = fields.Many2one("res.partner", readonly=True)
    dest_partner_id = fields.Many2one("res.partner", readonly=True)
    src_location_id = fields.Many2one("archive.location", readonly=True)
    dest_location_id = fields.Many2one("archive.location", readonly=True)

    def get_transfer_report(self):
        self.ensure_one()
        res = {
            "source": self.storage_id.name,
            "date": self.create_date,
            "user_id": self.create_uid.name,
            "storage_id": False,
            "partner_id": self.dest_partner_id.name or False,
            "location_id": self.dest_location_id.name or False,
        }
        if self.dest_storage_id:
            res.update(self.dest_storage_id._position_vals(self.create_date))
        return res
