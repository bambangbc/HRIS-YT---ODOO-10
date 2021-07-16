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



class HRKuota(models.Model):
    _name = 'hr.kuota'
    _order = "date desc" 
    _rec_name = "nik"

    @api.depends('employee_id.kuota_history_ids')
    def _compute_total_kuota(self):
        history = self.env['hr.kuota.history']
        for kuota in self:
            if kuota.is_active and kuota.date :
                if kuota.employee_id.contract_ids :
                    contract = kuota.employee_id.contract_ids.sorted('date_start', reverse=True)[0]
                    if contract.type_id.kuota > 0 :
                        if len(str(contract.type_id.tgl_kuota)) == 1 :
                            tgl = '0'+str(contract.type_id.tgl_kuota)
                        else :
                            tgl = str(contract.type_id.tgl_kuota)
                        if len(str(contract.type_id.bln_kuota)) == 1 :
                            bln = '0'+str(contract.type_id.bln_kuota)
                        else :
                            bln = str(contract.type_id.bln_kuota)
                        thn = kuota.date[:4]
                        if int(bln) < 6 :
                            pemakaian_kouta = kuota.employee_id.kuota_history_ids.filtered(lambda x:x.date >= thn+'-'+bln+'-'+tgl and x.date < str(int(thn)+1)+'-'+bln+'-'+tgl)
                        else :
                            pemakaian_kouta = kuota.employee_id.kuota_history_ids.filtered(lambda x:x.date > str(int(thn)-1)+'-'+bln+'-'+tgl and x.date <= thn+'-'+bln+'-'+tgl )
                        total_pemakaian_kouta = len(pemakaian_kouta)
                        kuota.sisa_kuota = total_pemakaian_kouta or 0


    employee_id = fields.Many2one("hr.employee","Employee")
    nik = fields.Char("NIK", related="employee_id.nik", store=True)
    department_id = fields.Many2one("hr.department","Department", related="employee_id.department_id", store=True)  
    job_id = fields.Many2one("hr.job","Job Title", related="employee_id.job_id", store=True)    
    date =fields.Date("Date")
    total_kuota = fields.Integer(string="Total Kuota")
    sisa_kuota = fields.Integer(string="Sisa Kuota")#, compute="_compute_total_kuota", store=True)
    is_active = fields.Boolean("Active", default=True)

HRKuota()


class HRKuotaHistory(models.Model):
    _name = 'hr.kuota.history'
    _order = "date desc" 
    _rec_name = "nik"

    employee_id = fields.Many2one("hr.employee","Employee")
    nik = fields.Char("NIK", related="employee_id.nik", store=True)
    department_id = fields.Many2one("hr.department","Department", related="employee_id.department_id", store=True)  
    job_id = fields.Many2one("hr.job","Job Title", related="employee_id.job_id", store=True)    
    date =fields.Date("Date")
    holiday_id = fields.Many2one("hr.holiday","Document")

    def check_quota_history(self):
        now = str(datetime.now()+timedelta(hours=7))
        seminggulalu = str(datetime.now()+timedelta(days=-7))
        attend = self.env['hr.attendance.finger']
        holi_public = self.env['hr.public_holiday']
        holi = self.env['hr.holidays']
        shift = self.env['hr.rolling.shift.detail']
        employee_ids = self.env['hr.employee'].sudo().search([('active','=',True)])
        for em in employee_ids :
            hari = 7
            for dt in range(7) :
                execu = datetime.now()+timedelta(days=-hari)
                besok_libur = datetime.now()+timedelta(days=-hari-1)
                hari -= 1
                # jika hari minggu skip
                if execu.strftime("%A") == 'Sunday' :
                    continue
                # jika besoknya hari minggu skip
                if besok_libur.strftime("%A") == 'Sunday' :
                    continue
                # cek jika libur nasional
                public_holiday = holi_public.sudo().search([('date','=',str(execu)[:10])])
                if public_holiday :
                    continue
                # cek jika  besok libur nasional
                public_holiday2 = holi_public.sudo().search([('date','=',str(besok_libur)[:10])])
                if public_holiday2 :
                    continue
                # cek jadwal kerja
                shift_exist = shift.sudo().search([('date_start','<=',str(execu)[:10]),
                                                    ('date_end','>=',str(execu)[:10]),
                                                    ('employee_id','=',em.id)],limit=1)
                if shift_exist :
                    # 5 hari kerja sabtu di bypass
                    if len(shift_exist.schedule_id.attendance_ids) == 5 :
                        if execu.strftime("%A") == 'Saturday' :
                            continue
                    else :
                        # cek di master attendance finger ada absen masuk 
                        hadir_exist = attend.sudo().search([('absen_id','=',em.absen_id),
                                                                ('date','>=',str(execu)[:10]+' 00:00:00'),
                                                                ('date','<=',str(execu)[:10]+' 23:59:59')])
                        if not hadir_exist :
                            # cek dulu jika mengajukan cuti dan sudah approve
                            holi_exist = holi.sudo().search([('employee_id','=',em.id),
                                                                ('state','=','validate'),
                                                                ('date_from','>=',str(execu)[:10]+' 00:00:00'),
                                                                ('date_from','<=',str(execu)[:10]+' 23:59:59')], limit=1)
                            if not holi_exist :
                                # cek dulu di master history kuota, supaya ga double
                                data_exist = self.sudo().search([('employee_id','=',em.id),('date','=',str(execu)[:10])])
                                if not data_exist :
                                    contract = em.contract_ids.sorted('date_start', reverse=True)
                                    if contract :
                                        cont_type = contract[0].type_id
                                        if cont_type.kuota > 0 :
                                            if len(str(cont_type.tgl_kuota)) == 1 :
                                                tgl = '0'+str(cont_type.tgl_kuota)
                                            else :
                                                tgl = str(cont_type.tgl_kuota)
                                            if len(str(cont_type.bln_kuota)) == 1 :
                                                bln = '0'+str(cont_type.bln_kuota)
                                            else :
                                                bln = str(cont_type.bln_kuota)
                                            thn = now[:4]
                                            if int(bln) < 6 :
                                                total_kuota = self.sudo().search([('date','>=',thn+'-'+bln+'-'+tgl),#tahun sekarang
                                                                                    ('date','<',str(int(thn)+1)+'-'+bln+'-'+tgl)])#tahun depan
                                            else :
                                                total_kuota = self.sudo().search([('date','>',str(int(thn)-1)+'-'+bln+'-'+tgl),# tahun kemarin
                                                                                    ('date','<=',thn+'-'+bln+'-'+tgl)])#tahun sekarang
                                            if len(total_kuota) < cont_type.kuota :
                                                self.create({'employee_id' : em.id,
                                                                'date' : str(execu)[:10]})
                                                self._cr.commit()
                                                info = 'Kuota '+str(em.name)+' created..'
                                                print info

HRKuotaHistory()

class tbkuota(models.Model):
    _name = "tbkuota"

    name = fields.Date(string="Tidak Bisa Quota")
tbkuota()