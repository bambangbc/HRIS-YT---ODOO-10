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

import xlsxwriter
import base64
from cStringIO import StringIO
import pytz
from pytz import timezone
import PIL
import io


class HRCatering(models.Model):
    _name = "hr.catering"
    _description = "Pengelolaan catering karyawan"
    _order = "name desc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))

    @api.multi
    def action_print(self):
        fp = StringIO()
        # create an new excel file and add a worksheet
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet('Catering')

        #konten di sini
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'white'
        })
        merge_format_teammember = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'FBD4B4'
        })
        merge_format_teamleader = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'CCC0D9'
        })
        merge_format_admin = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'DBE5F1'
        })
        merge_format_karyawan = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'FFFFFF'
        })
        merge_format_staff = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'F2DBDB'
        })
        merge_format_total = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'DAEEF3'
        })

        worksheet.set_column('B:B', 20)

        worksheet.merge_range('A1:A2','No.',merge_format)
        worksheet.merge_range('B1:B2','Division',merge_format)
        worksheet.merge_range('C1:E1','Team Member',merge_format_teammember)
        worksheet.write('C2','jml',merge_format_teammember)
        worksheet.write('D2','abs',merge_format_teammember)
        worksheet.write('E2','jml',merge_format_teammember)
        worksheet.merge_range('F1:H1','Team Leader',merge_format_teamleader)
        worksheet.write('F2','jml',merge_format_teamleader)
        worksheet.write('G2','abs',merge_format_teamleader)
        worksheet.write('H2','jml',merge_format_teamleader)
        worksheet.merge_range('I1:K1','Admin',merge_format_admin)
        worksheet.write('I2','jml',merge_format_admin)
        worksheet.write('J2','abs',merge_format_admin)
        worksheet.write('K2','jml',merge_format_admin)
        worksheet.merge_range('L1:L2','Karyawan',merge_format_karyawan)
        worksheet.merge_range('M1:O1','Staff',merge_format_staff)
        worksheet.write('M2','jml',merge_format_staff)
        worksheet.write('N2','abs',merge_format_staff)
        worksheet.write('O2','jml',merge_format_staff)
        worksheet.merge_range('P1:Q1','TTD',merge_format)
        worksheet.write('P2','Penerima',merge_format)
        worksheet.write('Q2','Pemberi',merge_format)

        department_id = self.env['hr.department'].search([])
        employee_id = self.env['hr.employee']
        emp_catering = self.env['hr.catering.detail']
        row = 1
        no = 0
        for dept in department_id :
            row = row + 1
            no += 1

            # jumlah employee per department
            TM = employee_id.search([('level_id','=','Team Member'),('department_id','=',dept.name)])
            TL = employee_id.search([('level_id','=','Team Leader'),('department_id','=',dept.name)])
            ADM = employee_id.search([('level_id','=','Admin'),('department_id','=',dept.name)])
            STF = employee_id.search([('level_id','=','Staff'),('department_id','=',dept.name)])
            GL = employee_id.search([('level_id','=','Group Leader'),('department_id','=',dept.name)])
            MNG = employee_id.search([('level_id','=','Manager'),('department_id','=',dept.name)])

            # jumlah emloyee yang hadir per department

            TMH = emp_catering.search([('catering_id','=',self.id),('level_id','=','Team Member'),('department_id','=',dept.name)])
            TLH = emp_catering.search([('catering_id','=',self.id),('level_id','=','Team Leader'),('department_id','=',dept.name)])
            ADMH = emp_catering.search([('catering_id','=',self.id),('level_id','=','Admin'),('department_id','=',dept.name)])
            STFH = emp_catering.search([('catering_id','=',self.id),('level_id','=','Staff'),('department_id','=',dept.name)])
            GLH = emp_catering.search([('catering_id','=',self.id),('level_id','=','Group Leader'),('department_id','=',dept.name)])
            MNGH = emp_catering.search([('catering_id','=',self.id),('level_id','=','Manager'),('department_id','=',dept.name)])

            worksheet.write(row,0,no,)
            worksheet.write(row,1,dept.name)
            worksheet.write(row,2,len(TM),merge_format_teammember)
            worksheet.write(row,3,len(TM)-len(TMH),merge_format_teammember)
            worksheet.write(row,4,len(TMH),merge_format_teammember)

            worksheet.write(row,5,len(TL),merge_format_teamleader)
            worksheet.write(row,6,len(TL)-len(TLH),merge_format_teamleader)
            worksheet.write(row,7,len(TLH),merge_format_teamleader)

            worksheet.write(row,8,len(ADM),merge_format_admin)
            worksheet.write(row,9,len(ADM)-len(ADMH),merge_format_admin)
            worksheet.write(row,10,len(ADMH),merge_format_admin)

            worksheet.write(row,11,'=E'+str(row+1)+'+H'+str(row+1)+'+K'+str(row+1),merge_format_karyawan)

            worksheet.write(row,12,len(STF),merge_format_staff)
            worksheet.write(row,13,len(STF)-len(STFH),merge_format_staff)
            worksheet.write(row,14,len(STFH),merge_format_staff)

        worksheet.merge_range('A'+str(row+2)+':'+'B'+str(row+2),'TOTAL')
        worksheet.write(row+1,2,'=sum(C3:C'+str(row+1)+')',merge_format_teammember)
        worksheet.write(row+1,3,'=sum(D3:D'+str(row+1)+')',merge_format_teammember)
        worksheet.write(row+1,4,'=sum(E3:E'+str(row+1)+')',merge_format_teammember)
        worksheet.write(row+1,5,'=sum(F3:F'+str(row+1)+')',merge_format_teamleader)
        worksheet.write(row+1,6,'=sum(G3:G'+str(row+1)+')',merge_format_teamleader)
        worksheet.write(row+1,7,'=sum(H3:H'+str(row+1)+')',merge_format_teamleader)
        worksheet.write(row+1,8,'=sum(I3:I'+str(row+1)+')',merge_format_admin)
        worksheet.write(row+1,9,'=sum(J3:J'+str(row+1)+')',merge_format_admin)
        worksheet.write(row+1,10,'=sum(K3:K'+str(row+1)+')',merge_format_admin)
        worksheet.write(row+1,11,'=sum(L3:L'+str(row+1)+')',merge_format_karyawan)
        worksheet.write(row+1,12,'=sum(M3:M'+str(row+1)+')',merge_format_staff)
        worksheet.write(row+1,13,'=sum(N3:N'+str(row+1)+')',merge_format_staff)
        worksheet.write(row+1,14,'=sum(O3:O'+str(row+1)+')',merge_format_staff)


        worksheet.merge_range('A'+str(row+3)+':'+'B'+str(row+3),'Total Karyawan')
        worksheet.merge_range('C'+str(row+3)+':'+'E'+str(row+3),'=C'+str(row+2)+'+F'+str(row+2)+'+I'+str(row+2),merge_format_total)

        worksheet.merge_range('A'+str(row+4)+':'+'B'+str(row+4),'Total Staff')
        worksheet.merge_range('C'+str(row+4)+':'+'E'+str(row+4),'=M'+str(row+2),merge_format_total)

        worksheet.merge_range('F'+str(row+3)+':'+'H'+str(row+3),'Karyawan Absen')
        worksheet.merge_range('I'+str(row+3)+':'+'K'+str(row+3),'=D'+str(row+2)+'+G'+str(row+2)+'+J'+str(row+2),merge_format_total)

        worksheet.merge_range('F'+str(row+4)+':'+'H'+str(row+4),'Staff Absen')
        worksheet.merge_range('I'+str(row+4)+':'+'K'+str(row+4),'=N'+str(row+2),merge_format_total)

        worksheet.merge_range('L'+str(row+3)+':'+'M'+str(row+4),'Catering',merge_format_teammember)
        worksheet.merge_range('N'+str(row+3)+':'+'O'+str(row+3),'=C'+str(row+3)+'-'+'I'+str(row+3),merge_format_admin)
        worksheet.merge_range('N'+str(row+4)+':'+'O'+str(row+4),'=C'+str(row+4)+'-'+'I'+str(row+4),merge_format_staff)
        workbook.close()
        result = base64.encodestring(fp.getvalue())
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        filename = 'Catering Report %s'%(date_string)
        filename += '%2Exlsx'
        self.write({'file_data':result})
        url = "web/content/?model="+self._name+"&id="+str(self.id)+"&field=file_data&download=true&filename="+filename
        return {
            'name': 'Slip Payslip',
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def create_catering(self):
        #shift_exist = self.env['hr.rolling.shift.detail'].search([('date_start','<=',str(datetime.now())[:10]),('date_end','>=',str(datetime.now())[:10])])
        shift_exist = self.env['hr.rolling.shift.detail'].search([('date_start','<=',self.date_to[:10]),('date_end','>=',self.date_to[:10])])
        #catering = self.create({
        #                'state':'draft',
        #                })
        shf = []
        for shift in shift_exist :
            #import pdb;pdb.set_trace()
            #if shift.employee_id.name == "LAELA SARI" :
                
            #    xx = 0
            #shift.shift_id.attendace_ids
            if str(shift.employee_id.id) not in shf :
                #date_shift = str(datetime.now()+timedelta(hours=7))[:10]+" "+'{0:02.0f}:{1:02.0f}'.format(*divmod(shift.schedule_id.attendance_ids[0].hour_from * 60, 60))+":00"
                date_shift = self.date_to[:10] + " " + '{0:02.0f}:{1:02.0f}'.format(*divmod(shift.schedule_id.attendance_ids[0].hour_from * 60, 60))+":00"
                date_shift_from = str(datetime.strptime(date_shift,"%Y-%m-%d %H:%M:%S")-timedelta(hours=10))
                date_shift_to = str(datetime.strptime(date_shift,"%Y-%m-%d %H:%M:%S")-timedelta(hours=5))
                att = self.env['hr.attendance.finger'].search([('date',">=",date_shift_from),('date',"<=",date_shift_to),('date','>=',str(self.date_from)),('date','<=',str(self.date_to)),('absen_id','=',shift.employee_id.absen_id)],limit=1)#,('date','>=',str(datetime.strptime(date_shift,"%Y-%m-%d %H:%M:%S")-timedelta(hours=12))),('date','<=',str(datetime.strptime(date_shift,"%Y-%m-%d %H:%M:%S")-timedelta(hours=3)))], limit=1)
        
                if att :
                    emp_ids = {
                            'catering_id' : self.id,
                            'employee_id' : shift.employee_id.id
                    }
                    self.env['hr.catering.detail'].create(emp_ids)
                shf.append(str(shift.employee_id.id))
        return True


    def approve_catering(self):
        eksekusi = self.env['hr.catering'].sudo().search([('state','=','draft')])
        for cat in eksekusi :
            # jika data list employee cuma satu atau kosong langsung dihapus
            if len(cat.employee_ids) <= 1 :
                message = "Form Catering  "+ cat.name + " Deleted.. "
                print message
                cat.unlink()
                continue
            cat.write({'state':'approved'})
            message = "Form Catering  "+ cat.name + " Auto Approved.. "
            print message

    @api.model
    def _get_yesterday(self):
        yesterday = datetime.now()- timedelta(days=1)
        return str(yesterday)

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    @api.depends('employee_ids.level_id')
    def _compute_job_level(self):
        #import pdb;pdb.set_trace()
        catering_detail = self.env['hr.catering.detail']
        levels = self.env['hr.job.level'].search([])
        for cat in self:
            summary = ''
            for lev in levels :
                level = catering_detail.search([('catering_id','=',cat.id),('level_id','=',lev.id)])
                if level :
                    new_level = str(lev.name)+ ' : ' + str(len(level))+ ' \n'
                    summary += new_level
            cat.total_level = summary


    name = fields.Char("Number", size=25, default="New", copy=False)
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user)
    date = fields.Datetime("Created Date",default=lambda self:time.strftime("%Y-%m-%d %H:%M:%S"))
    yesterday = fields.Datetime("Catering Date",default=_get_yesterday)
    employee_id = fields.Many2one("hr.employee","Responsibe", required=True, track_visibility='onchange', readonly=True,
        states={'draft': [('readonly', False)]}, default=_default_employee)
    nik = fields.Char("NIK", related="employee_id.nik", store=True)
    department_id = fields.Many2one("hr.department","Department", related="employee_id.department_id", store=True)
    level_id = fields.Many2one("hr.job.level","Job Level", related="employee_id.level_id", store=True)
    state = fields.Selection([('draft','Draft'),('approved','Approved'),('received','Received'),('done','Done')], default="draft",string="State", track_visibility='onchange')
    notes = fields.Text("Notes", track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    employee_ids = fields.One2many("hr.catering.detail", "catering_id", "Employee", readonly=True, states={'draft': [('readonly', False)],'approved': [('readonly',False)]})
    schedule_id= fields.Many2one(comodel_name='resource.calendar', string='Schedule')
    total_level = fields.Text('Summary', compute="_compute_job_level", readonly=True)
    file_data = fields.Binary('File', readonly=True)
    date_from = fields.Datetime("Date From")
    date_to = fields.Datetime("Date To")

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Nomor duplikat !'),
    ]

    #@api.onchange('department_id')
    #def onchange_department_id(self):
    #    if self.department_id:
    #        employee_ids = []
    #        employee_ids = self.env['hr.employee'].sudo().search([('department_id','=',self.department_id.id)])
    #        if employee_ids :
    #            emps = []
    #            for emp in employee_ids :
    #                emps.append((0, 0, {'employee_id' : emp.id}))
    #            self.employee_ids = emps

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise UserError(_('Data tidak bisa di duplikasi !'))
        return super(HRCatering, self).copy(default=default)


    @api.model
    def create(self,vals):
    	if not vals.get('name', False) or vals['name'] == 'New':
	       sequence = self.env['ir.sequence'].next_by_code('hr.catering') or 'Number not found !'
	       vals['name'] = sequence
        return super(HRCatering, self).create(vals)

    @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft' :
                raise UserError(_('Data yang bisa dihapus hanya yg berstatus draft'))
        return super(HRCatering, self).unlink()

    @api.multi
    def button_approve(self):
        for i in self:
            # cek jika harus approve pimpinan dept
            # if not i.department_id.manager_id :
            #     raise UserError(_('Manager untuk department %s belum di set !') % (str(i.department_id.name)))
            # elif i.department_id.manager_id.user_id.id != i._uid :
            #     raise UserError(_('Anda tidak punya akses untuk menyetujui dokumen ini ! (Manager Dept : %s) ') % (str(i.department_id.manager_id.name)))
            if i.employee_id.user_id.id != i._uid :
                raise UserError(_('Anda tidak punya akses untuk menyetujui dokumen ini ! ( Responsible : %s )') % (str(i.employee_id.name)))
            i.write({'state':'approved'})
        return True

    @api.multi
    def button_receive(self):
        for i in self:
            if i.employee_id.user_id.id != i._uid :
                raise UserError(_('Anda tidak punya akses untuk merubah status dokumen ini ! ( Responsible : %s )') % (str(i.employee_id.name)))
            i.write({'state':'received'})
        return True

    @api.multi
    def button_done(self):
        for i in self:
            i.write({'state':'done'})
        return True

HRCatering()


class HRCateringDetail(models.Model):
    _name = "hr.catering.detail"
    _inherit = ['ir.needaction_mixin']
    _rec_name = "nik"

    #check uang makan
    def _uang_makan(self):
        for emp in self :
            #import pdb;pdb.set_trace()
            date = emp.catering_id.date[:10]
            clause_1 = ['&',('date_start','<=', date),'|',('date_end', '=', False),('date_end','>=', date)]
            clause_final =  [('employee_id', '=', emp.employee_id.id)] +clause_1
            contract  = self.env['hr.contract'].sudo().search(clause_final, order="date_end desc", limit=1)
            if contract :
                #import pdb;pdb.set_trace()
                emp.uang_makan = contract.meals
                emp.write({'uang_makan2': contract.meals})


    catering_id = fields.Many2one("hr.catering","Catering", ondelete="cascade")
    schedule_id = fields.Many2one(comodel_name='resource.calendar', string='Schedule', related="catering_id.schedule_id", store=True)
    date = fields.Datetime("Created Date",related="catering_id.date", store=True)
    yesterday = fields.Datetime("Catering Date",related="catering_id.yesterday", store=True)
    employee_id = fields.Many2one("hr.employee","Employee", required=True, track_visibility='onchange')
    level_id = fields.Many2one("hr.job.level","Job Level", related="employee_id.level_id", store=True)
    nik = fields.Char("NIK", related="employee_id.nik", store=True)
    department_id = fields.Many2one("hr.department","Department", related="employee_id.department_id", store=True)
    level_id = fields.Many2one("hr.job.level","Job Level", related="employee_id.level_id", store=True)
    uang_makan = fields.Float("Uang Makan", compute="_uang_makan")
    uang_makan2 = fields.Float("Uang Makan")
    job_id = fields.Many2one("hr.job","Job Title", related="employee_id.job_id", store=True)
    state = fields.Selection([('draft','Draft'),('approved','Approved'),('received','Received'),('done','Done')],
        string="State", track_visibility='onchange', related="catering_id.state", store=True)



HRCateringDetail()