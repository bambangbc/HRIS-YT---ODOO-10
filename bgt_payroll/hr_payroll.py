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

class HRPayslip(models.Model):
    _inherit = "hr.payslip"


    date_from = fields.Date(string='Date From', readonly=True, required=True,
        default=str(datetime.now()+ relativedelta(months=-1, day=26)), states={'draft': [('readonly', False)]})
    date_to = fields.Date(string='Date To', readonly=True, required=True,
         default=time.strftime('%Y-%m-25'),
        states={'draft': [('readonly', False)]})
    net = fields.Float('Net')
    cuti = fields.Float(string="cuti")
    work_cuti = fields.Float(string="work cuti")

    line_ids = fields.One2many('hr.payslip.line', 'slip_id', string='Payslip Lines', readonly=True,
        states={'draft': [('readonly', False)]})

    # net = fields.Float(string="Nett")
    # real_presences = fields.Float(string="real presences", compute="get_real_presences")
    # jurnal_id = fields.Many2one(comodel_name="account.journal", related="employee_id.jurnal_id", store=True, readonly=True)

    # #field untuk keperluar report
    # full_basic_salary = fields.Float(string="Full Basic Salary")
    # basic_salary = fields.Float(string="Basic Salary")
    # t_jabatan = fields.Float(string="Tunjangan Jabatan")
    # t_fungsional = fields.Float(string="Tunjangan Fungsional")
    # t_komunikasi = fields.Float(string="Tunjangan Komunikasi")
    # t_transport = fields.Float(string="Tunjangan Transport")
    # t_makan = fields.Float(string="Uang Makan")
    # t_kost = fields.Float(string="Tunjangan Kost")
    # t_kemahalan = fields.Float(string="Tunjangan Kemahalan")
    # t_luarkota = fields.Float(string="Tunjangan Harian Luar Kota")
    # paket_lembur = fields.Float(string="Paket Lembur")
    # uang_makan_backpay = fields.Float(string="Uang Makan Backpay")
    # iuran_wajib = fields.Float(string="Iuran Wajib")
    # potongan_inhealth = fields.Float(string="Potongan Inhealth")
    # zakat_profesi = fields.Float(string="Zakat Profesi")
    # potongan_unpaid_leave = fields.Float(string="Potongan Unpaid Leave")
    # potongan_uang_makan = fields.Float(string="Potongan Uang Makan")
    # potongan_lainlain = fields.Float(string="Potongan Lain-Lain")
    # piutang_perusahaan = fields.Float(string="Piutang Perusahaan")
    # jaminan_pensiun = fields.Float(string="Jaminan Pensiun Employee")
    # bpjs_employee = fields.Float(string="BPJS K Employee")
    # jht_employee = fields.Float(string="JHT Employee")
    # pph21 = fields.Float(string="PPH 21")
    # total_deduction = fields.Float(string="Total Deduction")
    # take_home_pay = fields.Float(string="Take Home Pay")

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
            payslip.write({'line_ids': lines, 'number': number})
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
        for contract in self.env['hr.contract'].browse(contract_ids):
            attendances = {
                 'name': _("Normal Working Days paid at 100%"),
                 'sequence': 1,
                 'code': 'Work100',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            presences = {
                 'name': _("Presences"),
                 'sequence': 2,
                 'code': 'Presences',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            overtime = {
                 'name': _("Overtime"),
                 'sequence': 3,
                 'code': 'Overtime',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            day_off = {
                 'name': _("day off"),
                 'sequence': 4,
                 'code': 'day_off',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            day_off_absen = {
                 'name': _("day off absen"),
                 'sequence': 5,
                 'code': 'day_off_absen',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            kuota = {
                 'name': _("Kuota Terpakai"),
                 'sequence': 6,
                 'code': 'kuota',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            alpha = {
                 'name': _("Alpha"),
                 'sequence': 6,
                 'code': 'Alpha',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            #import pdb;pdb.set_trace()
            if contract.type_id.name == 'HARIAN' :
                bonus_mingguan = {
                    'name': _("Bonus Mingguan"),
                    'sequence': 7,
                    'code': 'BM',
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
            for day in range(0, nb_of_days):
                #import pdb;pdb.set_trace()
                #menghitung lembur
                #import pdb;pdb.set_trace()
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
                            else :
                                if day <= 7 :
                                    x = 1
                                elif day >= 8 :
                                    y = 1
                                day_off_absen['number_of_hours'] += jumlah
                                day_off_absen['number_of_days'] += 1
                        else:
                            overtime['number_of_hours'] += jumlah
                            if jumlah >= 2.5 :
                                overtime['number_of_days'] += 1

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
                    else:
                        #add the input vals to tmp (increment if existing)
                        attendances['number_of_days'] += 1.0
                        attendances['number_of_hours'] += working_hours_on_day
                        #kehadiran
                        #import pdb;pdb.set_trace()
                        real_working_hours_on_day = self.env['hr.attendance'].real_working_hours_on_day(employee_id, day_from + timedelta(days=day))
                        if real_working_hours_on_day >= 0.000000000000000001 :
                            #import pdb;pdb.set_trace()
                            presences['number_of_days'] += 1.0
                            presences['number_of_hours'] += working_hours_on_day
                        elif sisa_kuota > sisa_kuotas:
                            total_kuotas += 1
                            sisa_kuotas += 1
                        #import pdb;pdb.set_trace()
                        if contract.type_id.name == "HARIAN" and day <= 7 and real_working_hours_on_day <= 0 :
                            if sisa_kuota <= sisa_kuotas :
                                x = 1
                        if contract.type_id.name == "HARIAN" and day >= 8 and day < 14 and real_working_hours_on_day <= 0 :
                            if sisa_kuota <= sisa_kuotas :
                                y = 1
            xy = 2 - x - y
            if contract.type_id.name == 'HARIAN' :
                bonus_mingguan['number_of_days'] = xy
            leaves = [value for key, value in leaves.items()]
            res += [attendances] + leaves + [presences] + [overtime] + [day_off] + [day_off_absen]
            if contract.type_id.name == 'HARIAN' :
                res += [bonus_mingguan]
            #total_quota =
            #if total_kuotas > 0 :
            kuota['number_of_days'] = total_kuotas
            res += [kuota]
            total_alpha = attendances['number_of_days'] - presences['number_of_days'] - kuota['number_of_days']# tanpa_keterangan dianggap alpha
            #if total_alpha > 0 :
            alpha['number_of_days'] = total_alpha
            res += [alpha]
            #self.cuti = ct
            #self.work_cuti = ct + attendances['number_of_days']
        return res

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

            upah_br = {
                     'name': _("Upah Br"),
                     'sequence': 7,
                     'code': 'UPB',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }

            kerajinan = {
                     'name': _("Kerajinan"),
                     'sequence': 8,
                     'code': 'KJN',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }

            bns_pot = {
                     'name': _("Bonus/Potongan"),
                     'sequence': 9,
                     'code': 'BPOT',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }
            koreksian = {
                     'name': _("Koreksian"),
                     'sequence': 10,
                     'code': 'KRS',
                     'amount': 0.0,
                     'contract_id': contracts.id,
                }

            bonus_bulanan = {
                    'name': _("Bonus Bulanan Harian"),
                    'sequence': 9,
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
                    upah_br['amount'] = result.upah_br
                    kerajinan['amount'] = result.kerajinan
                    bns_pot['amount'] = result.bns_pot

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
                    cek_pay = obj_payroll.search([('date_to','=',day),('state','=','done')])
                    for result in cek_pay :
                        for work in result.worked_days_line_ids :
                            if work.code == 'Alpha' :
                                if work.number_of_days == 0 :
                                    bonus_bulanan['amount'] = (contracts.wage*10)/100


            res += [simpanan_pokok] + [simpanan_wajib]+ [bpjs_kesehatan] + [bpjs_tenagakerja] + [tunjangan] + [kasbon] + [koreksian]

            if contracts.type_id.name == "BORONGAN" :
                res += [upah_br] + [kerajinan] + [bns_pot]
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

    @api.multi
    def action_payslip_done(self):
        self.compute_sheet()
        sisa_kuota = 0
        kuota = 0
        kuotas = self.env['hr.kuota'].search([('employee_id','=',self.employee_id.id),('is_active','=',True)])
        for kuotas in kuotas :
                sisa_kuota = kuotas.sisa_kuota
        for line_ids in self.worked_days_line_ids :
            if line_ids.code == 'kuota' :
                kuota = line_ids.number_of_days
        sisa = sisa_kuota - kuota
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
    upah_br = fields.Integer('Upah BR')
    kerajinan = fields.Integer('Kerajinan')
    bns_pot = fields.Integer('Bonus/Potongan')

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

