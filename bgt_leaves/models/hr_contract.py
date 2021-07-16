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

import time
import calendar
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from collections import OrderedDict


class HRContractType(models.Model):
    _name = 'hr.contract.type'
    _inherit = 'hr.contract.type'

    kuota = fields.Integer(string="kuota")
    tgl_kuota = fields.Integer(string="Tanggal",help="Tanggal reset kuota")
    bln_kuota = fields.Integer(string="Bulan",help="Bulan reset kuota")
    cuti_tahunan = fields.Integer(string="Cuti Tahunan")

    def check_quota(self):
        #import pdb;pdb.set_trace()
        now = str(datetime.now()+timedelta(hours=7))
        tgl = now[8:10]
        bln = now[5:7]
        type_exist = self.search([('kuota','>',0),('tgl_kuota','=',int(tgl)),('bln_kuota','=',int(bln))])
        for tp in type_exist :
            employee_exist = self.env["hr.employee"].search([('active','=',True)])
            for e in employee_exist :
                contract = self.env['hr.contract'].search(['|',('date_end','=',False),('date_end','>',now[:10]),('employee_id','=',e.id),
                                                        ('type_id','=',tp.id)], order="id desc", limit=1)
                if contract :
                    # close kuota per employee
                    e.kuota_ids.filtered(lambda x: x.is_active == True).write({"is_active" : False})
                    self.env["hr.kuota"].create({"employee_id"  : e.id,
                                                "date"          : now[:10],
                                                "total_kuota"   : tp.kuota,
                                                "sisa_kuota"    : tp.kuota,
                                                "is_active"     : True,})
                    info = 'Kuota '+str(e.name)+' Updated..'
                    print info

HRContractType()