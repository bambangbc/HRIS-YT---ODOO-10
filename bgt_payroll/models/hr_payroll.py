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
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, tools, _, SUPERUSER_ID
import babel

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    @api.multi
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            contracts = self.env['hr.contract'].search([('id','=',slip_data['value'].get('contract_id'))]).type_id.name
            if contracts == 'BULANAN' or contracts == 'STAFF'  :
                cuti = slip_data['value'].get('worked_days_line_ids')[0]
                wc = slip_data['value'].get('worked_days_line_ids')[1]
            else :
                cuti = 0
                wc = 0
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'cuti' : cuti,
                'work_cuti' : wc,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')][2:],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
            }
            payslips += self.env['hr.payslip'].create(res)
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}

class HRPayslip(models.Model):
    _inherit = "hr.payslip"


    date_from = fields.Date(string='Date From', readonly=True, required=True,
        default=str(datetime.now()+ relativedelta(months=-1, day=26)), states={'draft': [('readonly', False)]})
    date_to = fields.Date(string='Date To', readonly=True, required=True,
         default=time.strftime('%Y-%m-25'),
        states={'draft': [('readonly', False)]})
    net = fields.Float('Net')
    status_karyawan = fields.Many2one("hr.contract.type", "Type Contract", related="employee_id.status_karyawan", store=True)
    cuti = fields.Float(string="cuti")
    work_cuti = fields.Float(string="work cuti")

    line_ids = fields.One2many('hr.payslip.line', 'slip_id', string='Payslip Lines', readonly=True,
        states={'draft': [('readonly', False)]})

    #tambahan
    paytoll_calendar_id = fields.Many2one('hr.calendarpayroll','Calendar')

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):

        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Salary Slip of %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        self.company_id = employee.company_id

        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                return
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

        if not self.contract_id.struct_id:
            return
        self.struct_id = self.contract_id.struct_id

        #computation of the salary input
        worked_days_line_ids = self.get_worked_day_lines(contract_ids, date_from, date_to)[2:]
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines
        
        input_line_ids = self.get_inputs(contract_ids, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        worked_cuti = self.get_worked_day_lines(contract_ids, date_from, date_to)
        self.cuti = worked_cuti[0]
        self.work_cuti = worked_cuti[1] 
        return

    def compute_sheet(self):
        for payslip in self:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            #delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            net = 0
            for lin in self.env['hr.payslip'].get_payslip_lines(contract_ids,payslip.id):
                if lin['code'] != 'GROSS' and lin['code'] != 'NET':
                    net += lin['amount']
            payslip.write({'net':round(net,-3)})
            lines = [(0, 0, line) for line in self.get_payslip_lines(contract_ids, payslip.id)]
            # tambahan
            obj_bonus = self.env['hr.calendarpayroll']
            calendar = False
            check_bonus = obj_bonus.search([('date','=',payslip.date_to),('minggu','=','2')],limit=1)
            if check_bonus :
                calendar = check_bonus.id
            payslip.write({'line_ids': lines, 'number': number, 'paytoll_calendar_id' : calendar})
        return True


    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        #import pdb;pdb.set_trace()
        def was_on_leave(employee_id, datetime_day):
            day = fields.Date.to_string(datetime_day)
            return self.env['hr.holidays'].search([
                ('state', '=', 'validate'),
                ('employee_id', '=', employee_id),
                ('type', '=', 'remove'),
                ('date_from', '<=', day),
                ('date_to', '>=', day)
            ], limit=1).holiday_status_id.name

        obj_shift = self.env['hr.rolling.shift.detail']
        res = []
        #fill only if the contract as a working schedule linked
        # for contract in self.env['hr.contract'].browse(contract_ids).filtered(lambda contract: contract.working_hours):
        total_kuotas = 0
        sisa_kuotas = 0
        cuti = 0
        work_cuti = 0
        for contract in self.env['hr.contract'].browse(contract_ids):
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                attendances = {
                     'name': _("Normal hari Kerja"),
                     'sequence': 1,
                     'code': 'Work100',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" or contract.type_id.name == "BORONGAN":
                attendances1 = {
                     'name': _("Normal hari Kerja Minggu Ke 1"),
                     'sequence': 2,
                     'code': 'Work1001',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
                attendances2 = {
                     'name': _("Normal hari Kerja Minggu Ke 2"),
                     'sequence': 3,
                     'code': 'Work1002',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN" :
                presences = {
                     'name': _("Kehadiran"),
                     'sequence': 4,
                     'code': 'Presences',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" or contract.type_id.name == "BORONGAN":
                presences_1 = {
                     'name': _("Kehadiran Minggu Ke 1 "),
                     'sequence': 5,
                     'code': 'Presences1',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
                presences_2 = {
                     'name': _("Kehadiran Minggu ke 2 "),
                     'sequence': 7,
                     'code': 'Presences2',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                overtime = {
                     'name': _("Lembur"),
                     'sequence': 7,
                     'code': 'Overtime',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" :
                overtime_1 = {
                     'name': _("Lembur minggu ke 1"),
                     'sequence': 8,
                     'code': 'Overtime1',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
                overtime_2 = {
                     'name': _("Lembur minggu ke 2"),
                     'sequence': 9,
                     'code': 'Overtime2',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                day_off = {
                     'name': _("Day off"),
                     'sequence': 10,
                     'code': 'day_off',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" :
                day_off_1 = {
                     'name': _("Day off minggu ke 1"),
                     'sequence': 11,
                     'code': 'day_off1',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
                day_off_2 = {
                     'name': _("Day off minggu ke 2"),
                     'sequence': 12,
                     'code': 'day_off2',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                day_off_absen = {
                     'name': _("Day off absen"),
                     'sequence': 13,
                     'code': 'day_off_absen',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" :
                day_off_absen_1 = {
                     'name': _("Day off absen minggu ke 1"),
                     'sequence': 14,
                     'code': 'day_off_absen1',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
                day_off_absen_2 = {
                     'name': _("Day off absen minggu ke 2"),
                     'sequence': 15,
                     'code': 'day_off_absen2',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                kuota = {
                     'name': _("Kuota Terpakai"),
                     'sequence': 16,
                     'code': 'kuota',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" :
                kuota_1 = {
                     'name': _("Kuota minggu ke 1"),
                     'sequence': 17,
                     'code': 'kuota1',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
                kuota_2 = {
                     'name': _("Kuota minggu ke 2"),
                     'sequence': 18,
                     'code': 'kuota2',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                alpha = {
                     'name': _("Alpha"),
                     'sequence': 19,
                     'code': 'Alpha',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" :
                alpha_1 = {
                     'name': _("Alpha Minggu Ke 1"),
                     'sequence': 20,
                     'code': 'Alpha1',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
                alpha_2 = {
                     'name': _("Alpha Minggu ke 2"),
                     'sequence': 21,
                     'code': 'Alpha2',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            #import pdb;pdb.set_trace()
            if contract.type_id.name == 'HARIAN' :
                #bonus_mingguan = {
                #    'name': _("Bonus Mingguan"),
                #    'sequence': 10,
                #    'code': 'BM',
                #    'number_of_days': 0.0,
                #    'number_of_hours': 0.0,
                #    'contract_id': contract.id
                #}
                bonus_mingguan_1 = {
                    'name': _("Bonus Mingguan ke 1"),
                    'sequence': 22,
                    'code': 'BM1',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id
                }
                bonus_mingguan_2 = {
                    'name': _("Bonus Mingguan Ke 2"),
                    'sequence': 23,
                    'code': 'BM2',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id
                }


            leaves = {}
            day_from = fields.Datetime.from_string(date_from)
            day_to = fields.Datetime.from_string(date_to)
            nb_of_days = (day_to - day_from).days + 1
            total_kuota = 0
            sisa_kuota = 0
            ct = 0
            kuotas = self.env['hr.kuota'].search([('employee_id','=',contract.employee_id.id),('is_active','=',True)])
            for kuotas in kuotas :
                sisa_kuota = kuotas.sisa_kuota
                total_kuota = kuotas.total_kuota
            x = 0
            y = 0
            z = 0
            for day in range(0, nb_of_days):
                employee_id = contract.employee_id.id
                datas = day_from + timedelta(days=day)
                tanggal = datas.strftime("%Y-%m-%d")
                obj_over = self.env['hr.overtime']
                obj_ovemp = self.env['hr.overtime.employee']
                obj_att = self.env['hr.attendance.finger']
                # lembur pegawai dengan schedule
                src_over = obj_over.search([('tgl_lembur','=',tanggal),('state','=','validate')])
                for overt in src_over :
                    src_ovemp = obj_ovemp.search([('overtime_id','=',overt.id),('employee_id','=',employee_id)],limit=1)
                    if src_ovemp :
                        jumlah = src_ovemp.ovt_hour
                        if overt.hari_libur:
                            date_start = tanggal + ' 00:00:01'
                            date_end = tanggal + ' 16:00:00'
                            att = obj_att.search([('date','>=',date_start),('date','<=',date_end),('absen_id','=',int(contract.employee_id.absen_id))])
                            if att :
                                day_off['number_of_hours'] += jumlah
                                if jumlah >= 2.5 :
                                    day_off['number_of_days'] += 1
                                if day <= 6 and contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" :
                                    day_off_1['number_of_hours'] += jumlah
                                    if jumlah >= 2.5 :
                                        day_off_1['number_of_days'] += 1
                                elif day >= 7 and contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" :
                                    day_off_2['number_of_hours'] += jumlah
                                    if jumlah >= 2.5 :
                                        day_off_2['number_of_days'] += 1
                            else :
                                if day <= 7 :
                                    x = 1
                                elif day >= 8 :
                                    y = 1
                                if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                                    day_off_absen['number_of_hours'] += jumlah
                                    day_off_absen['number_of_days'] += 1
                                if day <= 6 and contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" :
                                    day_off_absen_1['number_of_hours'] += jumlah
                                    day_off_1['number_of_days'] += 1
                                elif day >= 7 and contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING":
                                    day_off_2['number_of_hours'] += jumlah
                                    day_off_2['number_of_days'] += 1
                        else:
                            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING":
                                overtime['number_of_hours'] += jumlah
                                if jumlah >= 2.5 :
                                    overtime['number_of_days'] += 1
                            #import pdb;pdb.set_trace()
                            if day <= 6 and contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING":
                                overtime_1['number_of_hours'] += jumlah
                                if jumlah >= 2.5 :
                                    overtime_1['number_of_days'] += 1
                            elif day >= 7 and contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING":
                                overtime_2['number_of_hours'] += jumlah
                                if jumlah >= 2.5 :
                                    overtime_2['number_of_days'] += 1

                date = (day_from + timedelta(days=day))
                dates = str(date)[:10]
                # jika kerja shift-shift an
                if contract.shift_working_schedule :
                    working_hours_exist = obj_shift.search([('employee_id','=',contract.employee_id.id),('date_start','<=',dates),('date_end','>=',dates)], limit=1, order='id desc')
                    xxx = 0
                    for att in working_hours_exist.schedule_id.attendance_ids :
                        if str(datetime.strptime((dates),"%Y-%m-%d").isoweekday()- 1) == att.dayofweek :
                            xxx = 1
                    if not working_hours_exist or xxx == 0:
                        continue
                    if working_hours_exist.schedule_id.shift_type == 'shift malam' :
                        working_hours_on_day = 8.0
                    else:
                        working_hours_on_day = working_hours_exist.schedule_id.working_hours_on_day(day_from + timedelta(days=day))
                    #import pdb;pdb.set_trace()
                else :
                    # kerja non shift
                    working_hours_on_day = contract.working_hours.working_hours_on_day(day_from + timedelta(days=day))
                #import pdb;pdb.set_trace()
                if working_hours_on_day:
                    #the employee had to work
                    leave_type = was_on_leave(employee_id, day_from + timedelta(days=day))
                    if leave_type:
                        #if he was on leave, fill the leaves dict
                        ct = +1
                        if leave_type in leaves:
                            leaves[leave_type]['number_of_days'] += 1.0
                            leaves[leave_type]['number_of_hours'] += working_hours_on_day
                        else:
                            leaves[leave_type] = {
                                'name': leave_type,
                                'sequence': 6,
                                'code': leave_type,
                                'number_of_days': 1.0,
                                'number_of_hours': working_hours_on_day,
                                'contract_id': contract.id,
                            }
                        if day <=6 and leaves[leave_type]['code'] == 'Public Holidays' :
                                attendances1['number_of_days'] += 1.0
                                attendances1['number_of_hours'] += working_hours_on_day
                        if day >=7 and leaves[leave_type]['code'] == 'Public Holidays' :
                                attendances2['number_of_days'] += 1.0
                                attendances2['number_of_hours'] += working_hours_on_day
                        #import pdb;pdb.set_trace()
                    else:
                        #add the input vals to tmp (increment if existing)
                        if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                            attendances['number_of_days'] += 1.0
                            attendances['number_of_hours'] += working_hours_on_day
                        if  contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" or contract.type_id.name == "BORONGAN":
                            if day <=6 :
                                attendances1['number_of_days'] += 1.0
                                attendances1['number_of_hours'] += working_hours_on_day
                        if  contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" or contract.type_id.name == "BORONGAN":
                            if day >=7 :
                                attendances2['number_of_days'] += 1.0
                                attendances2['number_of_hours'] += working_hours_on_day

                        #kehadiran
                        real_working_hours_on_day = self.env['hr.attendance'].real_working_hours_on_day(employee_id, day_from + timedelta(days=day))
                        if real_working_hours_on_day >= 0.000000000000000001 :
                            #import pdb;pdb.set_trace()
                            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                                presences['number_of_days'] += 1.0
                                presences['number_of_hours'] += working_hours_on_day  
                            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" or contract.type_id.name == "BORONGAN":
                                if day <=6 :
                                    presences_1['number_of_days'] += 1.0
                                    presences_1['number_of_hours'] += working_hours_on_day
                            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" or contract.type_id.name == "BORONGAN":
                                if day >= 7 :
                                    presences_2['number_of_days'] += 1.0
                                    presences_2['number_of_hours'] += working_hours_on_day
                        elif sisa_kuota > sisa_kuotas:
                            cek_kuota = self.env['tbkuota'].search([('name','=',tanggal)])
                            if not cek_kuota :
                                total_kuotas += 1
                                sisa_kuotas += 1
                                if contract.type_id.name == 'HARIAN' :
                                    if day <=6 :
                                        kuota_1['number_of_days'] += 1
                                    elif day >= 7 :
                                        kuota_2['number_of_days'] += 1
                                if contract.type_id.name == "HARIAN" and day <= 7 and real_working_hours_on_day <= 0 :
                                    if sisa_kuota <= sisa_kuotas :
                                        x = 1
                                if contract.type_id.name == "HARIAN" and day >= 8 and day < 14 and real_working_hours_on_day <= 0 :
                                    if sisa_kuota <= sisa_kuotas :
                                        y = 1
            xy = 2 - x - y
            leaves = [value for key, value in leaves.items()]
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING"  and contract.type_id.name != "BORONGAN":
                res += [attendances]
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" or contract.type_id.name == "BORONGAN":
                res += [attendances1] + [attendances2]
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                res += [presences]
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" or contract.type_id.name == "BORONGAN":
                res += [presences_1] + [presences_2]
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                res += [overtime]
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" :
                res += [overtime_1] + [overtime_2]
            res += leaves
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                res += [day_off]
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING":
                res += [day_off_1] + [day_off_2]
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                res += [day_off_absen]
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" :
                res += [day_off_absen_1] + [day_off_absen_2]
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                kuota['number_of_days'] = total_kuotas
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                res += [kuota] 
            if contract.type_id.name == 'HARIAN' :
                res += [kuota_1] + [kuota_2]
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                total_alpha = attendances['number_of_days'] - presences['number_of_days'] - kuota['number_of_days']
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                alpha['number_of_days'] = total_alpha
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING" :
                alpha_1['number_of_days'] = attendances1['number_of_days'] - presences_1['number_of_days'] - kuota_1['number_of_days']
                alpha_2['number_of_days'] = attendances2['number_of_days'] - presences_2['number_of_days'] - kuota_2['number_of_days']
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN":
                res += [alpha]
            if contract.type_id.name == 'HARIAN' or contract.type_id.name == "TRAINING":
                res += [alpha_1] + [alpha_2]
            if contract.type_id.name == 'HARIAN' :
            	if alpha_1['number_of_days'] == 0 :
            		bonus_mingguan_1['number_of_days'] += 1
            	if alpha_2['number_of_days'] == 0 :
                	bonus_mingguan_2['number_of_days'] += 1
             	res += [bonus_mingguan_1]
             	res += [bonus_mingguan_2]
            if contract.type_id.name != 'HARIAN' and contract.type_id.name != "TRAINING" and contract.type_id.name != "BORONGAN": 
               cuti = ct
               work_cuti = ct + attendances['number_of_days']
        return [cuti] + [work_cuti] + res 

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        res = []
        for contracts in self.env['hr.contract'].browse(contract_ids):
            structure_ids = contracts.get_all_structures()
            rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
            sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
            inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')
            simpanan_pokok = {
                     'name': _("Simpanan Pokok"),
                     'sequence': 1,
                     'code': 'SIPO',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }
            simpanan_wajib = {
                     'name': _("Simpanan Wajib"),
                     'sequence': 2,
                     'code': 'SIWA',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }
            bpjs_kesehatan = {
                     'name': _("BPJS Kesehatan"),
                     'sequence': 3,
                     'code': 'BPKES',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }
            bpjs_tenagakerja = {
                     'name': _("BPJS Tenagakerja"),
                     'sequence': 4,
                     'code': 'BPTEN',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }
            tunjangan = {
                     'name': _("Tunjangan"),
                     'sequence': 5,
                     'code': 'TUN',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }
            kasbon = {
                     'name': _("Kasbon"),
                     'sequence': 6,
                     'code': 'KAS',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }

            upah_br1 = {
                     'name': _("Upah Br Minggu Ke 1"),
                     'sequence': 7,
                     'code': 'UPB1',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }

            upah_br2 = {
                     'name': _("Upah Br Minggu Ke 2"),
                     'sequence': 8,
                     'code': 'UPB2',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }

            kerajinan1 = {
                     'name': _("Kerajinan Minggu Ke 1"),
                     'sequence': 9,
                     'code': 'KJN1',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }

            kerajinan2 = {
                     'name': _("Kerajinan Minggu Ke 2"),
                     'sequence': 10,
                     'code': 'KJN2',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }

            bns_pot1 = {
                     'name': _("Bonus/Potongan Minggu Ke 1"),
                     'sequence': 11,
                     'code': 'BPOT1',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }

            bns_pot2 = {
                     'name': _("Bonus/Potongan Minggu Ke 2"),
                     'sequence': 12,
                     'code': 'BPOT2',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }

            koreksian = {
                     'name': _("Koreksian"),
                     'sequence': 13,
                     'code': 'KRS',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }

            bonus_bulanan = {
                    'name': _("Bonus Bulanan Harian"),
                    'sequence': 14,
                    'code': 'BBH',
                    'amount': 0.0,
                    'contract_id': contracts.id,
            }
            koperasi = self.env['hr.koperasi']
            check_koperasi_pokok = self.env['hr.koperasi'].search([('employee_id','=',contracts.employee_id.id),('sisa_cicilan','>',0),('state','=','validate'),('mekanisme','=','otomatis'),('type','=','pokok')], order="id asc", limit=1)
            if check_koperasi_pokok :
                for result in check_koperasi_pokok :
                    angsuran = result.angsuran
                    sisa = result.sisa_cicilan
                    for pokok in result.kasbon_ids:
                        if angsuran - (sisa - 1) == pokok.cicilan:
                            simpanan_pokok['amount'] = pokok.nominal
            check_koperasi_wajib = self.env['hr.koperasi'].search([('employee_id','=',contracts.employee_id.id),('sisa_cicilan','>',0),('state','=','validate'),('mekanisme','=','otomatis'),('type','=','wajib')], order="id asc", limit=1)
            if check_koperasi_wajib :
                for result in check_koperasi_wajib :
                    angsuran = result.angsuran
                    sisa = result.sisa_cicilan
                    for wajib in result.kasbon_ids:
                        if angsuran - (sisa - 1) == wajib.cicilan:
                            simpanan_wajib['amount'] = wajib.nominal

            import_payslip = self.env['hr.payslip.manual']
            if contracts.type_id.name != 'BORONGAN' :
                check_import = import_payslip.search([('employee_id','=',contracts.employee_id.id),('name','=',date_to),('status','=',False)], limit=1)
            else :
                check_import = import_payslip.search([('employee_id','=',contracts.employee_id.id),('name','=',date_to),('status','=',True)], limit=1)

            if check_import :
                for result in check_import :
                    bpjs_kesehatan['amount'] = result.bpjs_kes
                    bpjs_tenagakerja['amount'] = result.bpjs_ket
                    tunjangan['amount'] = result.tunjangan
                    kasbon['amount'] = result.kasbon
                    upah_br1['amount'] = result.upah_br1
                    upah_br2['amount'] = result.upah_br2
                    kerajinan1['amount'] = result.kerajinan1
                    kerajinan2['amount'] = result.kerajinan2
                    bns_pot1['amount'] = result.bns_pot1
                    bns_pot2['amount'] = result.bns_pot2

            import_koreksi = self.env['hr.koreksi']
            check_koreksi = import_koreksi.search([('employee_id','=',contracts.employee_id.id),('name','=',date_to),('state','=','done')])
            if check_koreksi:
                for result in check_koreksi :
                    koreksian['amount'] += result.koreksi

            if contracts.type_id.name == 'HARIAN' :
                obj_bonus = self.env['hr.calendarpayroll']
                obj_payroll = self.env['hr.payslip']
                check_bonus = obj_bonus.search([('date','=',date_to),('minggu','=','2')])
                if check_bonus :
                    day = str(datetime.strptime(date_to,"%Y-%m-%d")-timedelta(days=14))
                    cek_pay = obj_payroll.search([('date_to','=',day),('employee_id','=',contracts.employee_id.id)])
                    xxx = 0
                    yyy = 0
                    for result in cek_pay :
                        for work in result.worked_days_line_ids :
                            if work.code == 'BM1' :
                                if work.number_of_days == 1 :
                                    xxx = 1
                            if work.code == "BM2" :
                                if work.number_of_days == 1 :
                                    yyy = 1
                        if xxx == 1 and yyy == 1 :
                            bonus_bulanan['amount'] = (contracts.wage*10)/100

            res += [simpanan_pokok] + [simpanan_wajib]+ [bpjs_kesehatan] + [bpjs_tenagakerja] + [tunjangan] + [kasbon] + [koreksian]

            if contracts.type_id.name == "BORONGAN" :
                res += [upah_br1] + [upah_br2] + [kerajinan1] + [kerajinan2] + [bns_pot1] + [bns_pot2]
            elif contracts.type_id.name == "HARIAN" :
                res += [bonus_bulanan]


            for contract in contracts:
                for input in inputs:
                    input_data = {
                        'name': input.name,
                        'code': input.code,
                        'contract_id': contract.id,
                    }
                    res += [input_data]
        return res

    #@api.multi
    #def unlink(self):
    #    import pdb;pdb.set_trace()
    #    if any(self.filtered(lambda payslip: payslip.state not in ('draft', 'cancel','done'))):
    #        raise UserError(_('You cannot delete a payslip which is not draft or cancelled and done!'))
    #    return super(HRPayslip, self).unlink()

    @api.multi
    def action_payslip_done(self):
        self.compute_sheet()
        sisa_kuota = 0
        kuota = 0
        kuota2 = 0
        kuotas = self.env['hr.kuota'].search([('employee_id','=',self.employee_id.id),('is_active','=',True)])
        for kuotas in kuotas :
                sisa_kuota = kuotas.sisa_kuota
        for line_ids in self.worked_days_line_ids :
            if line_ids.code == 'kuota1' :
                kuota = line_ids.number_of_days
            if line_ids.code == 'kuota2' :
                kuota2 = line_ids.number_of_days
        sisa = sisa_kuota - kuota - kuota2
        kuotas.write({'sisa_kuota': sisa})

        ### koperasi ###
        check_koperasi = self.env['hr.koperasi'].search([('employee_id','=',self.employee_id.id),('sisa_cicilan','>',0),('state','=','validate'),('mekanisme','=','otomatis')])
        if check_koperasi :
            for result in check_koperasi :
                angsuran = result.angsuran
                sisa = result.sisa_cicilan
                if result.type == 'pokok' :
                    for pokok in result.kasbon_ids:
                        if angsuran - (sisa - 1) == pokok.cicilan:
                            pokok.write({'paid':True,'payslip':self.number,'tanggal_angsuran':self.date_to})
                if result.type == 'wajib' :
                    for wajib in result.kasbon_ids:
                        if angsuran - (sisa - 1) == pokok.cicilan :
                            wajib.write({'paid':True,'payslip':self.number,'tanggal_angsuran':self.date_to})
        return self.write({'state': 'done'})



HRPayslip()

class HRmanual(models.Model):
    _name = "hr.payslip.manual"
    _description = "import manual tunjangan dan potongan"

    name = fields.Date(string="Tanggal Gajian", required="True")
    employee_id = fields.Many2one(comodel_name="hr.employee", string="employee", required=True, track_visibikity="onchange")
    bpjs_kes = fields.Integer(string="BPJS Kesehatan")
    bpjs_ket = fields.Integer(string="BPJS Ketenagakerjaan")
    tunjangan = fields.Integer(string="Tunjangan")
    kasbon = fields.Integer(string="Kasbon")

    ### borongan ###
    status = fields.Boolean('Borongan')
    upah_br1 = fields.Integer('Upah BR Minggu Ke 1')
    upah_br2 = fields.Integer('Upah BR Minggu Ke 2')
    kerajinan1 = fields.Integer('Kerajinan Minggu Ke 1')
    kerajinan2 = fields.Integer('Kerajinan Minggu Ke 2')
    bns_pot1 = fields.Integer('Bonus/Potongan Minggu Ke 1')
    bns_pot2 = fields.Integer('Bonus/Potongan Minggu Ke 2')

class koreksian(models.Model):
    _name = "hr.koreksi"

    name = fields.Date(string='Tanggal Gajian', required="True")
    employee_id = fields.Many2one(comodel_name="hr.employee", string="employee", required=True, track_visibikity="onchange")
    koreksi = fields.Integer('Koreksi')
    state = fields.Selection([('draft','Draft'),('done','Done')],default="draft")

    @api.multi
    def validate(self) :
        return self.write({'state': 'done'})

class Thr(models.Model):
    _name = "hr.thr"

    name = fields.Char(string='Description')
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee")
    tahun = fields.Date('Tanggal THR')
    nik = fields.Char("NIK", related="employee_id.nik", store=True)
    nominal = fields.Integer("Nominal THR")
    state = fields.Selection([('draft','Draft'),('validate','validate'),('pay','Pay')],default="draft")

    @api.multi
    def validate(self) :
        return self.write({'state': 'validate'})

    @api.multi
    def pay(self) :
        return self.write({'state': 'pay'})

class CalendarPayroll(models.Model):
    _name = "hr.calendarpayroll"

    name = fields.Char('Description')
    date = fields.Date('Tanggal Gajian')
    minggu = fields.Selection([('1','Minggu ke -1'),('2','Minggu Ke -2')],string="Minggu Ke")

