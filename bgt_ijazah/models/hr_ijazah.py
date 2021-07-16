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


class HRIjazah(models.Model):
    _name = "hr.ijazah"
    _description = "Pengelolaan Ijazah"
    _order = "name desc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    @api.depends('name', 'note')
    def name_get(self):
        result = []
        for i in self:
            name = i.name
            if i.no_ijazah :
                name = name +' ('+i.no_ijazah+')'
            result.append((i.id, name))
        return result

    @api.onchange('ijazah_id')
    def onchange_ijazah_id(self):
        for i in self:
            i.employee_id = i.ijazah_id.employee_id.id
            i.no_ijazah = i.ijazah_id.no_ijazah
            i.almamater = i.ijazah_id.almamater
            i.jenjang_id = i.ijazah_id.jenjang_id.id
            i.jurusan = i.ijazah_id.jurusan
            i.tahun_keluar = i.ijazah_id.tahun_keluar
            i.tgl_terima = i.ijazah_id.tgl_terima
            i.status_dokumen = i.ijazah_id.status_dokumen
            i.tgl_dikembalikan = i.ijazah_id.tgl_dikembalikan

    def get_tanggal(self):
        for x in self:
            my_date = date.today()
            hari = calendar.day_name[my_date.weekday()]
            bulan = calendar.month_name[my_date.weekday()]
            x.hari_tanggal = str(hari)+' ,'+str(my_date)[-2:]+' '+str(bulan)+' '+str(my_date)[:4]

    name = fields.Char("Number", size=25, default="New")
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user)
    date = fields.Datetime("Created Date",default=lambda self:time.strftime("%Y-%m-%d %H:%M:%S"))
    employee_id = fields.Many2one("hr.employee","Employee", required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]}) 
    nik = fields.Char("NIK", related="employee_id.nik", store=True)
    department_id = fields.Many2one("hr.department","Department", related="employee_id.department_id", store=True)  
    job_id = fields.Many2one("hr.job","Job Title", related="employee_id.job_id", store=True)    
    no_ijazah = fields.Char("No Seri Ijazah", required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})   
    almamater = fields.Char("Almamater  Sekolah / Universitas", required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]}) 
    jenjang_id = fields.Many2one("hr.recruitment.degree","Jenjang Pendidikan", readonly=True, states={'draft': [('readonly', False)]}, track_visibility='onchange')
    jurusan = fields.Char("Jurusan", readonly=True, states={'draft': [('readonly', False)]}, track_visibility='onchange')
    tahun_keluar = fields.Char("Tahun Kelulusan", readonly=True, states={'draft': [('readonly', False)]}, size=4)
    tgl_terima = fields.Date("Tanggal Diterima", required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    status_dokumen = fields.Selection([('ada','Ada'),('tidak_ada','Tidak Ada')],string="Status Dokumen", track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    tgl_dikembalikan = fields.Date("Tanggal Dikembalikan", track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')], default="draft",string="State", track_visibility='onchange')
    type = fields.Selection([('terima_ijazah','Terima Ijazah'),('ambil_ijazah','Ambil Ijazah')])
    notes = fields.Text("Notes")
    ijazah_id = fields.Many2one("hr.ijazah","No Penerimaan Ijazah", readonly=True, states={'draft': [('readonly', False)]})
    hari_tanggal = fields.Char("Tanggal", compute="get_tanggal")
    ijazah_sudah_diambil = fields.Boolean('Ijazah sudah diambil')

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise UserError(_('Data tidak bisa di duplikasi !'))
        return super(HRIjazah, self).copy(default=default)
        
    @api.model
    def create(self, vals):
        if not vals.get('name', False) or vals['name'] == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.ijazah') or 'Number not found !'
        return super(HRIjazah, self).create(vals)

    @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft' :
                raise UserError(_('Data yang bisa dihapus hanya yg berstatus draft'))
        return super(HRIjazah, self).unlink()

    @api.multi
    def button_confirm(self):
        for i in self:
            datas={'state':'confirmed'}
            if i.type == 'terima_ijazah' :
                datas.update({'ijazah_sudah_diambil':False})
                i.employee_id.write({'jenjang'              : i.jenjang_id.id,
                                    'school_name'           : i.almamater,
                                    'jurusan'               : i.jurusan or False,
                                    'status_ijazah'         : i.status_dokumen,
                                    'no_seri_ijazah'        : i.no_ijazah,
                                    'end_year'              : i.tahun_keluar,
                                    'tanggal_terima_ijazah' : i.tgl_terima})
            elif i.type == 'ambil_ijazah' :
                i.ijazah_id.write({'ijazah_sudah_diambil':True})
                i.employee_id.write({'status_ijazah'         : 'tidak_ada',
                                     'tanggal_terima_ijazah' : False})
                if i.ijazah_id.no_ijazah != i.no_ijazah or i.ijazah_id.employee_id.id != i.employee_id.id or i.ijazah_id.jenjang_id.id != i.jenjang_id.id or i.ijazah_id.status_dokumen != i.status_dokumen:
                    raise UserError(_('Data ijazah yang diambil berbeda dengan data ijazah yang diterima (Nama pegawai, no ijazah, jenjang dan status dokumen)!'))
            i.write(datas)
        return True

    @api.multi
    def button_cancel(self):
        for i in self:
            i.write({'state':'cancel'})
            if i.type == 'terima_ijazah' :
                i.employee_id.write({'jenjang'              : False,
                                    'school_name'           : False,
                                    'jurusan'               : False,
                                    'status_ijazah'         : False,
                                    'no_seri_ijazah'        : False,
                                    'end_year'              : False,
                                    'tanggal_terima_ijazah' : False})
            elif i.type == 'ambil_ijazah' :
                i.ijazah_id.write({'ijazah_sudah_diambil':False})
        return True

    @api.multi
    def button_set_to_draft(self):
        for i in self:
            i.write({'state':'draft'})
        return True
        
HRIjazah()