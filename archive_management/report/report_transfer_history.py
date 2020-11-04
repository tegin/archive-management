from odoo import _, api, models
from odoo.exceptions import UserError


class ReportFileHistory(models.AbstractModel):
    _name = "report.archive_management.report_transfer_history"
    _description = "report.archive_management.report_transfer_history"

    @api.model
    def _get_report_values(self, docids, data=None):
        res_model = data.get(
            "res_model", self.env.context.get("active_model", False)
        )
        if not res_model:
            raise UserError(_("Model is required"))
        source = self.env[res_model].browse(
            self.env.context.get("active_ids", False)
        )
        source.ensure_one()
        res = {
            "doc_ids": source.ids,
            "doc_model": source._name,
            "data": data,
            "source": source,
            "docs": source.get_transfers(),
        }
        return res
