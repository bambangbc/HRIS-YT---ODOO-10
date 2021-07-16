# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 widianajuniar@gmail.com
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
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import xlsxwriter, base64, pytz, string, re
from cStringIO import StringIO
from datetime import datetime, timedelta
from pytz import timezone
from string import ascii_uppercase
import itertools
import xlwt

class PayrollReportWizard(models.TransientModel):
    _name = "payroll.report.wizard"
    _description = "Payroll Report"

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))

    @api.onchange('calendar_id')
    def onchange_calendar_id(self):
        if self.calendar_id.date :
            self.end_date = self.calendar_id.date
            self.start_date = self.calendar_id.date

    state_x = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    data_x = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date', default=fields.Datetime.now())
    category = fields.Selection([('Staff', 'Staff'), ('Harian', 'Harian'), ('Training', 'Training'), ('Borongan', 'Borongan'), ('Bulanan', 'Bulanan')], default='Staff', required=True)
    calendar_id = fields.Many2one('hr.calendarpayroll','Calendar')

    def add_workbook_format(self, workbook):
        colors = {
            'white_orange': '#FFFFDB',
            'orange': '#FFC300',
            'red': '#FF0000',
            'yellow': '#F6FA03',
            'blue': '#0000FF',
            'green': '#00FF00',
            'violet': '#8A2BE2',
        }

        wbf = {}
        wbf['header90'] = workbook.add_format({'bold': 1, 'font_color': '#000000'})
        wbf['header90'].set_border()
        wbf['header90'].set_rotation(90)
        wbf['header90'].set_align('vcenter')
        wbf['header90'].set_align('center')

        wbf['header90m'] = workbook.add_format({'bold': 1, 'font_color': '#000000'})
        wbf['header90m'].set_border()
        wbf['header90m'].set_rotation(90)
        wbf['header90m'].set_align('vcenter')
        wbf['header90m'].set_align('center')
        wbf['header90m'].set_bg_color('yellow')

        wbf['header'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'font_color': '#000000'})
        wbf['header'].set_border()
        wbf['header'].set_align('vcenter')
        wbf['header'].set_align('center')

        wbf['header_orange'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['orange'], 'font_color': '#000000'})
        wbf['header_orange'].set_border()
        wbf['header_orange'].set_align('vcenter')
        wbf['header_orange'].set_align('center')

        wbf['header_yellow'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['yellow'], 'font_color': '#000000'})
        wbf['header_yellow'].set_border()
        wbf['header_yellow'].set_align('vcenter')
        wbf['header_yellow'].set_align('center')

        wbf['header_blue'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['blue'], 'font_color': '#000000'})
        wbf['header_blue'].set_border()
        wbf['header_blue'].set_align('vcenter')
        wbf['header_blue'].set_align('center')

        wbf['header_green'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['green'], 'font_color': '#000000'})
        wbf['header_green'].set_border()
        wbf['header_green'].set_align('vcenter')
        wbf['header_green'].set_align('center')

        wbf['header_red'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['red'], 'font_color': '#000000'})
        wbf['header_red'].set_border()
        wbf['header_red'].set_align('vcenter')
        wbf['header_red'].set_align('center')

        wbf['header_violet'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['violet'], 'font_color': '#000000'})
        wbf['header_violet'].set_border()
        wbf['header_violet'].set_align('vcenter')
        wbf['header_violet'].set_align('center')

        wbf['header_no'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000'})
        wbf['header_no'].set_border()
        wbf['header_no'].set_align('vcenter')

        wbf['footer'] = workbook.add_format({'align': 'left'})

        wbf['content_date'] = workbook.add_format({'num_format': 'dd-mm-yyyy'})
        wbf['content_date'].set_left()
        wbf['content_date'].set_right()
        wbf['content_date'].set_border()

        wbf['content'] = workbook.add_format()
        wbf['content'].set_left()
        wbf['content'].set_right()
        wbf['content'].set_border()

        wbf['content_number'] = workbook.add_format({'align': 'right', 'num_format': '#,##0'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()
        wbf['content_number'].set_border()

        return wbf, workbook

    def convert_name_day(self, day):
        if day == 'Sunday':
            hari = 'Minggu'
        elif day == 'Monday':
            hari = 'Senin'
        elif day == 'Tuesday':
            hari = 'Selasa'
        elif day == 'Wednesday':
            hari = 'Rabu'
        elif day == 'Thursday':
            hari = 'Kamis'
        elif day == 'Friday':
            hari = 'Jumat'
        else:
            hari = 'Sabtu'
        return hari

    def print_excel_report(self):
        start_date = self.start_date
        end_date = self.end_date
        category = self.category
        contract = self.env['hr.contract']
        contract_type = self.env['hr.contract.type']
        contract_exist =False
        if category == 'Staff' :
            contract_exist = contract_type.sudo().search([('name','ilike','STAFF')],limit=1)
        elif category == 'Harian' :
            contract_exist = contract_type.sudo().search([('name','ilike','HARIAN')],limit=1)
        elif category == 'Training' :
            contract_exist = contract_type.sudo().search([('name','ilike','TRAINING')],limit=1)
        elif category == 'Borongan' :
            contract_exist = contract_type.sudo().search([('name','ilike','BORONGAN')],limit=1)
        elif category == 'Bulanan' :
            contract_exist = contract_type.sudo().search([('name','ilike','BULANAN')],limit=1)
        hasil = False
        if contract_exist :
            result = contract.sudo().search([('type_id','=',contract_exist.id),('state','!=','close')])
            if not result:
                raise UserError(_('Data not found !'))
            #result = contracts.mapped('employee_id')
            if category == 'Staff' :
                hasil = self.print_excel_report_staff(start_date,end_date,category,result)
            elif category == 'Harian' :
                hasil = self.print_excel_report_harian(start_date,end_date,category,result,self.calendar_id)
            elif category == 'Training' :
                hasil = self.print_excel_report_training(start_date,end_date,category,result)
            elif category == 'Borongan' :
                hasil = self.print_excel_report_borongan(start_date,end_date,category,result)
        return hasil

    # report staff
    def print_excel_report_staff(self,start_date,end_date,category,result):
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = start_date + ' to ' + end_date
        filename = 'Payroll Report %s (%s).xlsx' % ( category,date_string)
        
        
        worksheet = workbook.add_worksheet('Payroll Report')
        worksheet.set_column('A1:A1', 5)
        worksheet.set_column('B1:B1', 20)
        worksheet.set_column('C1:C1', 50)
        worksheet.set_column('D1:D1', 20)
        worksheet.set_column('E1:E1', 20)
        worksheet.set_column('F1:F1', 20)
        worksheet.set_column('G1:G1', 20)
        worksheet.set_column('H1:H1', 20)

        row = 1
        dtstart = datetime.strptime(start_date,'%Y-%m-%d')
        dtend = datetime.strptime(end_date,'%Y-%m-%d')
        day_length = dtend-dtstart       
        hari = self.convert_name_day(dtstart.strftime("%A"))
        col_count = 0
        # header pertama
        for size in itertools.count(1):
            stop = False
            for sup in itertools.product(ascii_uppercase, repeat=size):             
                if len(sup) == 1 :
                    col = str(sup[0])
                    if col not in ('A','B','C','D','E','F','G','H') :
                        #yield "".join(s)
                        worksheet.set_column('%s1:%s1' % (col,col), 2)
                        if hari == 'Minggu' :
                            worksheet.write('%s%s' % (col,row), hari, wbf['header90m'])
                        else :
                            worksheet.write('%s%s' % (col,row), hari, wbf['header90'])
                        col_count += 1
                        dtstart = dtstart+timedelta(days=1)
                        hari = self.convert_name_day(dtstart.strftime("%A"))
                        if col_count > day_length.days :
                            stop = True
                            break
                else :
                    col = str(sup[0]+sup[1])
                    worksheet.set_column('%s1:%s1' % (col,col), 2)
                    if hari == 'Minggu' :
                        worksheet.write('%s%s' % (col,row), hari, wbf['header90m'])
                    else :
                        worksheet.write('%s%s' % (col,row), hari, wbf['header90'])
                    col_count += 1
                    dtstart = dtstart+timedelta(days=1)
                    hari = self.convert_name_day(dtstart.strftime("%A"))
                    if col_count > day_length.days :
                        stop = True
                        break
            if stop :
                break

        row +=1
        dtstart2 = datetime.strptime(start_date,'%Y-%m-%d')
        dtend2 = datetime.strptime(end_date,'%Y-%m-%d')
        day_length2 = dtend2-dtstart2
        hari2 = self.convert_name_day(dtstart2.strftime("%A"))
        col_count2 = 0
        # header kedua
        for size2 in itertools.count(1):
            hadir = False
            sakit = False
            absen = False
            kuota = False
            izin = False
            hadir25 = False
            masukminggu = False
            total_absen = False
            lainlain = False
            sisa_kuota1 = False
            sisa_kuota2 = False
            sisa_cuti1 = False
            sisa_cuti2 = False
            lembur = False
            um_lembur = False
            bpjs_kes = False
            bpjs_ker = False
            total_potongan = False
            stop = False
            for sup2 in itertools.product(ascii_uppercase, repeat=size2):    
                if not stop :         
                    if len(sup2) == 1 :
                        col = str(sup2[0])
                        if col == 'A':
                            worksheet.write('%s%s' % (col,row), 'No', wbf['header'])
                        elif col == 'B':
                            worksheet.write('%s%s' % (col,row), 'NIK', wbf['header'])
                        elif col == 'C':
                            worksheet.write('%s%s' % (col,row), 'Nama', wbf['header'])
                        elif col == 'D':
                            worksheet.write('%s%s' % (col,row), 'Department', wbf['header'])
                        elif col == 'E':
                            worksheet.write('%s%s' % (col,row), 'STT', wbf['header'])
                        elif col == 'F':
                            worksheet.write('%s%s' % (col,row), 'Tgl Masuk', wbf['header'])
                        elif col == 'G':
                            worksheet.write('%s%s' % (col,row), 'TT Ref', wbf['header'])
                        elif col == 'H':
                            worksheet.write('%s%s' % (col,row), 'Uang Makan', wbf['header'])
                        else :
                            worksheet.set_column('%s1:%s1' % (col,col), 2)
                            if hari2 == 'Minggu' :
                                worksheet.write('%s%s' % (col,row), dtstart2.strftime("%d %b %Y"), wbf['header90m'])
                            else :
                                worksheet.write('%s%s' % (col,row), dtstart2.strftime("%d %b %Y"), wbf['header90'])
                            col_count2 += 1
                            dtstart2 = dtstart2+timedelta(days=1)
                            hari2 = self.convert_name_day(dtstart2.strftime("%A"))
                            if col_count2 > day_length2.days :
                                stop = True
                                
                    else :
                        col = str(sup2[0]+sup2[1])
                        worksheet.set_column('%s1:%s1' % (col,col), 2)
                        if hari2 == 'Minggu' :
                            worksheet.write('%s%s' % (col,row), dtstart2.strftime("%d %b %Y"), wbf['header90m'])
                        else :
                            worksheet.write('%s%s' % (col,row), dtstart2.strftime("%d %b %Y"), wbf['header90'])
                        col_count2 += 1
                        dtstart2 = dtstart2+timedelta(days=1)
                        hari2 = self.convert_name_day(dtstart2.strftime("%A"))
                        if col_count2 > day_length2.days :
                            stop = True
                        
                else :
                    tanggal = datetime.strptime(end_date,'%Y-%m-%d')
                    bulan = tanggal.strftime("%B")
                    tanggal_bulan_kemarin = tanggal - timedelta(days=30) 
                    bulan_kemarin = tanggal_bulan_kemarin.strftime("%B")
                    if len(sup2) == 1 :
                        col = str(sup2[0])
                    else :
                        col = str(sup2[0]+sup2[1])

                    if not hadir :
                        worksheet.write('%s%s' % (col,row), 'Hadir' , wbf['header'])
                        hadir = True
                        continue
                    elif not absen :
                        worksheet.write('%s%s' % (col,row), 'Absen' , wbf['header'])
                        absen = True
                        continue
                    elif not kuota :
                        worksheet.write('%s%s' % (col,row), 'Kuota' , wbf['header'])
                        kuota = True
                        continue
                    elif not sakit :
                        worksheet.write('%s%s' % (col,row), 'Sakit' , wbf['header'])
                        sakit = True
                        continue
                    elif not izin :
                        worksheet.write('%s%s' % (col,row), 'Izin' , wbf['header'])
                        izin = True
                        continue
                    elif not hadir25 :
                        worksheet.set_column('%s2:%s2' % (col,col), 15 )
                        worksheet.write('%s%s' % (col,row), 'Hadir 25 Hari' , wbf['header'])
                        hadir25 = True
                        continue
                    elif not masukminggu :
                        worksheet.set_column('%s2:%s2' % (col,col), 15 )
                        worksheet.write('%s%s' % (col,row), 'Masuk Minggu' , wbf['header'])
                        masukminggu = True
                        continue
                    elif not lainlain :
                        worksheet.set_column('%s2:%s2' % (col,col), 15 )
                        worksheet.write('%s%s' % (col,row), 'Lain-lain' , wbf['header'])
                        lainlain = True
                        continue
                    elif not sisa_kuota1 :
                        worksheet.set_column('%s2:%s2' % (col,col), 15 )
                        worksheet.write('%s%s' % (col,row), 'Sisa Kuota '+bulan_kemarin , wbf['header'])
                        sisa_kuota1 = True
                        continue
                    elif not sisa_kuota2 :
                        worksheet.set_column('%s2:%s2' % (col,col), 15 )
                        worksheet.write('%s%s' % (col,row), 'Sisa Kuota '+bulan , wbf['header'])
                        sisa_kuota2 = True
                        continue
                    elif not sisa_cuti1 :
                        worksheet.set_column('%s2:%s2' % (col,col), 15 )
                        worksheet.write('%s%s' % (col,row), 'Sisa Cuti '+bulan_kemarin , wbf['header'])
                        sisa_cuti1 = True
                        continue
                    elif not sisa_cuti2 :
                        worksheet.set_column('%s2:%s2' % (col,col), 15 )
                        worksheet.write('%s%s' % (col,row), 'Sisa Cuti ' +bulan, wbf['header'])
                        sisa_cuti2 = True
                        continue
                    elif not lembur :
                        worksheet.write('%s%s' % (col,row), 'Lembur' , wbf['header'])
                        lembur = True
                        continue
                    elif not um_lembur :
                        worksheet.set_column('%s2:%s2' % (col,col), 10 )
                        worksheet.write('%s%s' % (col,row), 'UM Lembur' , wbf['header'])
                        um_lembur = True
                        continue
                    elif not bpjs_kes :
                        worksheet.set_column('%s2:%s2' % (col,col), 15 )
                        worksheet.write('%s%s' % (col,row), 'BPJS Kesehatan' , wbf['header'])
                        bpjs_kes = True
                        continue
                    elif not bpjs_ker :
                        worksheet.set_column('%s2:%s2' % (col,col), 20 )
                        worksheet.write('%s%s' % (col,row), 'BPJS Ketenagakerjaan' , wbf['header'])
                        bpjs_ker = True
                        continue
                    elif not total_potongan :
                        worksheet.write('%s%s' % (col,row), 'Total Total' , wbf['header'])
                        total_potongan = True
                        continue

                    # elif not total_absen :
                    #     worksheet.set_column('%s1:%s1' % (col,col), 20)
                    #     worksheet.write('%s%s' % (col,row), 'Total Tidak hadir' , wbf['header_red'])
                    #     total_absen = True
                    #     continue
                    else :
                        break
            if stop :
                break

        # value report
        attend = self.env['hr.attendance.finger']
        over = self.env['hr.overtime.employee']
        kuot = self.env['hr.kuota.history']
        holi = self.env['hr.holidays']
        no = 1
        for co in result :
            em = co.employee_id
            row +=1
            dtstart3 = datetime.strptime(start_date,'%Y-%m-%d')
            dtend3 = datetime.strptime(end_date,'%Y-%m-%d')
            day_length3 = dtend3-dtstart3
            hari3 = self.convert_name_day(dtstart3.strftime("%A"))
            col_count3 = 0
            t_hadir = 0
            t_kuota = 0
            t_sakit = 0
            t_izin = 0
            t_absen = 0
            t_hadir_minggu = 0
            for size3 in itertools.count(1):
                hadir = False
                sakit = False
                absen = False
                kuota = False
                izin = False
                hadir25 = False
                hadir_minggu = False
                lainlain = False
                kuota1 = False
                kuota2 = False
                cuti1 = False
                cuti2 = False
                lembur = False
                um_lembur = False
                bpjs_kes = False
                bpjs_ker = False
                total_potongan = False
                stop = False
                for sup3 in itertools.product(ascii_uppercase, repeat=size3):    
                    if len(sup3) == 1 :
                        col = str(sup3[0])
                    else :
                        col = str(sup3[0]+sup3[1])
                    if not stop :
                        if col == 'A':
                            worksheet.write('%s%s' % (col,row), no, wbf['content_number'])
                            no += 1
                        elif col == 'B':
                            worksheet.write('%s%s' % (col,row), em.nik, wbf['content'])
                        elif col == 'C':
                            worksheet.write('%s%s' % (col,row), em.name, wbf['content'])
                        elif col == 'D':
                            worksheet.write('%s%s' % (col,row), em.department_id.name or '', wbf['content'])
                        elif col == 'E':
                            worksheet.write('%s%s' % (col,row), em.level_id.name or '', wbf['content'])
                        elif col == 'F':
                            worksheet.write('%s%s' % (col,row), em.work_date or '', wbf['content_date'])
                        elif col == 'G':
                            worksheet.write('%s%s' % (col,row), em.bank_account_id.acc_number or '', wbf['content'])
                        elif col == 'H':
                            worksheet.write('%s%s' % (col,row), co.meals or '', wbf['content_number'])
                        else :
                            
                            worksheet.set_column('%s1:%s1' % (col,col), 2)
                            hadir_exist = attend.sudo().search([('absen_id','=',em.absen_id),
                                                                ('date','>=',str(dtstart3+timedelta(hours=-7))),
                                                                ('date','<=',str(dtstart3)[:10]+' 16:59:59')])
                            if hadir_exist :
                                is_minggu = self.convert_name_day(dtstart3.strftime("%A"))
                                if is_minggu == 'Minggu' :
                                    t_hadir_minggu += 1
                                worksheet.write('%s%s' % (col,row), 'H', wbf['content'])
                                t_hadir += 1
                                col_count3 += 1
                                dtstart3 = dtstart3+timedelta(days=1)
                                hari3 = self.convert_name_day(dtstart3.strftime("%A"))
                                if col_count3 > day_length3.days :
                                    stop = True
                            else :
                                kuota_exist = kuot.sudo().search([('employee_id','=',em.id),
                                                                    ('date','=',str(dtstart3)[:10])])
                                if kuota_exist :
                                    worksheet.write('%s%s' % (col,row), 'K', wbf['content'])
                                    t_kuota += 1
                                    col_count3 += 1
                                    dtstart3 = dtstart3+timedelta(days=1)
                                    hari3 = self.convert_name_day(dtstart3.strftime("%A"))
                                    if col_count3 > day_length3.days :
                                        stop = True
                                else :
                                    holi_exist = holi.sudo().search([('employee_id','=',em.id),
                                                                    ('date_from','>=',str(dtstart3+timedelta(hours=-7))),
                                                                    ('date_from','<=',str(dtstart3)[:10]+' 16:59:59')], limit=1)
                                    if holi_exist :
                                        if holi_exist.holiday_status_id.is_legal_leaves :
                                            worksheet.write('%s%s' % (col,row), 'I', wbf['content'])
                                            t_izin += 1
                                        else :
                                            if 'sick' in [holi_exist.holiday_status_id.name.lower()]:
                                                worksheet.write('%s%s' % (col,row), 'S', wbf['content'])
                                                t_sakit += 1
                                            elif 'sakit' in [holi_exist.holiday_status_id.name.lower()]:
                                                worksheet.write('%s%s' % (col,row), 'S', wbf['content'])
                                                t_sakit += 1
                                            elif 'dinas' in [holi_exist.holiday_status_id.name.lower()]:
                                                worksheet.write('%s%s' % (col,row), 'D', wbf['content'])
                                                t_sakit += 1
                                            else :
                                                if hari3 != 'Minggu' :
                                                    worksheet.write('%s%s' % (col,row), 'A', wbf['content'])
                                                    t_absen += 1
                                    else :
                                        if hari3 != 'Minggu' :
                                            worksheet.write('%s%s' % (col,row), 'A', wbf['content'])
                                            t_absen += 1
                                    col_count3 += 1
                                    dtstart3 = dtstart3+timedelta(days=1)
                                    hari3 = self.convert_name_day(dtstart3.strftime("%A"))
                                    if col_count3 > day_length3.days :
                                        stop = True
                    else :
                        if not hadir :
                            worksheet.write('%s%s' % (col,row), t_hadir , wbf['content_number'])
                            hadir = True
                            continue
                        elif not absen :
                            worksheet.write('%s%s' % (col,row), t_absen , wbf['content_number'])
                            absen = True
                            continue
                        elif not kuota :
                            worksheet.write('%s%s' % (col,row), t_kuota , wbf['content_number'])
                            kuota = True
                            continue
                        elif not sakit :
                            worksheet.write('%s%s' % (col,row), t_sakit , wbf['content_number'])
                            sakit = True
                            continue
                        elif not izin :
                            worksheet.write('%s%s' % (col,row), t_izin , wbf['content_number'])
                            izin = True
                            continue
                        elif not hadir25 :
                            worksheet.write('%s%s' % (col,row), 25-t_izin-t_kuota-t_absen , wbf['content_number'])
                            hadir25 = True
                            continue
                        elif not hadir_minggu :
                            worksheet.write('%s%s' % (col,row), t_hadir_minggu , wbf['content_number'])
                            hadir_minggu = True
                            continue
                        elif not lainlain :
                            worksheet.write('%s%s' % (col,row), '' , wbf['content_number'])
                            lainlain = True
                            continue
                        elif not kuota1 :
                            mykuot = 0
                            mykuota = em.kuota_ids.filtered(lambda x:x.is_active)
                            if mykuota :
                                mykuot = mykuota[0].sisa_kuota
                            worksheet.write('%s%s' % (col,row), mykuot+t_kuota , wbf['content_number'])
                            kuota1 = True
                            continue
                        elif not kuota2 :
                            mykuot = 0
                            mykuota = em.kuota_ids.filtered(lambda x:x.is_active)
                            if mykuota :
                                mykuot = mykuota[0].sisa_kuota
                            worksheet.write('%s%s' % (col,row), mykuot , wbf['content_number'])
                            kuota2 = True
                            continue
                        elif not kuota2 :
                            mykuot = 0
                            mykuota = em.kuota_ids.filtered(lambda x:x.is_active)
                            if mykuota :
                                mykuot = mykuota[0].sisa_kuota
                            worksheet.write('%s%s' % (col,row), mykuot , wbf['content_number'])
                            kuota2 = True
                            continue
                        elif not cuti1 :
                            worksheet.write('%s%s' % (col,row), em.remaining_leaves-t_izin , wbf['content_number'])
                            cuti1 = True
                            continue
                        elif not cuti2 :
                            worksheet.write('%s%s' % (col,row), em.remaining_leaves , wbf['content_number'])
                            cuti2 = True
                            continue
                        elif not lembur :
                            t_overtime = 0
                            ovt_exist = over.sudo().search([('employee_id','=',em.id),('state','=','validate'),
                                ('date','>=',start_date),('date','<=',end_date)])
                            if ovt_exist :
                                t_overtime = sum(ovt_exist.mapped('total_jam'))
                            worksheet.write('%s%s' % (col,row), t_overtime , wbf['content_number'])
                            lembur = True
                            continue
                        elif not um_lembur :
                            worksheet.write('%s%s' % (col,row), t_overtime*20000 , wbf['content_number'])
                            um_lembur = True
                            continue
                        elif not bpjs_kes :
                            worksheet.write('%s%s' % (col,row), '' , wbf['content_number'])
                            bpjs_kes = True
                            continue
                        elif not bpjs_ker :
                            worksheet.write('%s%s' % (col,row), '' , wbf['content_number'])
                            bpjs_ker = True
                            continue
                        elif not total_potongan :
                            worksheet.write('%s%s' % (col,row), '' , wbf['content_number'])
                            total_potongan = True
                            continue
                        else :
                            break
                if stop :
                    break

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'state_x': 'get', 'data_x': out, 'name': filename})
        fp.close()

        ir_model_data = self.env['ir.model.data']
        form_res = ir_model_data.get_object_reference('bgt_payroll_report', 'payroll_report_form_view')

        form_id = form_res and form_res[1] or False
        return {
            'name': 'Download .xlsx',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payroll.report.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    # report harian
    def print_excel_report_harian(self,start_date,end_date,category,result,calendar_id):
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = end_date
        filename = 'Payroll Report %s (%s).xlsx' % ( category,date_string)
        
        worksheet = workbook.add_worksheet('Payroll Report')
        worksheet.set_column('A1:A1', 5)
        worksheet.set_column('B1:B1', 20)
        worksheet.set_column('C1:C1', 50)
        worksheet.set_column('D1:D1', 20)
        worksheet.set_column('E1:E1', 20)
        worksheet.set_column('F1:F1', 20)
        worksheet.set_column('G1:G1', 20)
        worksheet.set_column('H1:H1', 20)
        worksheet.set_column('I1:I1', 20)
        worksheet.set_column('J1:J1', 20)
        worksheet.set_column('K1:K1', 20)
        worksheet.set_column('L1:L1', 20)
        worksheet.set_column('M1:M1', 20)
        worksheet.set_column('N1:N1', 20)
        worksheet.set_column('O1:O1', 20)
        worksheet.set_column('P1:P1', 20)
        worksheet.set_column('Q1:Q1', 20)
        worksheet.set_column('R1:R1', 20)
        worksheet.set_column('S1:S1', 20)
        worksheet.set_column('T1:T1', 20)
        worksheet.set_column('U1:U1', 20)
        worksheet.set_column('V1:V1', 20)
        worksheet.set_column('W1:W1', 20)
        worksheet.set_column('X1:X1', 20)
        worksheet.set_column('Y1:Y1', 20)
        worksheet.set_column('Z1:Z1', 20)
        worksheet.set_column('AA1:AA1', 20)
        worksheet.set_column('AB1:AB1', 20)
        worksheet.set_column('AC1:AC1', 20)
        worksheet.set_column('AD1:AD1', 20)
        worksheet.set_column('AE1:AE1', 20)
        worksheet.set_column('AF1:AF1', 20)
        worksheet.set_column('AG1:AG1', 20)
        worksheet.set_column('AH1:AH1', 20)

        row = 1
        dtend = datetime.strptime(end_date,'%Y-%m-%d')
        week4_first = dtend-timedelta(days=21) # start minggu ke empat
        week4_second = dtend-timedelta(days=27) # end minggu ke empat
        week3_first = dtend-timedelta(days=14) # start minggu ketiga 
        week3_second = dtend-timedelta(days=20) # end minggu ketiga
        week2_first = dtend-timedelta(days=7) # start minggu kedua
        week2_second = dtend-timedelta(days=13) # end minggu kedua 
        week1_first = dtend # start minggu pertama
        week1_second = dtend-timedelta(days=6) #end minggu pertama
        #week2 = dtend.strftime("%V")
        #week1 = (week2_first).strftime("%V")
        # header
        worksheet.write('A%s' %(row), 'No' , wbf['header'])
        worksheet.write('B%s' %(row), 'NIK' , wbf['header'])
        worksheet.write('C%s' %(row), 'Nama' , wbf['header'])
        worksheet.write('D%s' %(row), 'Department' , wbf['header'])
        worksheet.write('E%s' %(row), 'STT' , wbf['header'])
        worksheet.write('F%s' %(row), 'Tanggal Mulai HR' , wbf['header'])
        worksheet.write('G%s' %(row), 'Upah Kotor/4 MInggu' , wbf['header'])
        worksheet.write('H%s' %(row), 'Gaji Pokok/HR' , wbf['header'])
        worksheet.write('I%s' %(row), 'Premi Hadir/HR' , wbf['header'])
        worksheet.write('J%s' %(row), 'Lembur Per Jam' , wbf['header'])
        worksheet.write('K%s' %(row), 'Minggu '+'1'+' (Lembur)' , wbf['header'])
        worksheet.write('L%s' %(row), 'Minggu '+'2'+' (Lembur)' , wbf['header'])
        worksheet.write('M%s' %(row), 'Minggu '+'1'+' (Hadir)' , wbf['header'])
        worksheet.write('N%s' %(row), 'Minggu '+'2'+' (Hadir)' , wbf['header'])
        worksheet.write('O%s' %(row), 'Minggu '+'1'+' (Absen)' , wbf['header'])
        worksheet.write('P%s' %(row), 'Minggu '+'2'+' (Absen)' , wbf['header'])
        worksheet.write('Q%s' %(row), 'Minggu '+'1'+' (Kuota)' , wbf['header'])
        worksheet.write('R%s' %(row), 'Minggu '+'2'+' (Kuota)' , wbf['header'])
        worksheet.write('S%s' %(row), 'Total Gaji Pokok' , wbf['header'])
        worksheet.write('T%s' %(row), 'Total Premi Hadir' , wbf['header'])
        worksheet.write('U%s' %(row), 'Total Lembur' , wbf['header'])
        worksheet.write('V%s' %(row), 'Bonus Mingguan' , wbf['header'])
        worksheet.write('W%s' %(row), 'Bonus Bulanan' , wbf['header'])
        worksheet.write('X%s' %(row), 'Total Uang Makan' , wbf['header'])
        worksheet.write('Y%s' %(row), 'Koreksian' , wbf['header'])
        worksheet.write('Z%s' %(row), 'Total Upah' , wbf['header'])
        worksheet.write('AA%s' %(row), 'Simp Pokok' , wbf['header'])
        worksheet.write('AB%s' %(row), 'Simp Wajib' , wbf['header'])
        worksheet.write('AC%s' %(row), 'Kasbon' , wbf['header'])
        worksheet.write('AD%s' %(row), 'Total Dibayarkan' , wbf['header'])
        worksheet.write('AE%s' %(row), 'Real' , wbf['header'])
        worksheet.write('AF%s' %(row), 'Bank' , wbf['header'])
        worksheet.write('AG%s' %(row), 'Masuk Minggu 1' , wbf['header'])
        worksheet.write('AH%s' %(row), 'Masuk Minggu 2' , wbf['header'])

        row+=1
        # value report
        attend = self.env['hr.attendance.finger']
        over = self.env['hr.overtime.employee']
        kuot = self.env['hr.kuota.history']
        holi = self.env['hr.holidays']
        no = 1
        #import pdb;pdb.set_trace()
        for co in result :
            em = co.employee_id
            ovt_week1 = 0
            ovt_week2 = 0
            lembur_week1 = 0
            lembur_week2 = 0
            hadir_week1 = 0
            hadir_week2 = 0
            kuota_week1 = 0
            kuota_week2 = 0
            bonus_mingguan = 0
            bonus_bulanan = 0
            koreksian = 0
            total_upah = 0
            simp_pokok = 0
            simp_wajib = 0
            net = 0
            harga_lembur = co.wage
            #slip_id = em.slip_ids.filtered(lambda i:calendar_id == calendar_id.id)
            slip_id = em.slip_ids.filtered(lambda i:i.date_to == end_date and i.contract_id.type_id.name == 'HARIAN')
            if slip_id :  
                slip_id = slip_id[0]
                
                if co.umk < co.wage :
                    harga_lembur = co.umk
                ovt_week1_exist = over.sudo().search([('employee_id','=',em.id),('state','=','validate'),
                                ('date','>=',week1_second),('date','<=',week1_first)])
                if ovt_week1_exist :
                    ovt_week1 = sum(ovt_week1_exist.mapped('total_jam'))
                ovt_week2_exist = over.sudo().search([('employee_id','=',em.id),('state','=','validate'),
                                ('date','>=',week2_second),('date','<=',week2_first)])
                if ovt_week2_exist :
                    ovt_week2 = sum(ovt_week2_exist.mapped('total_jam'))
                hadir_week1_exist = attend.sudo().search([('absen_id','=',em.absen_id),
                                                                ('date','>=',str(week1_second+timedelta(hours=-7))),
                                                                ('date','<=',str(week1_first)[:10]+' 16:59:59')])
                if hadir_week1_exist :
                    hadir_week1 = len(hadir_week1_exist) 
                hadir_week2_exist = attend.sudo().search([('absen_id','=',em.absen_id),
                                                                ('date','>=',str(week2_second+timedelta(hours=-7))),
                                                                ('date','<=',str(week2_first)[:10]+' 16:59:59')])
                if hadir_week2_exist :
                    hadir_week2 = len(hadir_week2_exist) 
                kuota_week1_exist = kuot.sudo().search([('employee_id','=',em.id),
                                                                ('date','>=',str(week1_second+timedelta(hours=-7))),
                                                                ('date','<=',str(week1_first)[:10]+' 16:59:59')]) 
                if kuota_week1_exist :
                    kuota_week1 = len(kuota_week1_exist)
                kuota_week1_exist = kuot.sudo().search([('employee_id','=',em.id),
                                                                ('date','>=',str(week1_second+timedelta(hours=-7))),
                                                                ('date','<=',str(week1_first)[:10]+' 16:59:59')]) 
                if kuota_week1_exist :
                    kuota_week1 = len(kuota_week1_exist)
                kuota_week2_exist = kuot.sudo().search([('employee_id','=',em.id),
                                                                ('date','>=',str(week2_second+timedelta(hours=-7))),
                                                                ('date','<=',str(week2_first)[:10]+' 16:59:59')]) 
                if kuota_week2_exist :
                    kuota_week2 = len(kuota_week2_exist) 
                if hadir_week1+kuota_week1 >= 6 :
                    bonus_mingguan += (hadir_week1+kuota_week1)*0.0125
                if hadir_week2+kuota_week2 >= 6 :
                    bonus_mingguan += (hadir_week2+kuota_week2)*0.0125
                bonus_bulanan_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'BBLH')
                if bonus_bulanan_exist :
                    bonus_bulanan = sum(bonus_bulanan_exist.mapped('amount'))
                koreksian_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'KRSN')
                if koreksian_exist :
                    koreksian = sum(koreksian_exist.mapped('amount'))
                total_upah_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'TGPH1' or bm.code == 'TGPH2' or bm.code == 'TGPH')
                if total_upah_exist :
                    total_upah = sum(total_upah_exist.mapped('amount'))
                simp_pokok_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'SP')
                if simp_pokok_exist :
                    simp_pokok = sum(simp_pokok_exist.mapped('amount'))
                simp_wajib_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'SW')
                if simp_wajib_exist :
                    simp_wajib = sum(simp_wajib_exist.mapped('amount'))
                net_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'NET')
                if net_exist :
                    net = sum(net_exist.mapped('amount'))

                worksheet.write('A%s' %row, no , wbf['content'])
                worksheet.write('B%s' %row, em.nik , wbf['content'])
                worksheet.write('C%s' %row, em.name , wbf['content'])
                worksheet.write('D%s' %row, em.department_id.name , wbf['content'])
                worksheet.write('E%s' %row, em.level_id.name , wbf['content'])
                worksheet.write('F%s' %row, em.work_date , wbf['content'])
                worksheet.write('G%s' %row, co.wage , wbf['content_number'])
                worksheet.write('H%s' %row, co.wage*0.65/28 , wbf['content_number'])
                worksheet.write('I%s' %row, co.wage*0.65/24 , wbf['content_number'])
                worksheet.write('J%s' %row, harga_lembur/56/4 * 1.5 , wbf['content_number'])
                worksheet.write('K%s' %row, ovt_week1, wbf['content_number'])
                worksheet.write('L%s' %row, ovt_week2, wbf['content_number'])
                worksheet.write('M%s' %row, hadir_week1 , wbf['content_number'])
                worksheet.write('N%s' %row, hadir_week2 , wbf['content_number'])
                worksheet.write('O%s' %row, 6-hadir_week1 , wbf['content_number'])
                worksheet.write('P%s' %row, 6-hadir_week1 , wbf['content_number'])
                worksheet.write('Q%s' %row, kuota_week1 , wbf['content_number'])
                worksheet.write('R%s' %row, kuota_week2 , wbf['content_number'])
                worksheet.write('S%s' %row, (co.wage*0.65/28)*(hadir_week1+hadir_week2+2), wbf['content_number'])
                worksheet.write('T%s' %row, (co.wage*0.65/24)*(hadir_week1+hadir_week2), wbf['content_number'])
                worksheet.write('U%s' %row, (harga_lembur/56/4 * 1.5)*(ovt_week1+ovt_week2) , wbf['content_number'])
                worksheet.write('V%s' %row, bonus_mingguan , wbf['content_number'])
                worksheet.write('W%s' %row, bonus_bulanan , wbf['content_number'])
                worksheet.write('X%s' %row, slip_id.contract_id.meals*(hadir_week1+hadir_week2), wbf['content_number'])
                worksheet.write('Y%s' %row, koreksian , wbf['content_number'])
                worksheet.write('Z%s' %row, total_upah, wbf['content_number'])
                worksheet.write('AA%s' %row, simp_pokok , wbf['content_number'])
                worksheet.write('AB%s' %row, simp_wajib , wbf['content_number'])
                worksheet.write('AC%s' %row, '' , wbf['content_number'])
                worksheet.write('AD%s' %row, net , wbf['content_number'])
                worksheet.write('AE%s' %row, net , wbf['content_number'])
                worksheet.write('AF%s' %row, em.bank_account_id.bank_id.name or '' , wbf['content_number'])
                worksheet.write('AG%s' %row, '' , wbf['content_number'])
                worksheet.write('AH%s' %row, '' , wbf['content_number'])

                row+=1
                no +=1

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'state_x': 'get', 'data_x': out, 'name': filename})
        fp.close()

        ir_model_data = self.env['ir.model.data']
        form_res = ir_model_data.get_object_reference('bgt_payroll_report', 'payroll_report_form_view')

        form_id = form_res and form_res[1] or False
        return {
            'name': 'Download .xlsx',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payroll.report.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    # report training
    def print_excel_report_training(self,start_date,end_date,category,result):
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = end_date
        filename = 'Payroll Report %s (%s).xlsx' % ( category,date_string)
        
        worksheet = workbook.add_worksheet('Payroll Report')
        worksheet.set_column('A1:A1', 5)
        worksheet.set_column('B1:B1', 20)
        worksheet.set_column('C1:C1', 50)
        worksheet.set_column('D1:D1', 20)
        worksheet.set_column('E1:E1', 20)
        worksheet.set_column('F1:F1', 20)
        worksheet.set_column('G1:G1', 20)
        worksheet.set_column('H1:H1', 20)
        worksheet.set_column('I1:I1', 20)
        worksheet.set_column('J1:J1', 20)
        worksheet.set_column('K1:K1', 20)
        worksheet.set_column('L1:L1', 20)
        worksheet.set_column('M1:M1', 20)
        worksheet.set_column('N1:N1', 20)
        worksheet.set_column('O1:O1', 20)
        worksheet.set_column('P1:P1', 20)
        worksheet.set_column('Q1:Q1', 20)
        worksheet.set_column('R1:R1', 20)
        worksheet.set_column('S1:S1', 20)
        worksheet.set_column('T1:T1', 20)
        worksheet.set_column('U1:U1', 20)
        worksheet.set_column('V1:V1', 20)
        worksheet.set_column('W1:W1', 20)
        worksheet.set_column('X1:X1', 20)
        worksheet.set_column('Y1:Y1', 20)
        worksheet.set_column('Z1:Z1', 20)
        worksheet.set_column('AA1:AA1', 10)
        worksheet.set_column('AB1:AB1', 10)

        row = 1
        dtend = datetime.strptime(end_date,'%Y-%m-%d')
        week4_first = dtend-timedelta(days=21) # start minggu ke empat
        week4_second = dtend-timedelta(days=27) # end minggu ke empat
        week3_first = dtend-timedelta(days=14) # start minggu ketiga 
        week3_second = dtend-timedelta(days=20) # end minggu ketiga
        week2_first = dtend-timedelta(days=7) # start minggu kedua
        week2_second = dtend-timedelta(days=13) # end minggu kedua 
        week1_first = dtend # start minggu pertama
        week1_second = dtend-timedelta(days=6) #end minggu pertama
        #week2 = dtend.strftime("%V")
        #week1 = (week2_first).strftime("%V")
        # header
        worksheet.write('A%s' %(row), 'No' , wbf['header'])
        worksheet.write('B%s' %(row), 'NIK' , wbf['header'])
        worksheet.write('C%s' %(row), 'Nama' , wbf['header'])
        worksheet.write('D%s' %(row), 'Department' , wbf['header'])
        worksheet.write('E%s' %(row), 'STT' , wbf['header'])
        worksheet.write('F%s' %(row), 'Tanggal Mulai HR' , wbf['header'])
        worksheet.write('G%s' %(row), 'Upah Kotor/4 Minggu' , wbf['header'])
        worksheet.write('H%s' %(row), 'Uang Saku/HR' , wbf['header'])
        worksheet.write('I%s' %(row), 'Lembur Per Jam' , wbf['header'])
        worksheet.write('J%s' %(row), 'Minggu '+"1"+' (Lembur)'  , wbf['header'])
        worksheet.write('K%s' %(row), 'Minggu '+"2"+' (Lembur)'  , wbf['header'])
        worksheet.write('L%s' %(row), 'Minggu '+"1"+' (Hadir)' , wbf['header'])
        worksheet.write('M%s' %(row), 'Minggu '+"2"+' (Hadir)' , wbf['header'])
        worksheet.write('N%s' %(row), 'Minggu '+"1"+' (Absen)' , wbf['header'])
        worksheet.write('O%s' %(row), 'Minggu '+"2"+' (Absen)' , wbf['header'])
        worksheet.write('P%s' %(row), 'Uang Saku' , wbf['header'])
        worksheet.write('Q%s' %(row), 'Total Lembur' , wbf['header'])
        worksheet.write('R%s' %(row), 'Total Uang Makan' , wbf['header'])
        worksheet.write('S%s' %(row), 'Koreksian' , wbf['header'])
        worksheet.write('T%s' %(row), 'Total Uang Saku' , wbf['header'])
        worksheet.write('U%s' %(row), 'Simp Pokok' , wbf['header'])
        worksheet.write('V%s' %(row), 'Simp Wajib' , wbf['header'])
        worksheet.write('W%s' %(row), 'Kasbon' , wbf['header'])
        worksheet.write('X%s' %(row), 'Total Dibayarkan' , wbf['header'])
        worksheet.write('Y%s' %(row), 'Real' , wbf['header'])
        worksheet.write('Z%s' %(row), 'Bank' , wbf['header'])
        worksheet.write('AA%s' %(row), '1' , wbf['header'])
        worksheet.write('AB%s' %(row), '2' , wbf['header'])

        row+=1
        # value report
        attend = self.env['hr.attendance.finger']
        over = self.env['hr.overtime.employee']
        kuot = self.env['hr.kuota.history']
        holi = self.env['hr.holidays']
        no = 1
        #import pdb;pdb.set_trace()
        for co in result :
            em = co.employee_id
            ovt_week1 = 0
            ovt_week2 = 0
            lembur_week1 = 0
            lembur_week2 = 0
            hadir_week1 = 0
            hadir_week2 = 0
            kuota_week1 = 0
            kuota_week2 = 0
            bonus_mingguan = 0
            bonus_bulanan = 0
            koreksian = 0
            total_upah = 0
            simp_pokok = 0
            simp_wajib = 0
            net = 0
            harga_lembur = co.wage
            #slip_id = em.slip_ids.filtered(lambda i:calendar_id == calendar_id.id)
            slip_id = em.slip_ids.filtered(lambda i:i.date_to == end_date and i.contract_id.type_id.name == 'TRAINING')
            if slip_id :  
                slip_id = slip_id[0]
                
                if co.umk < co.wage :
                    harga_lembur = co.umk
                ovt_week1_exist = over.sudo().search([('employee_id','=',em.id),('state','=','validate'),
                                ('date','>=',week1_second),('date','<=',week1_first)])
                if ovt_week1_exist :
                    ovt_week1 = sum(ovt_week1_exist.mapped('total_jam'))
                ovt_week2_exist = over.sudo().search([('employee_id','=',em.id),('state','=','validate'),
                                ('date','>=',week2_second),('date','<=',week2_first)])
                if ovt_week2_exist :
                    ovt_week2 = sum(ovt_week2_exist.mapped('total_jam'))
                hadir_week1_exist = attend.sudo().search([('absen_id','=',em.absen_id),
                                                                ('date','>=',str(week1_second+timedelta(hours=-7))),
                                                                ('date','<=',str(week1_first)[:10]+' 16:59:59')])
                if hadir_week1_exist :
                    hadir_week1 = len(hadir_week1_exist) 
                    if hadir_week1 > 6 :
                        hadir_week1 = 6
                hadir_week2_exist = attend.sudo().search([('absen_id','=',em.absen_id),
                                                                ('date','>=',str(week2_second+timedelta(hours=-7))),
                                                                ('date','<=',str(week2_first)[:10]+' 16:59:59')])
                if hadir_week2_exist :
                    hadir_week2 = len(hadir_week2_exist)
                    if hadir_week2 > 6 :
                        hadir_week2 = 6
                koreksian_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'KRSN')
                if koreksian_exist :
                    koreksian = sum(koreksian_exist.mapped('amount'))
                total_upah_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'TGPH1' or bm.code == 'TGPH2' or bm.code == 'TGPH')
                if total_upah_exist :
                    total_upah = sum(total_upah_exist.mapped('amount'))
                simp_pokok_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'SP')
                if simp_pokok_exist :
                    simp_pokok = sum(simp_pokok_exist.mapped('amount'))
                simp_wajib_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'SW')
                if simp_wajib_exist :
                    simp_wajib = sum(simp_wajib_exist.mapped('amount'))
                net_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'NET')
                if net_exist :
                    net = sum(net_exist.mapped('amount'))

                worksheet.write('A%s' %row, no , wbf['content'])
                worksheet.write('B%s' %row, em.nik , wbf['content'])
                worksheet.write('C%s' %row, em.name , wbf['content'])
                worksheet.write('D%s' %row, em.department_id.name , wbf['content'])
                worksheet.write('E%s' %row, em.level_id.name , wbf['content'])
                worksheet.write('F%s' %row, em.work_date , wbf['content'])
                worksheet.write('G%s' %row, co.wage , wbf['content_number'])
                worksheet.write('H%s' %row, co.wage/24 , wbf['content_number'])
                worksheet.write('I%s' %row, harga_lembur/56/4 * 1.5, wbf['content_number'])
                worksheet.write('J%s' %row, ovt_week1, wbf['content_number'])
                worksheet.write('K%s' %row, ovt_week2, wbf['content_number'])
                worksheet.write('L%s' %row, hadir_week1 , wbf['content_number'])
                worksheet.write('M%s' %row, hadir_week2 , wbf['content_number'])
                worksheet.write('N%s' %row, 6-hadir_week1 , wbf['content_number'])
                worksheet.write('O%s' %row, 6-hadir_week1 , wbf['content_number'])
                worksheet.write('P%s' %row, (co.wage/24) *(hadir_week1+hadir_week2) , wbf['content_number'])
                worksheet.write('Q%s' %row, (harga_lembur/56/4 * 1.5)*(ovt_week1+ovt_week2) , wbf['content_number'])
                worksheet.write('R%s' %row, slip_id.contract_id.meals*(hadir_week1+hadir_week2), wbf['content_number'])
                worksheet.write('S%s' %row, koreksian, wbf['content_number'])
                uang_saku = (co.wage/24 *(hadir_week1+hadir_week2)) - (co.meals*(hadir_week1+hadir_week2)) + koreksian
                worksheet.write('T%s' %row, uang_saku , wbf['content_number'])
                worksheet.write('U%s' %row, simp_pokok , wbf['content_number'])
                worksheet.write('V%s' %row, simp_wajib , wbf['content_number'])
                worksheet.write('W%s' %row, '', wbf['content_number'])
                worksheet.write('X%s' %row, net , wbf['content_number'])
                worksheet.write('Y%s' %row, net, wbf['content_number'])
                worksheet.write('Z%s' %row, em.bank_account_id.bank_id.name or ''  , wbf['content_number'])
                worksheet.write('AA%s' %row, '' , wbf['content_number'])
                worksheet.write('AB%s' %row, '' , wbf['content_number'])


                row+=1
                no +=1

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'state_x': 'get', 'data_x': out, 'name': filename})
        fp.close()

        ir_model_data = self.env['ir.model.data']
        form_res = ir_model_data.get_object_reference('bgt_payroll_report', 'payroll_report_form_view')

        form_id = form_res and form_res[1] or False
        return {
            'name': 'Download .xlsx',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payroll.report.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    # report borongan
    def print_excel_report_borongan(self,start_date,end_date,category,result):
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = end_date
        filename = 'Payroll Report %s (%s).xlsx' % ( category,date_string)
        
        worksheet = workbook.add_worksheet('Payroll Report')
        worksheet.set_column('A1:A1', 5)
        worksheet.set_column('B1:B1', 20)
        worksheet.set_column('C1:C1', 50)
        worksheet.set_column('D1:D1', 20)
        worksheet.set_column('E1:E1', 20)
        worksheet.set_column('F1:F1', 20)
        worksheet.set_column('G1:G1', 20)
        worksheet.set_column('H1:H1', 20)
        worksheet.set_column('I1:I1', 20)
        worksheet.set_column('J1:J1', 20)
        worksheet.set_column('K1:K1', 20)
        worksheet.set_column('L1:L1', 20)
        worksheet.set_column('M1:M1', 20)
        worksheet.set_column('N1:N1', 20)
        worksheet.set_column('O1:O1', 20)
        worksheet.set_column('P1:P1', 20)
        worksheet.set_column('Q1:Q1', 20)
        worksheet.set_column('R1:R1', 20)
        worksheet.set_column('S1:S1', 20)
        worksheet.set_column('T1:T1', 20)
        worksheet.set_column('U1:U1', 20)
        worksheet.set_column('V1:V1', 20)
        worksheet.set_column('W1:W1', 20)
        worksheet.set_column('X1:X1', 20)


        row = 1
        dtend = datetime.strptime(end_date,'%Y-%m-%d')
        week4_first = dtend-timedelta(days=21) # start minggu ke empat
        week4_second = dtend-timedelta(days=27) # end minggu ke empat
        week3_first = dtend-timedelta(days=14) # start minggu ketiga 
        week3_second = dtend-timedelta(days=20) # end minggu ketiga
        week2_first = dtend-timedelta(days=7) # start minggu kedua
        week2_second = dtend-timedelta(days=13) # end minggu kedua 
        week1_first = dtend # start minggu pertama
        week1_second = dtend-timedelta(days=6) #end minggu pertama
        #week2 = dtend.strftime("%V")
        #week1 = (week2_first).strftime("%V")
        # header
        worksheet.write('A%s' %(row), 'No' , wbf['header'])
        worksheet.write('B%s' %(row), 'NIK' , wbf['header'])
        worksheet.write('C%s' %(row), 'Nama' , wbf['header'])
        worksheet.write('D%s' %(row), 'Department' , wbf['header'])
        worksheet.write('E%s' %(row), 'STT' , wbf['header'])
        worksheet.write('F%s' %(row), 'T/T Ref' , wbf['header'])
        worksheet.write('G%s' %(row), 'UT' , wbf['header'])
        worksheet.write('H%s' %(row), 'UHK' , wbf['header'])
        worksheet.write('I%s' %(row), 'ABS' , wbf['header'])
        worksheet.write('J%s' %(row), 'TK'  , wbf['header'])
        worksheet.write('K%s' %(row), 'Upah BR'  , wbf['header'])
        worksheet.write('L%s' %(row), 'KRJJN' , wbf['header'])
        worksheet.write('M%s' %(row), 'BNS/Pot' , wbf['header'])
        worksheet.write('N%s' %(row), 'Total UT' , wbf['header'])
        worksheet.write('O%s' %(row), 'Koreksian' , wbf['header'])
        worksheet.write('P%s' %(row), 'Total Upah' , wbf['header'])
        worksheet.write('Q%s' %(row), 'Real' , wbf['header'])
        worksheet.write('R%s' %(row), 'Simp Pokok' , wbf['header'])
        worksheet.write('S%s' %(row), 'Simp Wajib' , wbf['header'])
        worksheet.write('T%s' %(row), 'Kasbon' , wbf['header'])
        worksheet.write('U%s' %(row), 'Total' , wbf['header'])
        worksheet.write('V%s' %(row), 'Total Real', wbf['header'])
        worksheet.write('W%s' %(row), 'Total Gabungan' , wbf['header'])
        worksheet.write('X%s' %(row), 'Bank Pajak' , wbf['header'])

        row+=1
        # value report
        attend = self.env['hr.attendance.finger']
        manual = self.env['hr.payslip.manual']
        no = 1
        #import pdb;pdb.set_trace()
        for co in result :
            em = co.employee_id

            hadir_week1 = 0
            hadir_week2 = 0
            br = 0
            kerajinan = 0
            bonus =0
            koreksian = 0
            total_upah = 0
            simp_pokok = 0
            simp_wajib = 0
            kasbon = 0
            net = 0
            harga_lembur = co.wage
            #slip_id = em.slip_ids.filtered(lambda i:calendar_id == calendar_id.id)
            slip_id = em.slip_ids.filtered(lambda i:i.date_to == end_date and i.contract_id.type_id.name == 'BORONGAN')
            if slip_id :  
                slip_id = slip_id[0]
                
                if co.umk < co.wage :
                    harga_lembur = co.umk

                if hadir_week1_exist :
                    hadir_week1 = len(hadir_week1_exist) 
                    if hadir_week1 > 6 :
                        hadir_week1 = 6
                hadir_week2_exist = attend.sudo().search([('absen_id','=',em.absen_id),
                                                                ('date','>=',str(week2_second+timedelta(hours=-7))),
                                                                ('date','<=',str(week2_first)[:10]+' 16:59:59')])
                if hadir_week2_exist :
                    hadir_week2 = len(hadir_week2_exist)
                    if hadir_week2 > 6 :
                        hadir_week2 = 6

                manual_exist = manual.sudo().search([('name','=',end_date),('employee_id','=',em.id)],limit=1)
                if manual_exist :
                    br = manual_exist.upah_br1 + manual_exist.upah_br2
                    kerajinan = manual_exist.kerajinan1 + manual_exist.kerajinan12
                    bonus = manual_exist.bns_pot1 +manual_exist.bns_pot2
                    kasbon = manual_exist.kasbon
                if total_upah_exist :
                    total_upah = sum(total_upah_exist.mapped('amount'))
                simp_pokok_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'SP')
                if simp_pokok_exist :
                    simp_pokok = sum(simp_pokok_exist.mapped('amount'))
                simp_wajib_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'SW')
                if simp_wajib_exist :
                    simp_wajib = sum(simp_wajib_exist.mapped('amount'))
                net_exist = slip_id.line_ids.filtered(lambda bm:bm.code == 'NET')
                if net_exist :
                    net = sum(net_exist.mapped('amount'))

                worksheet.write('A%s' %row, no , wbf['content'])
                worksheet.write('B%s' %row, em.nik , wbf['content'])
                worksheet.write('C%s' %row, em.name , wbf['content'])
                worksheet.write('D%s' %row, em.department_id.name , wbf['content'])
                worksheet.write('E%s' %row, em.level_id.name , wbf['content'])
                worksheet.write('F%s' %row, em.bank_account_id.bank_id.name or '' , wbf['content'])
                worksheet.write('G%s' %row, 1500 , wbf['content_number'])
                worksheet.write('H%s' %row,'', wbf['content_number'])
                worksheet.write('I%s' %row, '', wbf['content_number'])
                worksheet.write('J%s' %row, '', wbf['content_number'])
                worksheet.write('K%s' %row, br, wbf['content_number'])
                worksheet.write('L%s' %row, kerajinan , wbf['content_number'])
                worksheet.write('M%s' %row, bonus , wbf['content_number'])
                worksheet.write('N%s' %row, '' , wbf['content_number'])
                worksheet.write('O%s' %row, '' , wbf['content_number'])
                worksheet.write('P%s' %row, br+kerajinan+bonus , wbf['content_number'])
                worksheet.write('Q%s' %row, round(br+kerajinan+bonus,-3), wbf['content_number'])
                worksheet.write('R%s' %row, simp_pokok, wbf['content_number'])
                worksheet.write('S%s' %row, simp_wajib, wbf['content_number'])
                worksheet.write('T%s' %row, kasbon , wbf['content_number'])
                worksheet.write('U%s' %row, round(br+kerajinan+bonus,-3) - simp_wajib - simp_pokok - kasbon , wbf['content_number'])
                worksheet.write('V%s' %row, round(br+kerajinan+bonus,-3) - simp_wajib - simp_pokok - kasbon , wbf['content_number'])
                worksheet.write('W%s' %row, round(br+kerajinan+bonus,-3) - simp_wajib - simp_pokok - kasbon, wbf['content_number'])
                worksheet.write('X%s' %row, em.bank_account_id.bank_id.name , wbf['content_number'])

                row+=1
                no +=1

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'state_x': 'get', 'data_x': out, 'name': filename})
        fp.close()

        ir_model_data = self.env['ir.model.data']
        form_res = ir_model_data.get_object_reference('bgt_payroll_report', 'payroll_report_form_view')

        form_id = form_res and form_res[1] or False
        return {
            'name': 'Download .xlsx',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payroll.report.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

PayrollReportWizard()
