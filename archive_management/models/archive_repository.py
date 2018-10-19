from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ArchiveRepository(models.Model):
    _name = 'archive.repository'

    name = fields.Char(
        required=True,
    )
    storage_ids = fields.One2many(
        'archive.storage',
        inverse_name='repository_id',
        readonly=True,
    )
    expects_destruction = fields.Boolean(default=False)
    destruction_months = fields.Integer()
    active = fields.Boolean(default=True)
    model_ids = fields.Many2many(
        'ir.model',
    )
    repository_level_ids = fields.One2many(
        'archive.repository.level',
        inverse_name='repository_id'
    )
    level_max_difference = fields.Integer(required=True, default=1)

    @api.multi
    def toggle_active(self):
        for repository in self.filtered(lambda r: r.active):
            if repository.storage_ids.filtered(lambda r: r.active):
                raise ValidationError(_(
                    'Repositories should have no storages in order '
                    'to be archived'
                ))
        return super().toggle_active()


class ArchiveRepositoryLevel(models.Model):
    _name = 'archive.repository.level'
    _order = 'level'

    repository_id = fields.Many2one(
        'archive.repository',
        required=True,
        readonly=True
    )
    name = fields.Char(required=True)
    level = fields.Integer(
        required=True,
        default=1
    )
    can_assign_files = fields.Boolean(default=False)

    _sql_constraints = [
        ('repository_levels', 'unique(repository_id, level)',
         'Level must be unique in a repository')
    ]
