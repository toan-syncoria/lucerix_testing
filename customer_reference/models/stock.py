from odoo import SUPERUSER_ID, _, api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_order_line_ids = fields.One2many('sale.order.line', compute='_compute_sale_order_line')

    def _compute_sale_order_line(self):
        print("_compute_sale_order_line")
        for picking in self:
            if picking.sale_id and picking.picking_type_id.sequence_code == "OUT":
                picking.sale_order_line_ids = picking.sale_id.order_line
            else:
                picking.sale_order_line_ids = None