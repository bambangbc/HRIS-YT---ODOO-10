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


class HRContractType(models.Model):
    _name = 'hr.contract.type'
    _inherit = 'hr.contract.type'

    gaji_pokok = fields.Float("Gaji Pokok (%)")
    premi_hadir = fields.Float("Premi Hadir (%)")
    hari_kerja = fields.Float("Hari Kerja")
    bonus_bulanan = fields.Float("Bonus Bulanan")
    bonus_mingguan = fields.Float("Bonus Mingguan")

HRContractType()


class Contract(models.Model):
    _inherit = "hr.contract"

    def get_expired_contract_days(self):
        for x in self:
            if x.id :
                date_end = x.date_end
                res = 0
                if date_end :
                    date_now = str(fields.date.today())
                    dt_now  = datetime.strptime(date_now, '%Y-%m-%d')
                    dt_end  = datetime.strptime(date_end, '%Y-%m-%d')
                    date    = relativedelta(dt_now,dt_end)
                    year    = date.years
                    month   = date.months
                    day     = date.days

                    res     = -((year*365)+(month*30)+day)
                    x.remaining_expired = res
                    self.env.cr.execute("update hr_contract set remaining_expired_days=%s where id = %s",
                        ( int(res), x.id,))
                else :
                    # jika pegawai tetap injek 1000 hari
                    x.remaining_expired = 1000
                    self.env.cr.execute("update hr_contract set remaining_expired_days=%s where id = %s",
                        ( 1000, x.id,))


    def get_hari(self):
        for x in self:
            my_date = date.today()
            hari = calendar.day_name[my_date.weekday()]
            if hari == 'Sunday':
                hari = 'Minggu'
            elif hari == 'Monday':
                hari = 'Senin'
            elif hari == 'Tuesday':
                hari = 'Selasa'
            elif hari == 'Wednesday':
                hari = 'Rabu'
            elif hari == 'Thursday':
                hari = 'Kamis'
            elif hari == 'Friday':
                hari = 'Jumat'
            elif hari == 'Saturday':
                hari = 'Sabtu'

            bulan = calendar.month_name[my_date.weekday()]
            if bulan == 'January':
                bulan = 'Januari'
            elif bulan == 'February':
                bulan = 'Februari'
            elif bulan == 'March':
                bulan = 'Maret'
            elif bulan == 'April':
                bulan = 'April'
            elif bulan == 'May':
                bulan = 'Mei'
            elif bulan == 'June':
                bulan = 'Juni'
            elif bulan == 'July':
                bulan = 'Juli'
            elif bulan == 'August':
                bulan = 'Agustus'
            elif bulan == 'September':
                bulan = 'September'
            elif bulan == 'October':
                bulan = 'Oktober'
            elif bulan == 'November':
                bulan = 'Nopember'
            elif bulan == 'December':
                bulan = 'Desember'

            x.hari = str(hari)
            x.tanggal = str(my_date)[-2:]+' '+str(bulan)+' '+str(my_date)[:4]

    def get_gapok(self):
        for gp in self:
            wage = gp.wage
            if wage > 0.0 and gp.type_id and gp.type_id.gaji_pokok > 0.0 and gp.type_id.hari_kerja > 0.0 :
                gp.gapok = wage*(gp.type_id.gaji_pokok*0.01)/gp.type_id.hari_kerja

    @api.onchange('wage')
    def wages(self):
        if self.type_id.name == "TRAINING" :
            self.uang_saku = self.wage/24
        if self.type_id.name == "HARIAN" :
            self.premi_hadir = ((20 * self.wage)/100)/28
        elif self.type_id.name == "BULANAN" :
            self.premi_hadir = ((20 * self.wage)/100)/25
        self.upah_bersih = self.wage - self.meals

    @api.onchange('meals')
    def meals(self):
        self.upah_bersih = self.wage - self.meals


    remaining_expired = fields.Float("Expired Contract", compute="get_expired_contract_days")
    remaining_expired_days = fields.Float("Expired Contract Days")# jadikan field biasa agar bisa di search
    hari = fields.Char("Hari")#, compute="get_hari")
    tanggal = fields.Char("Tanggal")#, compute="get_hari")
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.user.company_id)
    no_sk_pengangkatan = fields.Char("No. SK Pengangkatan", size=25)
    no_kesepakatan_upah = fields.Char("No. Kesepakatan Upah", size=25)
    meals = fields.Float("Uang Makan")
    uang_saku = fields.Float("Uang Saku")
    premi_hadir = fields.Float("Premi Hadir")
    uang_transport = fields.Float("Uang Transport")
    bonus_kehadiran = fields.Float("Bonus Kehadiran")
    tunjangan = fields.Float("Tunjangan")
    gapok = fields.Float("Gapok / Hari",compute="get_gapok")
    umk = fields.Float("UMK")
    tmk = fields.Float("TMK")
    upah_bersih = fields.Float("Upah Bersih")

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
        my_date = str(date.today())
        bulan = my_date[5:7]
        sequence = self.env['ir.sequence'].next_by_code('hr.mutasi') or 'Number not found !'
        if sequence != 'Number not found !' :
            awal = sequence[:12]
            akhir = sequence[-4:]
            romawi = self.write_roman(int(bulan))

            vals['no_kesepakatan_upah'] = str(awal)+str(romawi)+'/'+str(akhir)

        return super(Contract, self).create(vals)

    # Cron
    def update_contract_state(self):
        contract = self.env['hr.contract']
        date_now = str(fields.date.today())
        now  = datetime.strptime(date_now, '%Y-%m-%d')
        # cek yang harus running
        must_running = contract.sudo().search([('date_start','=',str(now)),('state','!=','open')])
        for run in must_running :
            run.write({'state'  : 'open'})
            run.employee_id.write({'department_id'  : run.department_id.id,
                                    'job_id'        : run.job_id.id})
            message = "Contract "+ run.name + " Change status to running.. "
            print message
        kemarin = now - timedelta(days=1)
        must_closed = contract.sudo().search([('date_end','=',str(kemarin)),('state','!=','close')])
        for close in must_closed :
            close.write({'state'  : 'close'})
            message = "Contract "+ close.name + " Change status to close.. "
            print message
        tigabulanlagi = now + timedelta(days=90)
        must_renew = contract.sudo().search([('date_end','<=',str(tigabulanlagi)),
                                                ('date_end','>',str(now)),
                                                ('state','!=','pending')])
        for renew in must_renew :
            renew.write({'state'  : 'pending'})
            message = "Contract "+ renew.name + " Change status to renew.. "
            print message

        return True


Contract()