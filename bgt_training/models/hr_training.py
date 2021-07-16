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


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    training_ids = fields.One2many('hr.training.employee', 'employee_id', 'Training', readonly=True)


HREmployee()

class HRTraining(models.Model):
    _name = "hr.training"
    _description = "Pengelolaan Training Karyawan"
    _order = "name desc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def get_tanggal(self):
        for x in self:
            my_date = date.today()
            hari = calendar.day_name[my_date.weekday()]
            bulan = calendar.month_name[my_date.weekday()]
            x.hari_tanggal = str(my_date)[-2:]+' '+str(bulan)+' '+str(my_date)[:4]

    name = fields.Char("Number", size=25, default="New", copy=False)
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user)
    date = fields.Datetime("Created Date",default=lambda self:time.strftime("%Y-%m-%d %H:%M:%S"))
    notes = fields.Text("Notes")
    hari_tanggal = fields.Char("Dinamic date", compute="get_tanggal")
    tgl_berlaku = fields.Date("Tanggal Berlaku", track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    tgl_revisi = fields.Date("Tanggal Revisi", track_visibility='onchange', readonly=False, states={'done': [('readonly', True)]})
    register = fields.Char("No. Registrasi", track_visibility='onchange', readonly=False, states={'done': [('readonly', True)]})
    topik = fields.Char('Topik Pelatihan', size=128, required=True, readonly=True, states={'draft': [('readonly', False)]})
    alasan = fields.Char('Alasan Pemilihan Topik', size=128, required=True, readonly=True, states={'draft': [('readonly', False)]})
    tgl_training = fields.Date('Mulai Training', required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    tgl_akhir_training = fields.Date('Sampai', required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection([('eksternal','Eksternal'),('internal','Internal')],string="Type Pelatihan", required=True, default="eksternal", readonly=True, states={'draft': [('readonly', False)]})
    instruktur = fields.Char('Instruktur', size=128, readonly=True, states={'draft': [('readonly', False)]})
    instansi = fields.Char('Instansi', size=128, readonly=True, states={'draft': [('readonly', False)]})
    department_id = fields.Many2one('hr.department', 'Department', readonly=True, states={'draft': [('readonly', False)]})
    keterangan= fields.Char('Keterangan', size=128, readonly=True, states={'draft': [('readonly', False)]})
    tempat_pelatihan = fields.Char('Tempat Pelatihan', size=128, readonly=True, states={'draft': [('readonly', False)]})
    employee_ids = fields.One2many('hr.training.employee', 'training_id',  string='Employee', readonly=False, states={'done': [('readonly', True)]})
    alasan_menolak = fields.Char('Alasan Menolak', size=128)
    menolak = fields.Selection([
            ('manager', 'Manager'),
            ('hrd', 'HRD & Admin'),
            ('pimpinan', 'Pimpinan Perusahaan'),
            ], 'Pihak Tidak Setuju', track_visibility='onchange')
    jenis_training = fields.Selection([('tahun', 'Pelatihan Tahunan'),
                                            ('khusus', 'Pelatihan Khusus'),
                                            ('promosi', 'Promosi/Mutasi'),
                                            ('umum', 'Umum'),
                                            ], 'Jenis Pelatihan', required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})

    state = fields.Selection([
            ('draft', 'Draft'),
            ('verify', 'Verify'),
            ('approve', 'Approve'),
            ('reject', 'Reject'),
            ('second_approve', 'Second Approve'),
            ('evaluation', 'Evaluation'),
            ('done', 'Done'),
            ], 'Status', readonly=True, default="draft", track_visibility='onchange')


    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Nomor duplikat !'),
    ]


    @api.onchange('department_id')
    def onchange_department_id(self):
        for i in self:
            if i.type == 'internal' :
                emp_obj = self.env['hr.employee']
                employees = emp_obj.search([('department_id','=',i.department_id.id)])
                if employees:
                    emps = []
                    for e in employees :
                        emps.append((0,0,{'employee_id': e}))
                    i.employee_ids = emps

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise UserError(_('Data tidak bisa di duplikasi !'))
        return super(HRTraining, self).copy(default=default)

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
	        sequence = self.env['ir.sequence'].next_by_code('hr.training') or 'Number not found !'
	        if sequence != 'Number not found !' :
	            awal = sequence[:12]
	            akhir = sequence[-4:]
	            romawi = self.write_roman(int(bulan))
	            vals['name'] = str(awal)+str(romawi)+'/'+str(akhir)
        return super(HRTraining, self).create(vals)

    @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft' :
                raise UserError(_('Data yang bisa dihapus hanya yg berstatus draft'))
        return super(HRTraining, self).unlink()


    @api.multi
    def verify(self):
        for i in self:
            i.write({'state':'verify'})
            for x in i.employee_ids :
                x.write({'state':'verify'})
        return True

    @api.multi
    def cancel(self):
        for i in self:
            i.write({'state':'draft'})
            for x in i.employee_ids :
                x.write({'state':'draft'})
        return True

    @api.multi
    def reject(self):
        for i in self:
            i.write({'state':'reject'})
            for x in i.employee_ids :
                x.write({'state':'reject'})
        return True

    @api.multi
    def approve(self):
        for i in self:
            i.write({'state':'approve'})
            for x in i.employee_ids :
                x.write({'state':'approve'})
        return True

    @api.multi
    def evaluation(self):
        for i in self:
            i.write({'state':'evaluation'})
            for x in i.employee_ids :
                x.write({'state':'evaluation'})
        return True


    @api.multi
    def done(self):
        for i in self:
            for x in i.employee_ids :
                if x.point <= 0.0 :
                    raise UserError(_('Point employee %s masih nol !') % (x.employee_id.name))
                x.write({'state':'done'})
            i.write({'state':'done'})

        return True

HRTraining()


class HRTrainingEmployee(models.Model):
    _name = 'hr.training.employee'

    training_id = fields.Many2one('hr.training', 'Training')
    employee_id = fields.Many2one("hr.employee","Employee", required=True, readonly=True, states={'draft': [('readonly', False)]})
    identification_id = fields.Char("No KTP", related="employee_id.identification_id", store=True)
    nik = fields.Char("NIK", related="employee_id.nik", store=True)
    parent_id = fields.Many2one("hr.employee","Atasan", related="employee_id.parent_id", store=True)
    department_id = fields.Many2one("hr.department","Department", related="employee_id.department_id", store=True)
    job_id = fields.Many2one("hr.job","Job Title", related="employee_id.job_id", store=True)
    point = fields.Float("Point", readonly=True, states={'evaluation': [('readonly', False)]})
    keterangan =  fields.Char('Keterangan', size=24 ,readonly=True, states={'evaluation': [('readonly', False)]})
    state = fields.Selection([
            ('draft', 'Draft'),
            ('verify', 'Verify'),
            ('approve', 'Approve'),
            ('reject', 'Reject'),
            ('second_approve', 'Second Approve'),
            ('evaluation', 'Evaluation'),
            ('done', 'Done'),
            ], 'Status', related="training_id.state", store=True)

HRTrainingEmployee()