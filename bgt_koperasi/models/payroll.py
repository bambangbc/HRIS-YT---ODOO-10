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

from odoo import api, fields, models, tools, _, SUPERUSER_ID


class HRPayslip(models.Model):
    _inherit = "hr.payslip"

    kasbon = fields.Float(string="Potogan Pinjaman")
    length_of_service = fields.Char(string="Length of Service")
    piutang_perusahaan = fields.Float(string="Piutang Perusahaan")

    @api.multi
    def compute_sheet(self):
        for emp in self:
            employee = emp.employee_id.id
            date_from = emp.date_from
            date_to = emp.date_to

            kasbon_amount = 0
            check_cash_receipt = self.env['hr.koperasi'].search([('employee_id','=',employee),
                                                                ('state','=','validate'),
                                                                ('mekanisme','=','otomatis')])
            if check_cash_receipt:
                for result in check_cash_receipt:
                    for kasbon in result.kasbon_ids:
                        if kasbon.tanggal_angsuran >= date_from and kasbon.tanggal_angsuran <= date_to and kasbon.paid == False:
                            kasbon_amount = kasbon.nominal

            emp.write({'kasbon':kasbon_amount})
        return super(HRPayslip, self).compute_sheet()



    @api.multi
    def action_payslip_done(self):
        check_cash_receipt = self.env['hr.koperasi'].search([('employee_id','=',self.employee_id.id),('state','=','validate')])
        total_piutang = 0
        if check_cash_receipt:
            for result in check_cash_receipt:
                for kasbon in result.kasbon_ids:
                    if kasbon.tanggal_angsuran >= self.date_from and kasbon.tanggal_angsuran <= self.date_to and kasbon.paid == False:
                        kasbon.write({'paid':True,'payslip':self.number})

                    #get piutang perusahaan
                    if kasbon.paid == False:
                        total_piutang = total_piutang + kasbon.nominal

                    self.write({'piutang_perusahaan': total_piutang})
        self.compute_sheet()
        return self.write({'state': 'done'})

HRPayslip()