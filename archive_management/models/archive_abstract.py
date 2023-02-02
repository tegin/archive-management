from odoo import fields, models


class ArchiveAbstract(models.AbstractModel):
    _name = "archive.abstract"
    _description = "archive.abstract"

    file_ids = fields.One2many("archive.file", compute="_compute_repository_files")
    file_count = fields.Integer(compute="_compute_repository_files")
    pending_archive_file = fields.Boolean(compute="_compute_repository_files")

    def _compute_repository_files(self):
        res_model = self.env["ir.model"].search([("model", "=", self._name)])
        for r in self:
            files = self.env["archive.file"].search(
                [("res_id", "=", r.id), ("res_model", "=", self._name)]
            )
            r.file_ids = files
            r.file_count = len(files)
            repos = files.mapped("repository_id")
            r.pending_archive_file = bool(
                self.env["archive.repository"].search(
                    [
                        ("res_model_ids", "=", res_model.id),
                        ("id", "not in", repos.ids),
                    ]
                )
            )

    def action_add_file(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "archive_management.archive_file_add_action"
        )
        result["context"] = {
            "default_res_id": self.id,
            "default_res_model": self._name,
        }
        return result

    def action_view_files(self):
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "archive_management.archive_file_action"
        )
        result["domain"] = [
            ("res_model", "=", self._name),
            ("res_id", "in", self.ids),
        ]
        return result
