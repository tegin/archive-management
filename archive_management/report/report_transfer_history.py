from odoo import api, models, _
from odoo.exceptions import UserError


class ReportFileHistory(models.AbstractModel):
    _name = 'report.archive_management.report_transfer_history'

    @api.model
    def get_report_values(self, docids, data=None):
        model = data.get(
            'model', self.env.context.get('active_model', False))
        if not model:
            raise UserError(_('Model is required'))
        source = self.env[model].browse(
            self.env.context.get('active_ids', False))
        source.ensure_one()
        res = {
            'doc_ids': source.ids,
            'doc_model': source._name,
            'data': data,
            'source': source,
            'docs': source.get_transfers(),
        }
        return res
