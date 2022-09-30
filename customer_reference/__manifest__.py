# -*- coding: utf-8 -*-
{
    'name': "Customer Reference",
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
    'depends': ['base', 'sale','account', 'stock', 'mrp', 'lucerix_ship_dates', 'sale_stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_view.xml',
        'report/invoicing_report.xml',
        'report/stock_report_views.xml',
        'report/report_delivery_sale_order.xml',
        'views/stock_view.xml',
        'views/product_customerinfor_view.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
