import xlsxwriter, base64, pytz, string, re
from odoo import fields, models, api, _
from cStringIO import StringIO
from datetime import datetime, timedelta
from pytz import timezone
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from string import ascii_uppercase
import itertools
import xlwt

class AttendaneReport(models.TransientModel):
    _name = "attendance.report"
    _description = "Attendance Report"

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))

    state_x = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    data_x = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date', default=fields.Datetime.now())
    department_ids = fields.Many2many("hr.department", string="Department")
    employee_ids = fields.Many2many("hr.employee", string="Employee")
    status_ids = fields.Many2many("hr.contract.type", string="Status")
    job_level_ids = fields.Many2many("hr.job.level", string="Job Level")
    job_position_ids = fields.Many2many("hr.job", string="Job Position")
    type = fields.Selection([('bydept', 'By Department'), ('byemployee', 'By Employee'), 
                            ('bystatus','By Status'),('byjoblevel','By Job Level'),('byjobposition','By Job Position'),('all', 'All')], default='bydept')

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

        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = start_date + ' to ' + end_date
        filename = 'Attendance Report %s.xlsx' % ( date_string)
        if self.type == 'bydept' :
            result = self.env['hr.employee'].sudo().search([('department_id','in',self.department_ids.ids)], order='department_id asc')
        elif self.type == 'byemployee' :
            result = self.env['hr.employee'].sudo().search([('id', 'in', self.employee_ids.ids)], order='nik asc')
        elif self.type == 'bystatus' :
            result = self.env['hr.employee'].sudo().search([('status_karyawan', 'in', self.status_ids.ids)], order='nik asc')
        elif self.type == 'byjoblevel' :
            result = self.env['hr.employee'].sudo().search([('level_id', 'in', self.job_level_ids.ids)], order='nik asc')
        elif self.type == 'byjobposition' :
            result = self.env['hr.employee'].sudo().search([('job_id', 'in', self.job_position_ids.ids)], order='nik asc')
        else :
            result = self.env['hr.employee'].sudo().search([])
        if not result:
            raise UserError(_('Data not found !'))
        
        worksheet = workbook.add_worksheet('Attendance Report')
        worksheet.set_column('A1:A1', 5)
        worksheet.set_column('B1:B1', 20)
        worksheet.set_column('C1:C1', 50)
        worksheet.set_column('D1:D1', 20)
        worksheet.set_column('E1:E1', 20)
        worksheet.set_column('F1:F1', 20)

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
                    if col not in ('A','B','C','D','E','F') :
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
            total_absen = False
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
                    if len(sup2) == 1 :
                        col = str(sup2[0])
                    else :
                        col = str(sup2[0]+sup2[1])

                    if not hadir :
                        worksheet.write('%s%s' % (col,row), 'Hadir' , wbf['header_blue'])
                        hadir = True
                        continue
                    elif not absen :
                        worksheet.write('%s%s' % (col,row), 'Absen' , wbf['header_violet'])
                        absen = True
                        continue
                    elif not kuota :
                        worksheet.write('%s%s' % (col,row), 'Kuota' , wbf['header_yellow'])
                        kuota = True
                        continue
                    elif not sakit :
                        worksheet.write('%s%s' % (col,row), 'Sakit' , wbf['header_green'])
                        sakit = True
                        continue
                    elif not izin :
                        worksheet.write('%s%s' % (col,row), 'Izin' , wbf['header_orange'])
                        izin = True
                        continue
                    elif not total_absen :
                        worksheet.set_column('%s1:%s1' % (col,col), 20)
                        worksheet.write('%s%s' % (col,row), 'Total Tidak hadir' , wbf['header_red'])
                        total_absen = True
                        continue
                    else :
                        break
            if stop :
                break

        # value report
        attend = self.env['hr.attendance.finger']
        over = self.env['hr.overtime']
        kuot = self.env['hr.kuota.history']
        holi = self.env['hr.holidays']
        no = 1
        for em in result :
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
            for size3 in itertools.count(1):
                hadir = False
                sakit = False
                absen = False
                kuota = False
                izin = False
                total_absen = False
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
                            worksheet.write('%s%s' % (col,row), em.department_id.name, wbf['content'])
                        elif col == 'E':
                            worksheet.write('%s%s' % (col,row), em.level_id.name, wbf['content'])
                        elif col == 'F':
                            worksheet.write('%s%s' % (col,row), em.work_date, wbf['content_date'])
                        else :
                            worksheet.set_column('%s1:%s1' % (col,col), 2)
                            hadir_exist = attend.sudo().search([('absen_id','=',em.absen_id),
                                                                ('date','>=',str(dtstart3+timedelta(hours=-7))),
                                                                ('date','<=',str(dtstart3)[:10]+' 16:59:59')])
                            if hadir_exist :
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
                        elif not total_absen :
                            worksheet.set_column('%s1:%s1' % (col,col), 20)
                            worksheet.write('%s%s' % (col,row), t_absen+t_kuota+t_sakit+t_izin , wbf['content_number'])
                            total_absen = True
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
        form_res = ir_model_data.get_object_reference('bgt_attendance_report', 'attendance_report_form_view')

        form_id = form_res and form_res[1] or False
        return {
            'name': 'Download .xlsx',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'attendance.report',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }


AttendaneReport()