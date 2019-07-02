# Copyright 2017 Creu Blanca
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Archive management demo',
    'version': '12.0.1.0.0',
    'author': "Eficent, Creu Blanca, Odoo Community Association (OCA)",
    'summary': 'Based on ISO 15489',
    'category': 'Medical',
    'depends': [
        'archive_management',
    ],
    'website': 'https://github.com/OCA/vertical-medical',
    "license": "LGPL-3",
    "data": [
        'data/archive_demo_data.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
