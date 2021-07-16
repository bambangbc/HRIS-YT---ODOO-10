# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018  Odoo SA  (widianajuniar@gmail.com)
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

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
import math

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


class GenerateReportWizard(models.TransientModel):
    _name = 'report.payroll.wizard'

    name =  fields.Selection([('report_harian', 'Report Harian'),
                              ('report_training', 'Report Training'),
                              ('report_borongan', 'Report Borongan')], default='report_harian',required=True)
    date_start = fields.Date('Date Start',default=fields.Datetime.now, required=True)
    date_end = fields.Date('Date End', default=fields.Datetime.now, required=True )
    file_data = fields.Binary('File', readonly=True)

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))

    @api.multi
    def action_print(self):
        fp = StringIO()
        # create an new excel file and add a worksheet
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet('Report payroll')

        #konten di sini

        merge_format_left = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vleft',
            'fg_color': 'white'
        })
        merge_format_right = workbook.add_format({
            'bold': 0,
            'border': 1,
            'align': 'right',
            'valign': 'right',
            'fg_color': 'white'
        })
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'white'
        })
        merge_format1 = workbook.add_format({
            'bold': 0,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'white'
        })
        merge_format_admin = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'right',
            'valign': 'vright',
            'fg_color': 'DBE5F1'
        })

        worksheet.set_column('A:Q', 20)

        worksheet.write('A1','NAMA',merge_format)
        worksheet.write('B1','UPAH KOTOR',merge_format)
        worksheet.write('C1','KEHADIRAN / 28 HARI (GP)',merge_format)
        worksheet.write('D1','JUMLAH GP',merge_format)
        worksheet.write('E1','KEHADIRAN / 24 HARI (GP)',merge_format)
        worksheet.write('F1','JUMLAH PH',merge_format)
        worksheet.write('G1','KOEFISIEN BONUS MINGGUAN',merge_format)
        worksheet.write('H1','JUMLAH BONUS MINGGUAN',merge_format)
        worksheet.write('I1','KOEFISIEN BONUS BULANAN',merge_format)
        worksheet.write('J1','JUMLAH BONUS BULANAN',merge_format)
        worksheet.write('K1','TOTAL PAYROLL REAL',merge_format_admin)
        worksheet.write('L1','KOEFISIEN LEMBUR',merge_format)
        worksheet.write('M1','JUMLAH LEMBUR',merge_format)
        worksheet.write('N1','TUNJANGAN',merge_format)
        worksheet.write('O1','KOREKSIAN',merge_format)
        worksheet.write('P1','POT UANG MAKAN',merge_format)
        worksheet.write('Q1','BPJS KESEHATAN',merge_format)
        worksheet.write('R1','BPJS KETENAGAKERJAAN',merge_format)
        worksheet.write('S1','SIMPANAN POKOK',merge_format)
        worksheet.write('T1','SIMPANAN WAJIB',merge_format)
        worksheet.write('U1','KASBON',merge_format)
        worksheet.write('V1','TOTAL',merge_format_admin)

        payroll = self.env['hr.payslip'].search([('date_from','=',self.date_start),('date_to','=',self.date_end)])
        row = 1
        for pay in payroll :
            if pay.state != 'cancel' :
                row = row + 1
                C1 = 0
                G1 = 0
                L1 = 0
                D1 = 0
                F1 = 0
                H1 = 0
                J1 = 0
                M1 = 0
                N1 = 0
                O1 = 0
                P1 = 0
                Q1 = 0
                R1 = 0
                S1 = 0
                T1 = 0
                U1 = 0
                V1 = 0

                for code in pay.worked_days_line_ids :
                    if code.code == 'Presences' :
                        C1 = code.number_of_days
                    if code.code == 'BM' :
                        G1 = code.number_of_days
                    if code.code == 'Overtime' :
                        L1 = code.number_of_hours
                for gen in pay.line_ids :
                    if gen.code == 'TGPH' or gen.code == 'TGP' or gen.code == 'TGPT' :
                        D1 = gen.total
                    if gen.code == 'TPHH' or gen.code == 'TPH':
                        F1 = gen.total
                    if gen.code == 'BM' :
                        H1 = gen.total
                    if gen.code == 'BBLH' or gen.code == 'BBL' :
                        J1 = gen.total
                    if gen.code == 'OVTS' or gen.code == 'OVTB' or gen.code == 'OVTT' :
                        M1 = gen.total
                    if gen.code == 'TJ' :
                        N1 = gen.total
                    if gen.code == 'KRSN' :
                        O1 = gen.total
                    if gen.code == 'MEALS' :
                        P1 = gen.total
                    if gen.code == 'BPKES' :
                        Q1 = gen.total
                    if gen.code == 'BPTEN' :
                        R1 = gen.total
                    if gen.code == 'SP' :
                        S1 = gen.total
                    if gen.code == 'SW' :
                        T1 = gen.total
                    if gen.code == 'KAS' :
                        U1 = gen.total
                    if gen.code == 'NET' :
                        V1 = gen.total
                worksheet.write(row,0,pay.employee_id.name,merge_format_left)
                worksheet.write(row,1,int(pay.contract_id.wage),merge_format_right)
                worksheet.write(row,2,int(C1),merge_format1)
                worksheet.write(row,3,int(D1),merge_format_right)
                worksheet.write(row,4,int(C1),merge_format1)
                worksheet.write(row,5,int(F1),merge_format_right)
                worksheet.write(row,6,int(G1),merge_format1)
                worksheet.write(row,7,int(H1),merge_format_right)
                worksheet.write(row,8,'1',merge_format1)
                worksheet.write(row,9,int(J1),merge_format_right)
                worksheet.write(row,10,int(D1)+int(F1)+int(H1)+int(J1),merge_format_admin)
                worksheet.write(row,11,int(L1),merge_format1)
                worksheet.write(row,12,int(M1),merge_format_right)
                worksheet.write(row,13,int(N1),merge_format_right)
                worksheet.write(row,14,int(O1),merge_format_right)
                worksheet.write(row,15,int(P1),merge_format_right)
                worksheet.write(row,16,int(Q1),merge_format_right)
                worksheet.write(row,17,int(R1),merge_format_right)
                worksheet.write(row,18,int(S1),merge_format_right)
                worksheet.write(row,19,int(T1),merge_format_right)
                worksheet.write(row,20,int(U1),merge_format_right)
                worksheet.write(row,21,int(V1),merge_format_admin)
                #worksheet.write(row,21,int(D1)+int(F1)+int(H1)+int(J1)+int(M1)+int(N1)+int(O1)+int(P1)+int(Q1)+int(R1)+int(S1)+int(T1)+int(U1),merge_format_admin)
        #import pdb;pdb.set_trace()
        workbook.close()
        result = base64.encodestring(fp.getvalue())
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        date_start = self.date_start
        date_end = self.date_end
        filename = 'Report payslip %s'%(date_start)+' sampai %s'%(date_end)
        filename += '%2Exlsx'
        self.write({'file_data':result})
        url = "web/content/?model="+self._name+"&id="+str(self.id)+"&field=file_data&download=true&filename="+filename
        return {
            'name': 'Slip Payslip',
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }




GenerateReportWizard()