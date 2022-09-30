# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.osv import expression
import re
from odoo.tools.misc import formatLang, get_lang
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    partner_id = fields.Many2one('res.partner')
    product_default_code = fields.Char(related='product_id.default_code')
    customer_product_code = fields.Char(string="Customer Product Code", compute='get_customer_product_code')

    def get_customer_product_code(self):
        for line in self:
            product_code = ''
            customer_info = self.env['product.customerinfo'].sudo().search([
                        ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                        ('name', '=', line.order_id.partner_id.id),
                    ])
            if len(customer_info) > 0:
                product_code = customer_info.product_code
            line.customer_product_code = product_code


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def name_get(self):
        # TDE: this could be cleaned a bit I think
        check = self._context.get('name_get_from_so') or False
        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (code,name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'default_code', 'product_tmpl_id'], load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids
        if not check:
            print("DEFAULT")
            if partner_ids:
                supplier_info = self.env['product.supplierinfo'].sudo().search([
                    ('product_tmpl_id', 'in', product_template_ids),
                    ('name', 'in', partner_ids),
                ])
                # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
                # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
                supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
                supplier_info_by_template = {}
                for r in supplier_info:
                    supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
            for product in self.sudo():
                variant = product.product_template_attribute_value_ids._get_combination_name()

                name = variant and "%s (%s)" % (product.name, variant) or product.name
                sellers = []
                if partner_ids:
                    product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                    sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                    if not sellers:
                        sellers = [x for x in product_supplier_info if not x.product_id]
                    # Filter out sellers based on the company. This is done afterwards for a better
                    # code readability. At this point, only a few sellers should remain, so it should
                    # not be a performance issue.
                    if company_id:
                        sellers = [x for x in sellers if x.company_id.id in [company_id, False]]
                if sellers:
                    for s in sellers:
                        seller_variant = s.product_name and (
                            variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                            ) or False
                        mydict = {
                                'id': product.id,
                                'name': seller_variant or name,
                                'default_code': s.product_code or product.default_code,
                                }
                        temp = _name_get(mydict)
                        if temp not in result:
                            result.append(temp) 
                else:
                    mydict = {
                            'id': product.id,
                            'name': name,
                            'default_code': product.default_code,
                            }
                    result.append(_name_get(mydict))
        else:
            print("sale order")
            if partner_ids:
                customer_info = self.env['product.customerinfo'].sudo().search([
                    ('product_tmpl_id', 'in', product_template_ids),
                    ('name', 'in', partner_ids),
                ])
                customer_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
                customer_info_by_template = {}
                for r in customer_info:
                    customer_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
            for product in self.sudo():
                variant = product.product_template_attribute_value_ids._get_combination_name()
                name = variant and "%s (%s)" % (product.name, variant) or product.name
                customers = []
                if partner_ids:
                    product_customer_info = customer_info_by_template.get(product.product_tmpl_id, [])
                    customers = [x for x in product_customer_info if x.product_id and x.product_id == product]
                    if not customers:
                        customers = [x for x in product_customer_info if not x.product_id]
                    # Filter out sellers based on the company. This is done afterwards for a better
                    # code readability. At this point, only a few sellers should remain, so it should
                    # not be a performance issue.
                    if company_id:
                        customers = [x for x in customers if x.company_id.id in [company_id, False]]
                if customers:
                    for s in customers:
                        print(s)
                        customer_variant = s.product_name and (
                                variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                        mydict = {
                            'id': product.id,
                            'name': customer_variant or name,
                            'default_code': s.product_code or product.default_code,
                        }
                        print(mydict)
                        temp = _name_get(mydict)
                        if temp not in result:
                            result.append(temp)
                else:
                    mydict = {
                        'id': product.id,
                        'name': name,
                        'default_code': product.default_code,
                    }
                    result.append(_name_get(mydict))
        print("name_get RESULT")
        print(result)
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            if operator in positive_operators:
                product_ids = list(
                    self._search([('default_code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
                if not product_ids:
                    product_ids = list(
                        self._search([('barcode', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                product_ids = list(self._search(args + [('default_code', operator, name)], limit=limit))
                if not limit or len(product_ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(product_ids)) if limit else False
                    product2_ids = self._search(args + [('name', operator, name), ('id', 'not in', product_ids)],
                                                limit=limit2, access_rights_uid=name_get_uid)
                    product_ids.extend(product2_ids)
            elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                product_ids = list(self._search(domain, limit=limit, access_rights_uid=name_get_uid))
            if not product_ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    product_ids = list(self._search([('default_code', '=', res.group(2))] + args, limit=limit,
                                                    access_rights_uid=name_get_uid))
            # still no results, partner in context: search on supplier info as last hope to find something
            if not product_ids and self._context.get('partner_id'):
                suppliers_ids = self.env['product.supplierinfo']._search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)], access_rights_uid=name_get_uid)
                if suppliers_ids:
                    product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit,
                                               access_rights_uid=name_get_uid)
            if not product_ids and self._context.get('partner_id'):
                customer_ids = self.env['product.customerinfo']._search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)], access_rights_uid=name_get_uid)
                if customer_ids:
                    product_ids = self._search([('product_tmpl_id.customer_ids', 'in', customer_ids)], limit=limit,
                                               access_rights_uid=name_get_uid)

        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        for i in product_ids:
            print(i)
        return product_ids


class ProductTemplate(models.Model):
    _inherit = "product.template"
    customer_ids = fields.One2many('product.customerinfo', 'product_tmpl_id', string='Customers')


class CustomerInfo(models.Model):
    _name = "product.customerinfo"
    _description = "Customer Pricelist"
    _order = 'sequence, min_qty desc, price'

    customer_review = fields.Char(string='Cust. Rev')

    name = fields.Many2one(
        'res.partner', 'Customer',
        ondelete='cascade', required=True,
        help="Customer of this product", check_company=True)
    product_name = fields.Char(
        'Customer Product Name',
        help="This customer's product name will be used when printing a request for quotation. Keep empty to use the internal one.")
    product_code = fields.Char(
        'Customer Product Code',
        help="This customer's product code will be used when printing a request for quotation. Keep empty to use the internal one.")
    sequence = fields.Integer(
        'Sequence', default=1, help="Assigns the priority to the list of product vendor.")
    product_uom = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        related='product_tmpl_id.uom_po_id',
        help="This comes from the product form.")
    min_qty = fields.Float(
        'Quantity', default=0.0, required=True, digits="Product Unit Of Measure",
        help="The quantity to purchase from this vendor to benefit from the price, expressed in the vendor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")
    price = fields.Float(
        'Price', default=0.0, digits='Product Price',
        required=True, help="The price to purchase a product")
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company.id, index=1)
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.company.currency_id.id,
        required=True)
    date_start = fields.Date('Start Date', help="Start date for this vendor price")
    date_end = fields.Date('End Date', help="End date for this vendor price")
    product_id = fields.Many2one(
        'product.product', 'Product Variant', check_company=True,
        help="If not set, the vendor price will apply to all variants of this product.")
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template', check_company=True,
        index=True, ondelete='cascade')
    product_variant_count = fields.Integer('Variant Count', related='product_tmpl_id.product_variant_count')
    delay = fields.Integer(
        'Delivery Lead Time', default=1, required=True,
        help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.")
