from odoo import api, fields, models


class ArchiveFileAdd(models.TransientModel):
    _name = 'archive.file.add'

    model = fields.Char(required=True, readonly=True)
    res_id = fields.Integer(required=True, readonly=True)
    repository_id = fields.Many2one(
        'archive.repository',
        domain="[('id', 'in', repository_ids)]"
    )
    repository_ids = fields.Many2many(
        'archive.repository',
        compute='_compute_repositories'
    )

    @api.depends('model', 'res_id')
    def _compute_repositories(self):
        for record in self:
            repos = self.env['archive.file'].search([
                ('model', '=', record.model),
                ('res_id', '=', record.res_id)
            ]).mapped('repository_id')
            model = self.env['ir.model'].search([('model', '=', record.model)])
            record.repository_ids = self.env['archive.repository'].search([
                ('model_ids', '=', model.id),
                ('id', 'not in', repos.ids)
            ])

    def _file_vals(self):
        return {
            'model': self.model,
            'res_id': self.res_id,
            'repository_id': self.repository_id.id,
        }

    def _run(self):
        return self.env['archive.file'].create(self._file_vals())

    def run(self):
        self.ensure_one()
        doc = self._run()
        action = self.env.ref(
            'archive_management.archive_file_action')
        result = action.read()[0]
        res = self.env.ref('archive_management.archive_file_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = doc.id
        return result
