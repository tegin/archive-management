from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ArchiveRepository(models.Model):
    _name = "archive.repository"
    _description = "archive.repository"

    name = fields.Char(required=True)
    storage_ids = fields.One2many(
        "archive.storage", inverse_name="repository_id", readonly=True
    )
    expects_destruction = fields.Boolean(default=False)
    destruction_months = fields.Integer()
    active = fields.Boolean(default=True)
    res_model_ids = fields.Many2many("ir.model")
    repository_level_ids = fields.One2many(
        "archive.repository.level", inverse_name="repository_id"
    )
    level_max_difference = fields.Integer(required=True, default=1)
    sequence_id = fields.Many2one("ir.sequence")

    @api.multi
    def toggle_active(self):
        for repository in self.filtered(lambda r: r.active):
            if repository.storage_ids.filtered(lambda r: r.active):
                raise ValidationError(
                    _(
                        "Repositories should have no storages in order "
                        "to be archived"
                    )
                )
        return super().toggle_active()


class ArchiveRepositoryLevel(models.Model):
    _name = "archive.repository.level"
    _description = "archive.repository.level"
    _order = "repository_id, level"

    repository_id = fields.Many2one(
        "archive.repository", required=True, readonly=True
    )
    name = fields.Char(required=True)
    level = fields.Integer(required=True, default=1)
    can_assign_files = fields.Boolean(default=False)
    sequence_id = fields.Many2one("ir.sequence")

    _sql_constraints = [
        (
            "repository_levels",
            "unique(repository_id, level)",
            "Level must be unique in a repository",
        )
    ]

    def add_repository_prefix(self, names):
        res = []
        for name in names:
            rec = self.browse(name[0])
            name = "[%s] %s" % (rec.repository_id.name, name[1])
            res += [(rec.id, name)]
        return res

    @api.multi
    @api.depends("repository_id")
    def name_get(self):
        """When the user is assigned to the multi-company group,
        all of the multi-company dependent objects will be listed with the
        company as suffix, in brackets."""
        names = super(ArchiveRepositoryLevel, self).name_get()
        res = self.add_repository_prefix(names)
        return res
