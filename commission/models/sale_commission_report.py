# -*- coding: utf-8 -*-
from odoo import api, models, fields, tools


class SalesCommissionReport(models.Model):
    _name = 'sale.commission.reports'
    _description = "Sale Commission Report"

    date = fields.Datetime(string='Order Date')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    invoice_id = fields.Many2one("account.move", string='Invoice Number')
    invoice_date = fields.Date(string='Invoice Date')
    partner_id = fields.Many2one('res.partner', string='Customer')
    customer_reference = fields.Char(string='Customer Reference')
    invoice_value = fields.Float(string='Invoice Value')
    merchandise_value = fields.Float(string='Merchandise Value')
    commission_amount = fields.Float(string='Commission Amount')
    commission_percent = fields.Float(string='Commission (%)')
    product_id = fields.Many2one('product.product', string='Product')
    commission_id = fields.Many2one('sale.commission', string='Commission Code')
    quantity = fields.Float(string='Quantity')
    price_unit = fields.Float(string='Unit Price')

    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_commission', store=True)

    @api.depends('sale_order_id')
    def _compute_commission(self):
        print('_compute_commission')
        for record in self:
            record.currency_id = record.sale_order_id.pricelist_id.currency_id

    def action_recreate(self):
        reports = self.env['sale.commission.reports'].search([])
        for record in reports:
            account_moves = self.env['account.move'].search([('invoice_origin', '=', record.sale_order_id.name)])
            for move in account_moves:
                for line in move.invoice_line_ids:
                    if (record.product_id and record.product_id.id == line.product_id.id and record.quantity == line.quantity):
                        record.invoice_id = move.id