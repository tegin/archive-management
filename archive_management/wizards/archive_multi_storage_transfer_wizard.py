# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ArchiveMultiStorageTransferWizard(models.TransientModel):
    _name = "archive.multi.storage.transfer.wizard"
    _description = "archive.multi.storage.transfer.wizard"

    original_location_id = fields.Many2one("archive.location", required=True)
    storage_ids = fields.Many2many("archive.storage")
    repository_id = fields.Many2one("archive.repository", required=True)
    dest_location_id = fields.Many2one(
        "archive.location", string="Destination", required=True
    )

    def _prepare_storage_domain(self):
        return [
            ("repository_id", "=", self.repository_id.id),
            ("location_id", "=", self.original_location_id.id),
        ]

    def populate(self):
        domain = self._prepare_storage_domain()
        lines = self.env["archive.storage"].search(domain)
        self.storage_ids = lines
        action = self.env.ref(
            "archive_management." "archive_multi_storage_transfer_wizard_act_window"
        )
        result = action.read()[0]
        result["res_id"] = self.id
        return result

    def _transfer_vals(self, storage, multi_storage):
        return {
            "storage_id": storage.id,
            "src_storage_id": storage.storage_id.id or False,
            "src_location_id": storage.location_id.id or False,
            "src_partner_id": storage.partner_id.id or False,
            "dest_storage_id": False,
            "dest_location_id": self.dest_location_id.id or False,
            "dest_partner_id": False,
            "multi_transfer_id": multi_storage.id,
        }

    def run(self):
        self.ensure_one()
        if not self.storage_ids:
            return False
        multi_storage = self.env["archive.multi.storage.transfer"].create(
            {"dest_location_id": self.dest_location_id.id or False}
        )
        for storage in self.storage_ids:
            transfer = self.env["archive.storage.transfer"].create(
                self._transfer_vals(storage, multi_storage)
            )
            storage._transfer(transfer)
        action = self.env.ref(
            "archive_management.archive_multi_storage_transfer_action"
        )
        result = action.read()[0]
        result["res_id"] = multi_storage.id
        result["views"] = [(False, "form")]
        return result
