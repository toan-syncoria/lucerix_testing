# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, models
from odoo.tools import float_is_zero, format_datetime, format_date, float_round
from odoo import api, fields, models, SUPERUSER_ID, _


class ReplenishmentReport(models.AbstractModel):
    _inherit = 'report.stock.report_product_product_replenishment'
    
    order_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')

    def is_same_kit(self, parent, child):
        boms_of_parent = self.env['mrp.bom'].search(['|', ('product_id', '=', parent.id), '&', ('product_id', '=', False), ('product_tmpl_id', '=', parent.product_tmpl_id.id)])
        flag = False
        for bom in boms_of_parent:
            for line in bom.bom_line_ids:
                if line.product_id.id == child.id:
                    flag = True
        return flag

    def get_delivery_date_so(self, product, quantity, order_line= None, move_out=None, move_in=None):
        print("get_delivery_date_so")
        timezone = self._context.get('tz')
        if move_out:
            print("sale.order")
            print(move_out._get_source_document())
            print(type(move_out._get_source_document()).__name__)
            print(order_line)
            if "sale.order" in type(move_out._get_source_document()).__name__ and order_line:
                so = move_out._get_source_document()
                print(so.name)
                for line in so.order_line:
                    print(line.id)
                    if (line.product_id == product and line.id == order_line.id) or self.is_same_kit(line.product_id, product):
                        print(line.commitment_date)
                        return format_datetime(self.env, line.commitment_date, timezone, dt_format=False)
            else:
                return format_datetime(self.env, move_out.date, timezone, dt_format=False)
        if move_in:
            if "purchase.order" in type(move_in._get_source_document()).__name__:
                po = move_in._get_source_document()
                for line in po.order_line:
                    if (line.product_id == product and line.product_uom_qty == quantity) or self.is_same_kit(line.product_id, product):
                        return format_datetime(self.env, line.date_planned, timezone, dt_format=False)
            else:
                return format_datetime(self.env, move_in.date, timezone, dt_format=False)

    def _prepare_report_line(self, quantity, move_out=None, move_in=None, order_line=None, replenishment_filled=True, product=False, reservation=False):
        timezone = self._context.get('tz')
        product = product or (move_out.product_id if move_out else move_in.product_id)
        is_late = move_out.date < move_in.date if (move_out and move_in) else False
        return {
            'document_in': move_in._get_source_document() if move_in else False,
            'document_out': move_out._get_source_document() if move_out else False,
            'product': {
                'id': product.id,
                'display_name': product.display_name
            },
            'replenishment_filled': replenishment_filled,
            'uom_id': product.uom_id,
            'receipt_date': self.get_delivery_date_so(product, quantity, move_in = move_in) if move_in else False,
            'delivery_date': self.get_delivery_date_so(product, quantity, order_line, move_out = move_out) if move_out else False,
            'is_late': is_late,
            'quantity': float_round(quantity, precision_rounding=product.uom_id.rounding),
            'move_out': move_out,
            'move_in': move_in,
            'reservation': reservation,
        }

    def _get_report_lines(self, product_template_ids, product_variant_ids, wh_location_ids):
        def _rollup_move_dests(move, seen):
            for dst in move.move_dest_ids:
                if dst.id not in seen:

                    seen.add(dst.id)
                    _rollup_move_dests(dst, seen)
            return seen

        def _reconcile_out_with_ins(lines, out, ins, demand, only_matching_move_dest=True):
            index_to_remove = []
            for index, in_ in enumerate(ins):
                if float_is_zero(in_['qty'], precision_rounding=out.product_id.uom_id.rounding):
                    continue
                if only_matching_move_dest and in_['move_dests'] and out.id not in in_['move_dests']:
                    continue
                taken_from_in = min(demand, in_['qty'])
                demand -= taken_from_in
                lines.append(self._prepare_report_line(taken_from_in, move_in=in_['move'], move_out=out, order_line=out.sale_line_id))
                in_['qty'] -= taken_from_in
                if in_['qty'] <= 0:
                    index_to_remove.append(index)
                if float_is_zero(demand, precision_rounding=out.product_id.uom_id.rounding):
                    break
            for index in index_to_remove[::-1]:
                ins.pop(index)
            return demand

        in_domain, out_domain = self._move_confirmed_domain(
            product_template_ids, product_variant_ids, wh_location_ids
        )
        outs = self.env['stock.move'].search(out_domain, order='priority desc, date, id')
        outs_per_product = defaultdict(lambda: [])
        for out in outs:
            outs_per_product[out.product_id.id].append(out)
        ins = self.env['stock.move'].search(in_domain, order='priority desc, date, id')
        ins_per_product = defaultdict(lambda: [])
        for in_ in ins:
            ins_per_product[in_.product_id.id].append({
                'qty': in_.product_qty,
                'move': in_,
                'move_dests': _rollup_move_dests(in_, set())
            })
        currents = {c['id']: c['qty_available'] for c in outs.product_id.read(['qty_available'])}

        lines = []
        for product in (ins | outs).product_id:
            for out in outs_per_product[product.id]:
                if out.state not in ('partially_available', 'assigned'):
                    continue
                current = currents[out.product_id.id]
                reserved = out.product_uom._compute_quantity(out.reserved_availability, product.uom_id)
                currents[product.id] -= reserved
                lines.append(self._prepare_report_line(reserved, move_out=out, reservation=True, order_line=out.sale_line_id))

            unreconciled_outs = []
            for out in outs_per_product[product.id]:
                # Reconcile with the current stock.
                current = currents[out.product_id.id]
                reserved = 0.0
                if out.state in ('partially_available', 'assigned'):
                    reserved = out.product_uom._compute_quantity(out.reserved_availability, product.uom_id)
                demand = out.product_qty - reserved
                taken_from_stock = min(demand, current)
                if not float_is_zero(taken_from_stock, precision_rounding=product.uom_id.rounding):
                    currents[product.id] -= taken_from_stock
                    demand -= taken_from_stock
                    lines.append(self._prepare_report_line(taken_from_stock, move_out=out, order_line=out.sale_line_id))
                # Reconcile with the ins.
                if not float_is_zero(demand, precision_rounding=product.uom_id.rounding):
                    demand = _reconcile_out_with_ins(lines, out, ins_per_product[out.product_id.id], demand, only_matching_move_dest=True)
                if not float_is_zero(demand, precision_rounding=product.uom_id.rounding):
                    unreconciled_outs.append((demand, out))
            if unreconciled_outs:
                for (demand, out) in unreconciled_outs:
                    # Another pass, in case there are some ins linked to a dest move but that still have some quantity available
                    demand = _reconcile_out_with_ins(lines, out, ins_per_product[product.id], demand, only_matching_move_dest=False)
                    if not float_is_zero(demand, precision_rounding=product.uom_id.rounding):
                        # Not reconciled
                        lines.append(self._prepare_report_line(demand, move_out=out, replenishment_filled=False, order_line=out.sale_line_id))
            # Unused remaining stock.
            free_stock = currents.get(product.id, 0)
            if not float_is_zero(free_stock, precision_rounding=product.uom_id.rounding):
                lines.append(self._prepare_report_line(free_stock, product=product))
            # In moves not used.
            for in_ in ins_per_product[product.id]:
                if float_is_zero(in_['qty'], precision_rounding=product.uom_id.rounding):
                    continue
                lines.append(self._prepare_report_line(in_['qty'], move_in=in_['move']))
        return lines
