 # -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 widianajuniar@gmail.com
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from itertools import groupby
from datetime import datetime, timedelta, date

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang

import odoo.addons.decimal_precision as dp

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    @api.multi
    @api.onchange('product_uom_qty','price_unit')
    def product_disc_change(self):
        #import pdb;pdb.set_trace()
        res = super(SaleOrderLine,self).product_id_change()
        if self.product_id and self.product_id.seragam and self.product_id.min_order > 0 and self.product_id.days > 0:
            date_now = fields.date.today()
            satu_tahun_lalu = str(date_now+timedelta(days=-self.product_id.days))
            order_exist = self.env['sale.order.line'].search([('product_id','=',self.product_id.id),
                                                            ('order_id.date_order','>',satu_tahun_lalu),
                                                            ('order_id.partner_id','=',self.order_id.partner_id.id),
                                                            ('state','in',('sale','done'))])
            if order_exist :
                jml_product = sum(order_exist.mapped('product_uom_qty'))
                jatah = self.product_id.min_order - jml_product
                if jatah > 0.0 :
                    if jatah <= self.product_uom_qty :
                        self.discount = self.product_id.disc
                    else :
                        return {'warning': {'title': 'Warning',
                                        'message': 'Untuk mendapatkan discount %s percent minimal order pembelian %s ' % (self.product_id.disc,jatah)
                                        }}
            else :
                if self.product_id.min_order >= self.product_uom_qty :
                    self.discount = self.product_id.disc
                else :
                    return {'warning': {'title': 'Warning',
                                    'message': 'Untuk mendapatkan discount %s percent minimal order pembelian %s ' % (self.product_id.disc,self.product_id.min_order)
                                    }}


SaleOrderLine()