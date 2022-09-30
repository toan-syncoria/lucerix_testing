# -*- coding: utf-8 -*-
{
    'name': "Commission",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Syncoria",
    'website': "http://www.syncoria.com",
    'category': 'Uncategorized',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account','customer_reference'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/commision_view.xml',
        'views/partner_view.xml',
        'views/commission_reporting.xml',

        # 'views/sale_order_view.xml',
        # 'views/account_move_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
