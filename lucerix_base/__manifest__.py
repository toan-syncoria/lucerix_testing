# -*- coding: utf-8 -*-
{
    'name': "Lucerix Base",
    'summary': "",
    'description': "",
    'author': "Syncoria",
    'website': "http://www.syncoria.com",
    'category': 'base',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sale_management'],

    # always loaded
    'data': [
        'views/sale_order_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
