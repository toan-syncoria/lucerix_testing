# -*- coding: utf-8 -*-
from odoo import api, models, fields, tools, _
import time
from odoo.exceptions import UserError

# class SaleAdvancePaymentInv(models.TransientModel):
#     _inherit = "sale.advance.payment.inv"

#     def create_invoices(self):
#         order = self.env['sale.order'].browse(self.env.context.get('active_id'))
#         customer_ref = ''
#         amount_shipping = 0
#         for line in order.order_line:
#             if line.product_id.type == 'service':
#                 amount_shipping += line.price_unit
#         for line in order.order_line:
#             for customer in line.product_id.customer_ids:
#                 if customer.product_code:
#                     customer_ref = customer.product_code
#                     break

#             amount_tax = 0
#             if len(line.tax_id) > 0:
#                 for tax in line.tax_id:
#                     amount_tax += tax.amount

#             if line.product_id.type != 'service':
#                 self.env['sale.commission.reports'].create({
#                     'date': order.date_order,
#                     'sale_order_id': order.id,
#                     'partner_id': order.partner_id.id,
#                     'customer_reference': customer_ref,
#                     'invoice_value': line.price_subtotal * (100.0 + amount_tax) / 100.0,
#                     'merchandise_value': line.price_subtotal,
#                     'commission_amount': line.commission_amount,
#                     'commission_percent': line.commission_percent,
#                     'product_id': line.product_id.id,
#                     'quantity': line.product_uom_qty,
#                     'price_unit': line.price_unit,
#                     'commission_id': line.commission_id.id
#                 })

#         res = super(SaleAdvancePaymentInv, self).create_invoices()
#         return res
    
#     def _prepare_so_line(self, order, analytic_tag_ids, tax_ids, amount):
#         print("_prepare_so_line inherit")
#         context = {'lang': order.partner_id.lang}
#         so_values = {
#             'name': _('Down Payment: %s') % (time.strftime('%m %Y'),),
#             'price_unit': amount,
#             'product_uom_qty': 0.0,
#             'order_id': order.id,
#             'discount': 0.0,
#             'product_uom': self.product_id.uom_id.id,
#             'product_id': self.product_id.id,
#             'analytic_tag_ids': analytic_tag_ids,
#             'tax_id': [(6, 0, tax_ids)],
#             'is_downpayment': True,
#             'sequence': order.order_line and order.order_line[-1].sequence + 1 or 10,
#             'commission_percent': self.commission_percent,
#             'commission_amount': self.commission_amount
#         }
#         del context
#         return so_values


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    commission_percent = fields.Float(string='Commission(%)', compute='get_commission_percent')
    commission_id = fields.Many2one('sale.commission', string='Commission Code', compute='get_commission_percent')
    commission_amount = fields.Float(string='Commission Amount', compute='get_commission_amount')

    @api.depends('product_id', 'order_id.partner_id')
    def get_commission_percent(self):
        
        for rec in self:
            commission_obj = None
            if rec.order_id.partner_shipping_id.commission_id:
                commission_obj = rec.order_id.partner_shipping_id.commission_id
            elif rec.order_id.partner_invoice_id.commission_id:
                commission_obj = rec.order_id.partner_invoice_id.commission_id
            else:
                commission_obj = rec.order_id.partner_id.commission_id
                
            if commission_obj != None:
                rec.commission_percent = commission_obj.percentage or 0.0
                rec.commission_id = commission_obj.id
            else:
                rec.commission_percent = 0
                rec.commission_id = None


    @api.depends('product_id', 'price_subtotal', 'order_id.partner_id')
    def get_commission_amount(self):
        for rec in self:
            rec.commission_amount = 0
            if rec.commission_percent:
                rec.commission_amount = (rec.price_subtotal / 100) * rec.commission_percent


class SalesCommission(models.Model):
    _name = 'sale.commission'
    _rec_name = 'code'

    code = fields.Char(string='Code')
    percentage = fields.Float(string='Percentage')
    user_id = fields.Many2one('res.users', string='Salesperson')

    
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id','partner_invoice_id','partner_shipping_id')
    def onchange_partner_address(self):
        """
        Update the salesperson when the partner, Invoice address, Delivery address are changed:
        """
        commission_obj = None
        if self.partner_shipping_id.commission_id:
            commission_obj = self.partner_shipping_id.commission_id
        elif self.partner_invoice_id.commission_id:
            commission_obj = self.partner_invoice_id.commission_id
        elif self.partner_id.commission_id:
            commission_obj = self.partner_id.commission_id


        values = {}
        if commission_obj != None:
            values['user_id'] = commission_obj.user_id
        else:
            self.update({
                'user_id': False,
            })
            return

        self.update(values)
