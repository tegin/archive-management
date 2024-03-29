# Copyright 2017 Creu Blanca
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Archive management system",
    "version": "14.0.1.0.0",
    "author": "Eficent, CreuBlanca, Odoo Community Association (OCA)",
    "summary": "Based on ISO 15489",
    "category": "Medical",
    "depends": ["mail"],
    "website": "https://github.com/tegin/archive-management",
    "license": "LGPL-3",
    "data": [
        "security/archive_security.xml",
        "security/ir.model.access.csv",
        "data/archive_sequence.xml",
        "views/archive_menu.xml",
        "wizards/archive_multi_storage_transfer_wizard.xml",
        "wizards/archive_file_add_views.xml",
        "wizards/archive_file_transfer_wizard_views.xml",
        "wizards/archive_storage_transfer_wizard_views.xml",
        "views/archive_repository_views.xml",
        "views/archive_file_views.xml",
        "views/archive_storage_views.xml",
        "views/archive_location_views.xml",
        "views/archive_multi_storage_transfer_views.xml",
        "report/report_transfer_history.xml",
    ],
    "installable": True,
    "auto_install": False,
}
