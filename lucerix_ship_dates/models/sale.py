# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    customer_req_date = fields.Date('Customer Req Date', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    # commitment_date = fields.Datetime('Delivery Date', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    commitment_date = fields.Datetime('Delivery Date')
    outstanding_qty = fields.Float(string='Outstanding Quantity', compute='get_outstanding_qty', store=True)
    partner_id = fields.Many2one(related='order_id.partner_id', store=True)
    client_order_ref = fields.Char(string="Customer PO#", related='order_id.client_order_ref', store=True)
    partner_shipping_id = fields.Many2one(string="Delivery Address", related='order_id.partner_shipping_id', store=True)
    date_order = fields.Datetime(string="Order Date", related='order_id.date_order', store=True)
    product_default_code = fields.Char(string="Part Number", related='product_id.default_code', store=True)

    @api.depends('product_uom_qty', 'qty_delivered')
    def get_outstanding_qty(self):
        for rec in self:
            rec.outstanding_qty = rec.product_uom_qty - rec.qty_delivered

    def write(self, vals):
        result = super(SaleOrderLine, self).write(vals)
        if 'commitment_date' in vals or 'qty_invoiced' in vals:
            self.order_id.action_recalculate_delivery_date()
        return result
    
    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        print("INHERIT _action_launch_stock_rule")
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or not line.product_id.type in ('consu','product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue
            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty
            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            if line.qty_delivered < line.product_uom_qty:
                procurements.append(self.env['procurement.group'].Procurement(
                    line.product_id, product_qty, procurement_uom,
                    line.order_id.partner_shipping_id.property_stock_customer,
                    line.name, line.order_id.name, line.order_id.company_id, values))
        if procurements:
            self.env['procurement.group'].run(procurements)
        return True

    @api.onchange("commitment_date")
    def onchange_commitment_date(self):
        if self.order_id.picking_ids and self.commitment_date:
            for picking in self.order_id.picking_ids:
                if picking.state not in ['cancel', 'done']:
                    stock_move_obj = self.env['stock.move'].search([('picking_id', '=', picking._origin.id)])
                    for move in stock_move_obj:
                        if move.product_id.id == self.product_id.id or self.env['report.stock.report_product_product_replenishment'].is_same_kit(self.product_id, move.product_id):
                            move.date_deadline = self.commitment_date

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        date_deadline = self.commitment_date or (self.order_id.date_order + timedelta(days=self.customer_lead or 0.0))
        date_planned = date_deadline - timedelta(days=self.order_id.company_id.security_lead)
        values.update({
            'group_id': group_id,
            'sale_line_id': self.id,
            'date_planned': date_planned,
            'date_deadline': date_deadline,
            'route_ids': self.route_id,
            'warehouse_id': self.order_id.warehouse_id or False,
            'partner_id': self.order_id.partner_shipping_id.id,
            'product_description_variants': self._get_sale_order_line_multiline_description_variants(),
            'company_id': self.order_id.company_id,
        })
        return values

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'


    commitment_date = fields.Datetime('Delivery Date', index=True, copy=False, store=True, compute='_compute_commitment_date',
                                      states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                      help="This is the delivery date promised to the customer. "
                                           "If set, the delivery order will be scheduled based on "
                                           "this date rather than product lead times.")
    def write(self, values):
        result = super(SaleOrderInherit, self).write(values)
        if values.get('commitment_date'):
            if self.picking_ids:
                for picking in self.picking_ids:
                    if picking.state not in ['cancel', 'done']:
                        stock_move_obj = self.env['stock.move'].search([('picking_id', '=', picking._origin.id)])
                        print(stock_move_obj)
                        for move in stock_move_obj:
                            if move.sale_line_id.commitment_date:
                                move.date_deadline = move.sale_line_id.commitment_date
                            # for line in self.order_line:
                            #     if line.commitment_date:
                            #         if move.product_id.id == line.product_id.id and line.commitment_date and move.sale_line_id == line.id:
                            #             move.date_deadline = line.commitment_date
        if values.get('order_line'):
            self.action_recalculate_delivery_date()


    def action_recalculate_delivery_date(self):
        temp = [0]
        for rec in self.order_line:
            checking_qty = rec.qty_delivered == rec.qty_invoiced == rec.product_uom_qty
            if rec.commitment_date and not checking_qty:
                temp.append(rec.commitment_date)
        temp.pop(0)
        if len(temp) > 0:
            self.commitment_date = min(temp)
        return True


    @api.depends('order_line.commitment_date')
    def _compute_commitment_date(self):
        """ commitment_date = the earliest commitment_date across all order lines. """
        for order in self:
            dates_list = order.order_line.filtered(lambda x: not x.display_type and x.commitment_date).mapped('commitment_date')
            if dates_list:
                order.commitment_date = fields.Datetime.to_string(min(dates_list))
            else:
                order.commitment_date = False

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        sale_order = self.env['sale.order'].browse(self._context.get('active_id'))
        sale_order.action_recalculate_delivery_date()
        return res