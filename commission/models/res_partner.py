# -*- coding: utf-8 -*-
from odoo import api, models, fields


class Respartner(models.Model):
    _inherit = 'res.partner'
    
    commission_id = fields.Many2one('sale.commission', string='Commission Code')
