# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Duplicate Records',
    'version': '1.0',
    'author':'Syncoria',
    'category': 'Extra Tools',
    'summary': 'Duplicate in List view',
    'description': """Mass Duplicate""",
    'website': 'http://www.syncoria.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/web_duplicate_views.xml',
        ],
   
    'installable': True,
    'auto_install': False,
    'application': True,
}
