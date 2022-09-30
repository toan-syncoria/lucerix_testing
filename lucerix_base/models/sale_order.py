# -*- coding: utf-8 -*-
from odoo import api, models, fields, tools, _
import time
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('commitment_date')
    def _onchange_commitment_date(self):
        """ Warn if the commitment dates is sooner than the expected date """
        if (self.commitment_date and self.expected_date and self.commitment_date < self.expected_date):
            # return {
            #     'warning': {
            #         'title': _('Requested date is too soon.'),
            #         'message': _("The delivery date is sooner than the expected date."
            #                      "You may be unable to honor the delivery date.")
            #     }
            # }
            return

class SaleOrderOption(models.Model):
    _inherit = "sale.order.option"

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    product_id = fields.Many2one('product.product', 'Product', required=False, domain=[('sale_ok', '=', True)])
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', required=False, domain="[('category_id', '=', product_uom_category_id)]")