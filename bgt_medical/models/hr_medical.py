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


class HRMedical(models.Model):
    _name = "hr.medical"
    _description = "Pengelolaan Kesehatan karyawan"
    _order = "name desc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    def post_mesages_medical(self,state,manager_id):
        group_user_hr = self.env['ir.model.data'].sudo().get_object('hr', 'group_hr_user')
        #import pdb;pdb.set_trace()
        partner_hr_ids = group_user_hr.users.mapped('partner_id')

        partners_hr =  map(lambda x:x['id'],partner_hr_ids)

        partners_ids = partners_hr + [manager_id]
        subject = _("Medical Document")

        body = 'Medical Document State : '+str(state)
        messages = self.message_post(body=body, subject=subject)
        messages.update({'needaction_partner_ids' : [(6, 0, partners_ids)]})
        print body
        return True

    def get_tanggal(self):
        for x in self:
            my_date = date.today()
            hari = calendar.day_name[my_date.weekday()]
            bulan = calendar.month_name[my_date.weekday()]
            x.hari_tanggal = str(my_date)[-2:]+' '+str(bulan)+' '+str(my_date)[:4]

    name = fields.Char("Number", size=25, default="New", copy=False)
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user)
    date = fields.Datetime("Created Date",default=lambda self:time.strftime("%Y-%m-%d %H:%M:%S"))
    employee_id = fields.Many2one("hr.employee","Employee", required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    identification_id = fields.Char("No KTP", related="employee_id.identification_id", store=True)
    nik = fields.Char("NIK", related="employee_id.nik", store=True)
    parent_id = fields.Many2one("hr.employee","Atasan", related="employee_id.parent_id", store=True)
    department_id = fields.Many2one("hr.department","Department", related="employee_id.department_id", store=True)
    job_id = fields.Many2one("hr.job","Job Title", related="employee_id.job_id", store=True)
    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('approved','Approved'),('done','Done'),('cancel','Cancelled')], default="draft",string="State", track_visibility='onchange')
    notes = fields.Text("Notes")
    hari_tanggal = fields.Char("Dinamic date", compute="get_tanggal")
    tanggal = fields.Date("Tanggal")
    diagnosa = fields.Text("Diagnosa Kerja")
    obat = fields.Text("Obat Yang Diberikan")
    tanggal_berobat = fields.Date("Tanggal Berobat")
    klaim_harga = fields.Float("Klaim Harga")

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Nomor duplikat !'),
    ]

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise UserError(_('Data tidak bisa di duplikasi !'))
        return super(HRMedical, self).copy(default=default)

    def write_roman(self,num):
        roman = OrderedDict()
        roman[1000] = "M"
        roman[900] = "CM"
        roman[500] = "D"
        roman[400] = "CD"
        roman[100] = "C"
        roman[90] = "XC"
        roman[50] = "L"
        roman[40] = "XL"
        roman[10] = "X"
        roman[9] = "IX"
        roman[5] = "V"
        roman[4] = "IV"
        roman[1] = "I"

        def roman_num(num):
            for r in roman.keys():
                x, y = divmod(num, r)
                yield roman[r] * x
                num -= (r * x)
                if num > 0:
                    roman_num(num)
                else:
                    break

        return "".join([a for a in roman_num(num)])


    @api.model
    def create(self,vals):
    	if not vals.get('name', False) or vals['name'] == 'New':
	        my_date = str(date.today())
	        bulan = my_date[5:7]
	        sequence = self.env['ir.sequence'].next_by_code('hr.medical') or 'Number not found !'
	        if sequence != 'Number not found !' :
	            awal = sequence[:12]
	            akhir = sequence[-4:]
	            romawi = self.write_roman(int(bulan))
	            vals['name'] = str(awal)+str(romawi)+'/'+str(akhir)
        res = super(HRMedical, self).create(vals)

        return res

    @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft' :
                raise UserError(_('Data yang bisa dihapus hanya yg berstatus draft'))
        return super(HRMedical, self).unlink()

    @api.multi
    def button_confirm(self):
        for i in self:
            # cek jika harus approve pimpinan dept
            #if not i.department_id.manager_id :
            #    raise UserError(_('Manager untuk department %s belum di set !') % (str(i.department_id.name)))
            #elif i.department_id.manager_id.user_id.id != i._uid :
            #    raise UserError(_('Anda tidak punya akses untuk menyetujui dokumen ini ! (Manager Dept : %s) ') % (str(i.department_id.manager_id.name)))
            #manager = [i.department_id.manager_id.user_id.id]
            #i.post_mesages_medical('Confirmed', manager)
            i.write({'state':'confirmed'})
        return True

    @api.multi
    def button_approve(self):
        for i in self:
            #manager = [i.department_id.manager_id.user_id.id]
            #i.post_mesages_medical('Approved', manager)
            i.write({'state':'approved'})
        return True

    @api.multi
    def button_cancel(self):
        for i in self:
            #manager = [i.department_id.manager_id.user_id.id]
            #i.post_mesages_medical('Cancelled', manager)
            i.write({'state':'cancel'})
        return True

    @api.multi
    def button_set_to_draft(self):
        for i in self:
            #manager = [i.department_id.manager_id.user_id.id]
            #i.post_mesages_medical('Set to Draft', manager)
            i.write({'state':'draft'})
        return True

    @api.multi
    def button_claim(self):
        for i in self:
            if i.klaim_harga <= 0.0 :
                raise UserError(_('Klaim harga tidak bisa diisi nol !'))
            i.write({'state':'done'})
        return True

HRMedical()