# -*- coding: utf-8 -*-
{
    'name': "rod_cooperativa_aportes",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','contacts','mail', 'rod_cooperativa'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/nominal_relationship_mindef_contributions.xml',
        'views/res_config_settings.xml',
        'views/partner_payroll.xml',
        'views/rod_cooperativa_aportes_menuitem.xml',
        'views/res_partner.xml',
        'views/payroll_payments.xml',
        'views/month.xml',
        'data/sequence.xml',
        # 'views/contacts.xml',
        'wizard/init_payroll_partner.xml',
        'wizard/reconcile_contributions.xml',
        'wizard/homolagate_form.xml',
        'wizard/alert_message.xml',
    ],
}
