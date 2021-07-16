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


class HRMutasi(models.Model):
    _name = "hr.mutasi"
    _description = "Pengelolaan Mutasi karyawan"
    _order = "name desc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def get_tanggal(self):
        for x in self:
            my_date = date.today()
            hari = calendar.day_name[my_date.weekday()]
            bulan = calendar.month_name[my_date.weekday()]
            x.hari_tanggal = str(hari)+' ,'+str(my_date)[-2:]+' '+str(bulan)+' '+str(my_date)[:4]

    # def get_contract_existing(self):
    #     for x in self:
    #         obj_contract = self.env['hr.contract']
    #         if x.employee_id and not x.contract_id:
    #             my_contract = obj_contract.search([('employee_id','=',x.employee_id.id)], order="id desc", limit=1)
    #             if my_contract :
    #                 x.contract_id = my_contract.id
    #                 if x.contract_id.type_id :
    #                     x.pay_status_id = x.contract_id.type_id.id

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for x in self:
            x.department_id = x.employee_id.department_id.id
            x.job_id = x.employee_id.job_id.id
            obj_contract = self.env['hr.contract']
            if x.employee_id and not x.contract_id:
                my_contract = obj_contract.search([('employee_id','=',x.employee_id.id)], order="id desc", limit=1)
                if my_contract :
                    x.contract_id = my_contract.id
                    if x.contract_id.type_id :
                        x.pay_status_id = x.contract_id.type_id.id

    name = fields.Char("Number", size=25, default="New")
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user)
    date = fields.Datetime("Created Date",default=lambda self:time.strftime("%Y-%m-%d %H:%M:%S"))
    employee_id = fields.Many2one("hr.employee","Employee", required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    nik = fields.Char("NIK", related="employee_id.nik", store=True)
    department_id = fields.Many2one("hr.department","Department")
    job_id = fields.Many2one("hr.job","Job Title")
    contract_id = fields.Many2one("hr.contract","Contract", readonly=True, states={'draft': [('readonly', False)]})
    pay_status_id = fields.Many2one("hr.contract.type","Pay Status", related="contract_id.type_id")
    new_contract_id = fields.Many2one("hr.contract","New Contract",domain="[('employee_id','=',employee_id)]")
    new_pay_status_id = fields.Many2one("hr.contract.type","New Pay Status", related="new_contract_id.type_id", store=True)
    new_department_id = fields.Many2one("hr.department","New Department", readonly=True, states={'draft': [('readonly', False)]}, track_visibility='onchange')
    new_job_id = fields.Many2one("hr.job","New Job Title",domain="[('department_id','=',new_department_id)]", readonly=True, states={'draft': [('readonly', False)]}, track_visibility='onchange')
    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('done','Done'),('cancel','Cancelled')], default="draft",string="State", track_visibility='onchange')
    notes = fields.Text("Notes")
    hari_tanggal = fields.Char("Tanggal", compute="get_tanggal")
    date_mutation = fields.Date("Date", readonly=True, states={'draft': [('readonly', False)]}, track_visibility='onchange')

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Nomor duplikat !'),
    ]

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise UserError(_('Data tidak bisa di duplikasi !'))
        return super(HRMutasi, self).copy(default=default)

    @api.model
    def create(self, vals):
        if not vals.get('name', False) or vals['name'] == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.mutasi') or 'Number not found !'
        return super(HRMutasi, self).create(vals)

    @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft' :
                raise UserError(_('Data yang bisa dihapus hanya yg berstatus draft'))
        return super(HRMutasi, self).unlink()

    @api.multi
    def button_confirm(self):
        for i in self:
            mutasi = datetime.strptime(i.date_mutation,'%Y-%m-%d')
           # date_now = fields.date.today()
            minus1hari = str(mutasi+timedelta(days=-1))[:10]
            if i.contract_id :
                date_end_lama = i.contract_id.date_end
                i.contract_id.write({'date_end' : minus1hari,'notes' : "Closed by Mutasi : " + i.name})
                new_contract = i.contract_id.copy({'department_id'  : i.new_department_id.id,
                                                    'job_id'        : i.new_job_id.id,
                                                    'date_start'    : i.date_mutation,
                                                    'date_end'      : date_end_lama,
                                                    'notes'         : "Created by Mutasi : " + i.name,
                                                    'state'         :'draft'})
                i.new_contract_id = new_contract.id
                i.write({'state':'confirmed'})
        return True

    @api.multi
    def button_cancel(self):
        for i in self:
            if i.contract_id :
                i.contract_id.write({'date_end':i.new_contract_id.date_end})
                i.new_contract_id.unlink()
                i.write({'state':'cancel'})
        return True

    @api.multi
    def button_set_to_draft(self):
        for i in self:
            i.write({'state':'draft'})
        return True

    @api.multi
    def button_approve(self):
        for i in self:
            i.write({'state':'done'})
            if i.date_mutation <= str(datetime.now()+timedelta(hours=7))[:10] :
                i.employee_id.write({'department_id': i.new_department_id.id, 'job_id':i.new_job_id.id})
        return True

    def action_mutation(self):
        mutation_exist = self.env['hr.mutasi'].search([('date_mutation','=',str(datetime.now()+timedelta(hours=7))[:10]),('state','=','done')])
        for mutation in mutation_exist :
            mutation.employee_id.write({'department_id': mutation.new_department_id.id, 'job_id':mutation.new_job_id.id})
        return True

HRMutasi()