# -*- coding: utf-8 -*-
{
    'name': "Lucerix Ship Dates",
    'summary': """
        Ship dates customization
    """,
    'description': """
    """,
    'author': "Syncoria",
    'website': "http://www.syncoria.com",
    'category': 'Sale',
    'version': '0.1',
    'depends': ['base', 'sale', 'purchase', 'stock', 'purchase_stock', 'sale_stock'],

    'data': [
        #'security/ir.model.access.csv',
        # 'views/stock_delivery_views.xml',
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
