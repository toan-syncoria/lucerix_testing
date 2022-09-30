# -*- coding: utf-8 -*-
from odoo import api, models, fields, tools


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    commission_percent = fields.Float(string='Commission(%)', compute='get_commission_percent')
    commission_amount = fields.Float(string='Commission Amount', compute='get_commission_amount')
    commission_id = fields.Many2one('sale.commission', string='Commission Code', compute='get_commission_percent')

    @api.depends('product_id', 'move_id.partner_id')
    def get_commission_percent(self):
        for rec in self:
            sale_order = rec.env['sale.order'].search([('name', '=', rec.move_id.invoice_origin)], limit=1)
            commission_obj = None
            rec.commission_percent = 0
            if sale_order:
                if sale_order.partner_shipping_id.commission_id:
                    commission_obj = sale_order.partner_shipping_id.commission_id
                elif sale_order.partner_invoice_id.commission_id:
                    commission_obj = sale_order.partner_invoice_id.commission_id
                else:
                    commission_obj = sale_order.partner_id.commission_id
                    
            if commission_obj != None:
                rec.commission_percent = commission_obj.percentage or 0.0
                rec.commission_id = commission_obj.id
            else:
                rec.commission_percent = 0
                rec.commission_id = None

    @api.depends('commission_percent')
    def get_commission_amount(self):
        for rec in self:
            rec.commission_amount = 0
            if rec.commission_percent:
                rec.commission_amount = (rec.price_subtotal / 100) * rec.commission_percent

    

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        #inherit of the function from account.move to validate a new tax and the priceunit of a downpayment
        res = super(AccountMove, self).action_post()
        if self.invoice_origin != None:
            order = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
            if len(order) > 0:
                customer_ref = ''
                amount_shipping = 0
                for line in self.invoice_line_ids:
                    if line.product_id.type == 'service':
                        amount_shipping += line.price_unit

                for line in self.invoice_line_ids:
                    for customer in line.product_id.customer_ids:
                        if customer.product_code:
                            customer_ref = customer.product_code
                            break

                    amount_tax = 0
                    if line.tax_ids:
                        for tax in line.tax_ids:
                            amount_tax += tax.amount

                    if line.product_id.type != 'service':
                        self.env['sale.commission.reports'].create({
                            'invoice_id': self.id,
                            'date': order.date_order,
                            'sale_order_id': order.id,
                            'invoice_date': self.invoice_date,
                            'partner_id': order.partner_id.id,
                            'customer_reference': customer_ref,
                            'invoice_value': line.price_subtotal * (100.0 + amount_tax) / 100.0,
                            'merchandise_value': line.price_subtotal,
                            'commission_amount': line.commission_amount,
                            'commission_percent': line.commission_percent,
                            'product_id': line.product_id.id,
                            'quantity': line.quantity,
                            'price_unit': line.price_unit,
                            'commission_id': line.commission_id.id
                        })
        return res

    def remove_commission_report(self):
        report = self.env['sale.commission.reports'].search([('invoice_id', '=', self.id)])
        if report:
            report.unlink()
    def unlink(self):
        self.remove_commission_report()
        return super(AccountMove, self).unlink()
    def button_draft(self):
        self.remove_commission_report()
        return super(AccountMove, self).button_draft()
    def button_cancel(self):
        self.remove_commission_report()
        return super(AccountMove, self).button_cancel()