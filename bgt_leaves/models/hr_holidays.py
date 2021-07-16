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


class HRHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    is_legal_leaves = fields.Boolean('Legal Leaves')

HRHolidaysStatus()


class Holidays(models.Model):
    _inherit = "hr.holidays"

    def _compute_total_leaves(self):
        for x in self :
            if x.holiday_status_id.is_legal_leaves and x.employee_id :
                self._cr.execute("""
                    SELECT
                        sum(h.number_of_days) AS days
                    FROM
                        hr_holidays h
                        join hr_holidays_status s ON (s.id=h.holiday_status_id)
                    WHERE
                        h.state='validate' AND
                        h.type='remove' AND
                        h.holiday_status_id=%s AND
                        s.is_legal_leaves=True AND
                        h.employee_id = %s""", (x.holiday_status_id.id,x.employee_id.id,))
                leaves = self._cr.fetchone()
                if leaves and leaves != (None,):
                    x.total_leaves = leaves[0]
                    x.sisa_leaves = x.number_of_days+leaves[0]

    not_used_quota = fields.Boolean('Potong Gaji')
    total_leaves = fields.Float('Total Leaves',compute='_compute_total_leaves')
    sisa_leaves = fields.Float('Remaining Leaves',compute='_compute_total_leaves')
    # date_from = fields.Date('Start Date', readonly=True, index=True, copy=False,
    #     states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    # date_to = fields.Date('End Date', readonly=True, copy=False,
    #     states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})



    # @api.multi
    # def action_validate(self):
    #     res = super(Holidays, self).action_validate()
    #     if not self.holiday_status_id.is_legal_leaves and self.type == 'remove' :
    #         now = datetime.now()#+timedelta(hours=7)
    #         date_from = datetime.strptime(self.date_from,'%Y-%m-%d %H:%M:%S')
    #         date_to = datetime.strptime(self.date_to,'%Y-%m-%d %H:%M:%S')
    #         kemarin = date_from+timedelta(hours=7)+timedelta(days=-1)
    #         besok = date_to+timedelta(hours=7)+timedelta(days=1)

    #         # cari jika hari ini, kemarin, dan besok ada libur nasional
    #         holidays_exist = self.search([('holiday_status_id.is_public_holiday','=',True),
    #                                         ('state','=','validate'),
    #                                         ('employee_id','=',self.employee_id.id),
    #                                         ('date_from','>=',str(kemarin)),
    #                                         ('date_to','<=',str(besok))])
    #         if not holidays_exist :
    #             kuota_exist = self.env['hr.kuota'].search([('employee_id','=',self.employee_id.id),
    #                                                         ('is_active','=',True)],limit=1)
    #             if kuota_exist :
    #                 sisa_kuota = kuota_exist.sisa_kuota
    #                 kuota_exist.write({'sisa_kuota':sisa_kuota-self.number_of_days_temp})
    #         elif not self.holiday_status_id.is_legal_leaves :
    #             self.write({"not_used_quota": True})

    #     return res

    def check_legal_leaves(self): 
        #import pdb;pdb.set_trace()  
        hol_obj = self.env["hr.holidays"]
        now = str(datetime.now()+timedelta(hours=7))
        tgl = now[8:10]
        bln = now[5:7]
        tgl_bulan = now[5:10]
        legal_leaves = self.env["hr.holidays.status"].create({'name' : 'Cuti Tahunan'+time.strftime('%Y'),
                                                                    'color_name' : 'lightblue',
                                                                    'is_legal_leaves' : True,})
        #jika bulan satu tanggal satu
        #if tgl_bulan == '01-01' :

        # cari yg secara type kontrak punya kuota
        type_exist = self.env["hr.contract.type"].search([('cuti_tahunan','>',0)])
        if type_exist :
            type_id = type_exist.mapped('id')
            employee_exist = self.env["hr.employee"].search([('active','=',True)])

            for e in employee_exist :
                contract = self.env['hr.contract'].search(['|',('date_end','=',False),('date_end','>',now[:10]),('employee_id','=',e.id),
                                                        ('type_id','in',type_id)], order="id desc", limit=1)
                if contract :
                    date_start = contract.date_start
                    cont_date = datetime.strptime(date_start+' 00:00:00','%Y-%m-%d %H:%M:%S')
                    #jika start kontrak lebih dari setahun yg lalu 
                    if cont_date <= datetime.now()+timedelta(days=-365) :
                        values = {
                            'type': 'add',
                            'holiday_type': 'employee',
                            'holiday_status_id': legal_leaves.id,
                            'number_of_days_temp': type_exist.cuti_tahunan,
                            'state': 'confirm',
                            'employee_id': e.id
                        }
                        leave = hol_obj.create(values)
                        leave.action_validate()
                    else :
                        tgl_start = date_start[8:10]
                        bln_start = date_start[5:7]
                        bln_tgl_start = date_start[5:10] 
                        bln_leave = int(bln_start)
                        if int(tgl_start) >= 15 :
                            bln_leave = int(bln_start)+ 1
                        sisa_leave = 12 - bln_leave
                        if sisa_leave > 0 :
                            values = {
                            'type': 'add',
                            'holiday_type': 'employee',
                            'holiday_status_id': legal_leaves.id,
                            'number_of_days_temp': sisa_leave,
                            'state': 'confirm',
                            'employee_id': e.id
                            }
                            leave = hol_obj.create(values)
                            leave.action_validate()

                    info = str(legal_leaves.name)+' '+str(e.name)+' Created..'
                    print info

Holidays()