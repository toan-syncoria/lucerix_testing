# -*- coding: utf-8 -*-
# from odoo import http


# class AccountEdiFix(http.Controller):
#     @http.route('/account_edi_fix/account_edi_fix/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_edi_fix/account_edi_fix/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_edi_fix.listing', {
#             'root': '/account_edi_fix/account_edi_fix',
#             'objects': http.request.env['account_edi_fix.account_edi_fix'].search([]),
#         })

#     @http.route('/account_edi_fix/account_edi_fix/objects/<model("account_edi_fix.account_edi_fix"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_edi_fix.object', {
#             'object': obj
#         })
