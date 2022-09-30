# -*- coding: utf-8 -*-
from odoo import models,fields,api

class MassSale(models.Model):
	_name = 'mass.duplicate'

	def mass_copy(self,vals):
		order_ids=[]
		model = None
		for i in vals:
			order_ids.append(i['data']['id'])
			model = i['model']
		order = self.env[model].browse(order_ids)
		for odr in order:
			odr.copy()
		return