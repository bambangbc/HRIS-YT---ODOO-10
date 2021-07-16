# -*- coding: utf-8 -*-
# @Author: xrix
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from openerp import models, fields, api
from openerp.exceptions import except_orm

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


dic = {       
    'to_19' : ('Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'),
    'tens'  : ('Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'),
    'denom' : ('', 'Thousand', 'Million', 'Billion', 'Trillion', 'Quadrillion', 'Quintillion'),        
    'to_19_id' : ('NOL', 'SATU', 'DUA', 'TIGA', 'EMPAT', 'LIMA', 'ENAM', 'TUJUH', 'DELAPAN', 'SEMBILAN', 'SEPULUH', 'SEBELAS', 'DUA BELAS', 'TIGA BELAS', 'EMPAT BELAS', 'LIMA BELAS', 'ENAM BELAS', 'TUJUH BELAS', 'DELAPAN BELAS', 'SEMBILAN BELAS'),
    'tens_id'  : ('DUA PULUH', 'TIGA PULUH', 'EMPAT PULUH', 'LIMA PULUH', 'ENAM PULUH', 'TUJUH PULUH', 'DELAPAN PULUH', 'SEMBILAN PULUH'),
    'denom_id' : ('', 'RIBU', 'JUTA', 'MILIAR', 'TRILIUN', 'BILIUN')
}
 
def terbilang(number, currency, bhs):
    number = '%.2f' % number
    units_name = ' ' + cur_name(currency) + ' '
    lis = str(number).split('.')
    start_word = english_number(int(lis[0]), bhs)
    end_word = english_number(int(lis[1]), bhs)
    cents_number = int(lis[1])
    cents_name = (cents_number > 1) and 'Sen' or 'sen'
    final_result_sen = start_word + units_name + end_word +' '+cents_name
    final_result = start_word + units_name
    if end_word == 'NOL' or end_word == 'ZERO':
        final_result = final_result
    else:
        final_result = final_result_sen
     
    return final_result[:1].upper()+final_result[1:]
 
def _convert_nn(val, bhs):
    tens = dic['tens_id']
    to_19 = dic['to_19_id']
    if bhs == 'en':
        tens = dic['tens']
        to_19 = dic['to_19']
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                return dcap + ' ' + to_19[val % 10]
            return dcap
 
def _convert_nnn(val, bhs):
    word = ''; rat = ' RATUS'; to_19 = dic['to_19_id']
    if bhs == 'en':
        rat = ' Hundred'
        to_19 = dic['to_19']
    (mod, rem) = (val % 100, val // 100)
    if rem == 1:
        word = 'Seratus'
        if mod > 0:
            word = word + ' '   
    elif rem > 1:
        word = to_19[rem] + rat
        if mod > 0:
            word = word + ' '
    if mod > 0:
        word = word + _convert_nn(mod, bhs)
    return word
 
def english_number(val, bhs):
    denom = dic['denom_id']
    if bhs == 'en':
        denom = dic['denom']
    if val < 100:
        return _convert_nn(val, bhs)
    if val < 1000:
        return _convert_nnn(val, bhs)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn(l, bhs) + ' ' + denom[didx]
            if r > 0:
                ret = ret + ' ' + english_number(r, bhs)
            if bhs == 'id':
                if val < 2000:
                    ret = ret.replace("SATU RIBU", "SERIBU")
            return ret
 
def cur_name(cur="idr"):
    cur = cur.lower()
    if cur=="usd":
        return "Dollars"
    elif cur=="aud":
        return "Dollars"
    elif cur=="idr":
        return "RUPIAH"
    elif cur=="jpy":
        return "Yen"
    elif cur=="sgd":
        return "Dollars"
    elif cur=="usd":
        return "Dollars"
    elif cur=="eur":
        return "Euro"
    else:
        return cur


class purchaseConfirmWizard(models.TransientModel):
    _name = 'slip.payroll'

    warning = fields.Char(readonly=True)
    file_data = fields.Binary('File', readonly=True)

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))

    @api.multi
    def download_slip(self):
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet('Report Payroll')
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:D', 3)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 3)
        worksheet.set_column('G:G', 17)
        worksheet.set_column('H:H', 3)

        worksheet.set_column('I:I', 12)
        worksheet.set_column('J:K', 3)
        worksheet.set_column('M:M', 12)
        worksheet.set_column('N:N', 3)
        worksheet.set_column('O:O', 17)
        worksheet.set_column('P:P', 3)

        worksheet.set_column('Q:Q', 12)
        worksheet.set_column('R:T', 3)
        worksheet.set_column('U:U', 12)
        worksheet.set_column('V:V', 3)
        worksheet.set_column('W:W', 17)
        worksheet.set_column('X:X', 3)

        worksheet.set_column('Y:Y', 12)
        worksheet.set_column('Z:AB', 3)
        worksheet.set_column('AC:AC', 12)
        worksheet.set_column('AD:AD', 3)
        worksheet.set_column('AE:AE', 17)
        worksheet.set_column('AF:AF', 3)

        #konten di sini
        active_ids = self._context.get('active_ids')
        desain_ids = self.env['hr.payslip'].browse(active_ids)
        brand_ids = desain_ids.mapped('name')

        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'white'
        })
        merge_format.set_font_color('red')
        title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'valign': 'vcenter',
        })
        left_format = workbook.add_format({
            'bold': 0,
            'border' : 1,
            'valign' : 'vleft',
        })
        left2_format = workbook.add_format({
            'bold': 0,
            'border' : 0,
            'valign' : 'vleft',
        })
        center_format = workbook.add_format({
            'bold': 0,
            'border' : 0,
            'align' : 'center',
            'valign' : 'vcenter',
        })
        center1_format = workbook.add_format({
            'bold': 1,
            'border' : 0,
            'align' : 'center',
            'valign' : 'vcenter',
        })
        title_format.set_text_wrap()
        right_format = workbook.add_format({
            'bold' : 0,
            'border': 0,
            'align' : 'right',
            'valign': 'vright',
        })
        right1_format = workbook.add_format({
            'bold' : 1,
            'border': 0,
            'align' : 'right',
            'valign': 'vright',
        })
        left_format_top = workbook.add_format({
            'bold': 0,
            'top' : 1,
            'valign' : 'vleft',
        })
        right_format_top = workbook.add_format({
            'bold': 0,
            'top' : 1,
            'valign' : 'vright',
        })
        center_format_top = workbook.add_format({
            'bold': 0,
            'top' : 1,
            'valign' : 'vcenter',
        })


        row = 1
        #for brand_id in brand_ids :
        merge_from = row
        merge_to = row+1
        row += 2
        worksheet.merge_range('A%s:AB%s'%(merge_from,merge_to), 'Payroll', title_format)
        #desain_brand_ids = desain_ids.filtered(lambda desain: desain.brand_id.id == brand_id.id)
        desain_brand_ids = desain_ids
        while desain_brand_ids :
            five_desain_ids = desain_brand_ids[0:4]
            col = {1:['A','B','C','D','E','F','G','H'], 2:['I','J','K','L','M','N','O','P'], 3:['Q','R','S','T','U','V','W','X'], 4:['Y','Z','AA','AB','AC','AD','AE','AF']}
            col_range = 1
            row += 1
            x = 0
            jum = len(five_desain_ids)
            for desain in five_desain_ids :
                one_letter = col[col_range][0]
                two_letter = col[col_range][1]
                tree_letter = col[col_range][2]
                four_letter = col[col_range][3]
                five_letter = col[col_range][4]
                six_letter = col[col_range][5]
                seven_letter = col[col_range][6]
                eeg_letter = col[col_range][7]
                presences1 = 0
                presences2 = 0
                overtime1 = 0
                overtime2 = 0
                day_off1 = 0
                day_off2 = 0
                day_off_absen1 = 0
                day_off_absen2 = 0
                kuota1 = 0
                kuota2 = 0
                alpha1 = 0 
                alpha2 = 0
                BM1 = 0 
                BM2 = 0
                #import pdb;pdb.set_trace()
                if desain.contract_id.type_id.name == "HARIAN" :
                    for line in desain.worked_days_line_ids :
                        if line.code == 'Presences1' :
                            presences1 = line.number_of_days
                        elif line.code == 'Presences2' :
                            presences2 = line.number_of_days
                        elif line.code == 'Overtime1' :
                            overtime1 = line.number_of_hours
                        elif line.code == 'Overtime2' :
                            overtime2 = line.number_of_hours
                        elif line.code == 'day_off1' :
                            day_off1 = line.number_of_days
                        elif line.code == 'day_off2' :
                            day_off2 = line.number_of_days
                        elif line.code == 'day_off_absen1' :
                            day_off_absen2 = line.number_of_days
                        elif line.code == 'kuota1' :
                            kuota1 = line.number_of_days
                        elif line.code == 'kuota2' :
                            kuota2 = line.number_of_days
                        elif line.code == 'Alpha1' :
                            alpha1 = line.number_of_days
                        elif line.code == 'Alpha2' :
                            alpha2 = line.number_of_days
                        elif line.code == 'BM1' :
                            BM1 = line.number_of_days
                        elif line.code == 'BM2' :
                            BM2 = line.number_of_days
                    pres1 = presences1 + 1 + day_off1
                    pres2 = presences2 + 1 + day_off2 
                    premi1 = presences1 + day_off1
                    premi2 = presences2 + day_off2
                    umak = presences1 + presences2 + day_off1 + day_off2
                    TGPH1 = 0
                    TGPH2 = 0
                    TPHH1 = 0
                    TPHH2 = 0
                    BM1 = 0
                    BM2 = 0
                    BBLH = 0
                    OVM1 = 0
                    OVM2 = 0
                    meals1 = 0
                    SP = 0
                    SW = 0
                    KAS = 0
                    KRSN = 0
                    NET = 0
                    for nominal in desain.line_ids :
                        if nominal.code == 'TGPH1' :
                            TGPH1 = nominal.amount
                        elif nominal.code == 'TGPH2' :
                            TGPH2 = nominal.amount
                        elif nominal.code == 'TPHH1' :
                            TPHH1 = nominal.amount
                        elif nominal.code == 'TPHH2' :
                            TPHH2 = nominal.amount
                        elif nominal.code == 'BM1' :
                            BM1 = nominal.amount
                        elif nominal.code == 'BM2' :
                            BM2 = nominal.amount
                        elif nominal.code == 'BBLH' :
                            BBLH = nominal.amount
                        elif nominal.code == 'OVM1' :
                            OVM1 = nominal.amount
                        elif nominal.code == 'OVM2' :
                            OVM2 = nominal.amount
                        elif nominal.code == 'MEALS1' :
                            meals1 = nominal.amount
                        elif nominal.code == 'SP' :
                            SP = nominal.amount
                        elif nominal.code == 'SW' :
                            SW = nominal.amount
                        elif nominal.code == 'KAS' :
                            KAS = nominal.amount
                        elif nominal.code == 'KRSN' :
                            KRSN = nominal.amount
                        elif nominal.code == 'NET' :
                            NET = nominal.amount
                    if desain.contract_id.wage > desain.contract_id.umk :
                        ovrt = int(desain.contract_id.umk/56/4*1.5)
                    else :
                        ovrt = int(desain.contract_id.wage/56/4*1.5)
                    #import pdb;pdb.set_trace()
                    bulan = ["","Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]
                    tanggal = desain.date_to[8:10] + "-" + bulan[int(desain.date_to[5:7])] + "-" + desain.date_to[:4]
                    worksheet.write('%s%s'%(one_letter,row), 'NAMA', workbook.add_format({'bold': 0,'top' : 1,'left': 1,'valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(two_letter,row,five_letter,row),desain.employee_id.name,left_format_top)
                    worksheet.write('%s%s'%(six_letter,row), "", center_format_top)
                    worksheet.write('%s%s'%(seven_letter,row),tanggal,workbook.add_format({'bold': 0,'align':'right','top': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row),'',workbook.add_format({'bold': 0,'top': 1,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+1), 'NIK', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(two_letter,row+1,five_letter,row+1),desain.employee_id.nik,left2_format)
                    worksheet.write('%s%s'%(seven_letter,row+1),desain.employee_id.bank_account_id.bank_id.name,workbook.add_format({'bold': 0,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+1),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+2), 'DIV', workbook.add_format({'bold': 0,'bottom': 1,'left': 1,'valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(two_letter,row+2,five_letter,row+2),desain.employee_id.department_id.name,workbook.add_format({'bold': 0,'bottom' : 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(four_letter,row+2), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+2), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(six_letter,row+2), "", workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+2), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+2),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vleft'}))
                    
                    worksheet.write('%s%s'%(one_letter,row+3), 'G POKOK', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+4), '', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+3), '1', center_format)
                    worksheet.write('%s%s'%(two_letter,row+4), '2', center_format)
                    worksheet.write('%s%s'%(tree_letter,row+3), presences1+1, center_format)
                    worksheet.write('%s%s'%(tree_letter,row+4), presences2+1, center_format)
                    worksheet.write('%s%s'%(four_letter,row+3), 'x', center_format)
                    worksheet.write('%s%s'%(four_letter,row+4), 'x', center_format)
                    worksheet.write('%s%s'%(five_letter,row+3), round((desain.contract_id.wage*0.65)/28), workbook.add_format({'num_format': '#,##0', 'valign':'right'}))
                    worksheet.write('%s%s'%(five_letter,row+4), round((desain.contract_id.wage*0.65)/28), workbook.add_format({'num_format': '#,##0', 'valign':'right'}))
                    worksheet.write('%s%s'%(six_letter,row+3), "'=", center_format)
                    worksheet.write('%s%s'%(six_letter,row+4), "'=", center_format)
                    worksheet.write('%s%s'%(seven_letter,row+3), round(TGPH1), workbook.add_format({'bold': 0,'valign' : 'vright','num_format': '#,##0'}))
                    worksheet.write('%s%s'%(seven_letter,row+4), round(TGPH2), workbook.add_format({'bold': 0,'valign' : 'vright','num_format': '#,##0'}))
                    worksheet.write('%s%s'%(eeg_letter,row+3),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+4),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    
                    worksheet.write('%s%s'%(one_letter,row+5), 'PREMI', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+6), '', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+5), '1', center_format)
                    worksheet.write('%s%s'%(two_letter,row+6), '2', center_format)
                    worksheet.write('%s%s'%(tree_letter,row+5), premi1, center_format)
                    worksheet.write('%s%s'%(tree_letter,row+6), premi2, center_format)
                    worksheet.write('%s%s'%(four_letter,row+5), 'x', center_format)
                    worksheet.write('%s%s'%(four_letter,row+6), 'x', center_format)
                    worksheet.write('%s%s'%(five_letter,row+5), round(desain.contract_id.wage*0.2/24), workbook.add_format({'num_format': '#,##0', 'valign':'right'}))
                    worksheet.write('%s%s'%(five_letter,row+6), round(desain.contract_id.wage*0.2/24), workbook.add_format({'num_format': '#,##0', 'valign':'right'}))
                    worksheet.write('%s%s'%(six_letter,row+5), "'=", center_format)
                    worksheet.write('%s%s'%(six_letter,row+6), "'=", center_format)
                    worksheet.write('%s%s'%(seven_letter,row+5), round(TPHH1), workbook.add_format({'bold': 0,'valign' : 'vright','num_format': '#,##0'}))
                    worksheet.write('%s%s'%(seven_letter,row+6), round(TPHH2), workbook.add_format({'bold': 0,'valign' : 'vright','num_format': '#,##0'}))
                    worksheet.write('%s%s'%(eeg_letter,row+5),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+6),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+7), 'BNS MG', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+8), '', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+7), '1', center_format)
                    worksheet.write('%s%s'%(two_letter,row+8), '2', center_format)
                    worksheet.write('%s%s'%(seven_letter,row+7), round(BM1), workbook.add_format({'num_format': '#,##0','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(seven_letter,row+8), round(BM2), workbook.add_format({'num_format': '#,##0','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+7),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+8),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+9),'BNS BLN',workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+9),round(BBLH), workbook.add_format({'num_format': '#,##0','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+9),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+10), 'U LMBR', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+11), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+10), '1', center_format)
                    worksheet.write('%s%s'%(two_letter,row+11), '2', workbook.add_format({'bold': 0,'bottom': 1,'align' : 'center','valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(tree_letter,row+10), overtime1, center_format)
                    worksheet.write('%s%s'%(tree_letter,row+11), overtime2, workbook.add_format({'bold': 0,'bottom': 1,'align' : 'center','valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(four_letter,row+10), 'x', center_format)
                    worksheet.write('%s%s'%(four_letter,row+11), 'x', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'center'}))
                    worksheet.write('%s%s'%(five_letter,row+10), ovrt, workbook.add_format({'num_format': '#,##0', 'valign':'right'}))
                    worksheet.write('%s%s'%(five_letter,row+11), ovrt, workbook.add_format({'num_format': '#,##0','bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(six_letter,row+10), "'=", center_format)
                    worksheet.write('%s%s'%(six_letter,row+11), "'=", workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(seven_letter,row+10), round(OVM1), workbook.add_format({'num_format': '#,##0','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(seven_letter,row+11), round(OVM2), workbook.add_format({'num_format': '#,##0','bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+10),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+11),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(seven_letter,row+12), round(TGPH1 + TGPH2 + TPHH1 + TPHH2 + BM1 + BM2 + BBLH + OVM1 + OVM2) ,workbook.add_format({'num_format': '#,##0', 'valign':'right'}))
                    worksheet.write('%s%s'%(one_letter,row+12),'',workbook.add_format({'bold': 0,'left': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+12),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+13),'U MKN',workbook.add_format({'bold': 0,'bottom': 1,'left': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+13), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(tree_letter,row+13),umak,workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(four_letter,row+13),'x',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(five_letter,row+13),desain.contract_id.meals,workbook.add_format({'bold': 0,'bottom': 1,'align' : 'center','valign' : 'vright'}))
                    worksheet.write('%s%s'%(six_letter,row+13),"'=",workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(seven_letter,row+13),round(meals1),workbook.add_format({'num_format': '#,##0','bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+13),'+',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    col_range += 1

                    worksheet.write('%s%s'%(seven_letter,row+14),round(TGPH1 + TGPH2 + TPHH1 + TPHH2 + BM1 + BM2 + BBLH + OVM1 + OVM2 + meals1),right_format)
                    worksheet.write('%s%s'%(one_letter,row+14),'',workbook.add_format({'bold': 0,'left': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+14),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+15),'S POKOK',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+15),SP,workbook.add_format({'num_format': '#,##0', 'valign':'right'}))
                    worksheet.write('%s%s'%(eeg_letter,row+15),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+16),'S WAJIB',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+16),SW,workbook.add_format({'num_format': '#,##0', 'valign':'right'}))
                    worksheet.write('%s%s'%(eeg_letter,row+16),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+17),'KB KAS',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+17),KAS,workbook.add_format({'num_format': '#,##0', 'valign':'right'}))
                    worksheet.write('%s%s'%(eeg_letter,row+17),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+18),'KOREKSI',workbook.add_format({'bold': 0,'left': 1,'align': 'left','bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+18), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(tree_letter,row+18),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(four_letter,row+18),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(five_letter,row+18),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(six_letter,row+18),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(seven_letter,row+18),KRSN,workbook.add_format({'num_format': '#,##0', 'bottom':1, 'valign':'right'}))
                    worksheet.write('%s%s'%(eeg_letter,row+18),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+19),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+19),'TOTAL',center1_format)
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+19,seven_letter,row+19),round(TGPH1 + TGPH2 + TPHH1 + TPHH2 + BM1 + BM2 + BBLH + OVM1 + OVM2 + meals1 + SP + SW + KAS + KRSN),workbook.add_format({'num_format': '#,##0', 'valign':'right'}))
                    worksheet.write('%s%s'%(eeg_letter,row+19),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+20),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+20),'REAL',workbook.add_format({'bold': 0,'bottom': 1,'font_size':15,'bold':1,'align': 'center','valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+20,seven_letter,row+20),NET,workbook.add_format({'num_format': '#,##0','bold': 0,'bottom': 1,'font_size':15,'bold':1,'align': 'right','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+20),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+21),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+21),desain.employee_id.bank_account_id.bank_id.name,workbook.add_format({'bold': 0,'font_size':15,'bold':1,'align': 'center','valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+21,seven_letter,row+21),NET,workbook.add_format({'num_format': '#,##0','font_size':15,'bold':1,'align': 'right','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+21),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+22),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+22),'CASH',workbook.add_format({'bold': 0,'font_size':15,'bold':1,'align': 'center','valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+22,seven_letter,row+22),'-',workbook.add_format({'num_format': '#,##0','bold': 0,'font_size':15,'bold':1,'align': 'right','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+22),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+23),'',workbook.add_format({'bold': 0,'left': 1,'bottom': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+23),'TOTAL',workbook.add_format({'bold': 1,'align': 'center','valign' : 'vright'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+23,seven_letter,row+23),NET,workbook.add_format({'num_format': '#,##0','bold': 0,'right': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+23),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+23), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(tree_letter,row+23),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(four_letter,row+23),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(six_letter,row+23),NET,workbook.add_format({'num_format': '#,##0','bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(seven_letter,row+23),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    NETS = terbilang(NET, 'idr', 'idr')
                    worksheet.merge_range('%s%s:%s%s'%(one_letter,row+24,eeg_letter,row+25),NETS,workbook.add_format({'bold': 1,'border': 1,'align':'center','valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+26),'Payroll',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+26), '', workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))
                    worksheet.merge_range('%s%s:%s%s'%(tree_letter,row+26,four_letter,row+26),'Finance',workbook.add_format({'bold': 0,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(five_letter,row+26),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vcenter'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+26,seven_letter,row+26),'Checker',workbook.add_format({'bold': 0,'align':'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+26),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+27),'',workbook.add_format({'bold': 0,'bottom': 1,'left': 1,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+27), '', workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    worksheet.merge_range('%s%s:%s%s'%(tree_letter,row+27,four_letter,row+27),'',workbook.add_format({'bold': 0,'align': 'left','bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(five_letter,row+27),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vcenter'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+27,seven_letter,row+27),'',workbook.add_format({'bold': 0,'bottom': 1,'align':'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+27),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    
                    x +=1
                    if x == jum :
                        row += 28
                        desain_brand_ids -= five_desain_ids
                
                elif desain.contract_id.type_id.name == "TRAINING" :
                    presences1 = 0
                    presences2 = 0
                    overtime1 = 0
                    overtime2 = 0
                    umak    = 0
                    ov1 = 0
                    ov2 = 0
                    SP = 0
                    SW = 0
                    KAS = 0
                    KRSN = 0
                    NET = 0
                    for line in desain.worked_days_line_ids :
                        if line.code == 'Presences1' :
                            presences1 = line.number_of_days
                        elif line.code == 'Presences2' :
                            presences2 = line.number_of_days
                        elif line.code == 'Overtime1' :
                            overtime1 = line.number_of_hours
                            if desain.contract_id.wage > desain.contract_id.umk :
                                ov1 = int(overtime1 * (desain.contract_id.umk/56/4*1.5))
                            else : 
                                ov1 = int(overtime1 * (desain.contract_id.wage/56/4*1.5))
                        elif line.code == 'Overtime2' :
                            overtime2 = line.number_of_hours
                            if desain.contract_id.wage > desain.contract_id.umk :
                                ov2 = int(overtime2 * (desain.contract_id.umk/56/4*1.5)) 
                            else : 
                                ov2 = int(overtime2 * (desain.contract_id.wage/56/4*1.5))

                    for nominal in desain.line_ids :
                        if nominal.code == 'SP' :
                            SP = nominal.amount
                        elif nominal.code == 'SW' :
                            SW = nominal.amount
                        elif nominal.code == 'KAS' :
                            KAS = nominal.amount
                        elif nominal.code == 'KRSN' :
                            KRSN = nominal.amount
                        elif nominal.code == 'NET' :
                            NET = nominal.amount
                    bulan = ["","Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]
                    tanggal = desain.date_to[8:10] + "-" + bulan[int(desain.date_to[5:7])] + "-" + desain.date_to[:4]
                    worksheet.write('%s%s'%(one_letter,row), 'NAMA', workbook.add_format({'bold': 0,'top' : 1,'left': 1,'valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(two_letter,row,five_letter,row),desain.employee_id.name,left_format_top)
                    worksheet.write('%s%s'%(six_letter,row), "", center_format_top)
                    worksheet.write('%s%s'%(seven_letter,row),tanggal,workbook.add_format({'bold': 0,'align':'right','top': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row),'',workbook.add_format({'bold': 0,'top': 1,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+1), 'NIK', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(two_letter,row+1,five_letter,row+1),desain.employee_id.nik,left2_format)
                    worksheet.write('%s%s'%(seven_letter,row+1),desain.employee_id.bank_account_id.bank_id.name,workbook.add_format({'bold': 0,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+1),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+2), 'DIV', workbook.add_format({'bold': 0,'bottom': 1,'left': 1,'valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(two_letter,row+2,five_letter,row+2),desain.employee_id.department_id.name,workbook.add_format({'bold': 0,'bottom' : 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(four_letter,row+2), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+2), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(six_letter,row+2), "", workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+2), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+2),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vleft'}))
                    
                    worksheet.write('%s%s'%(one_letter,row+3), 'U SAKU', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+4), '', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+3), '1', center_format)
                    worksheet.write('%s%s'%(two_letter,row+4), '2', center_format)
                    worksheet.write('%s%s'%(tree_letter,row+3), presences1+1, center_format)
                    worksheet.write('%s%s'%(tree_letter,row+4), presences2+1, center_format)
                    worksheet.write('%s%s'%(four_letter,row+3), 'x', center_format)
                    worksheet.write('%s%s'%(four_letter,row+4), 'x', center_format)
                    worksheet.write('%s%s'%(five_letter,row+3), round(desain.contract_id.wage/24), workbook.add_format({'num_format': '#,##0','right':1}))
                    worksheet.write('%s%s'%(five_letter,row+4), round(desain.contract_id.wage/24), workbook.add_format({'num_format': '#,##0','right':1}))
                    worksheet.write('%s%s'%(six_letter,row+3), "'=", center_format)
                    worksheet.write('%s%s'%(six_letter,row+4), "'=", center_format)
                    worksheet.write('%s%s'%(seven_letter,row+3), round((desain.contract_id.wage/24)*presences1), workbook.add_format({'num_format': '#,##0','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(seven_letter,row+4), round((desain.contract_id.wage/24)*presences2), workbook.add_format({'num_format': '#,##0','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+3),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+4),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    
                    worksheet.write('%s%s'%(one_letter,row+5), 'U LEMBUR', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+6), '', workbook.add_format({'bold': 0,'left': 1,'bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+5), '1', center_format)
                    worksheet.write('%s%s'%(two_letter,row+6), '2', workbook.add_format({'bold': 0,'bottom':1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(tree_letter,row+5), overtime1, workbook.add_format({'num_format': '#,##0','right':1}))
                    worksheet.write('%s%s'%(tree_letter,row+6), overtime2, workbook.add_format({'num_format': '#,##0','bold': 0,'align' : 'center','bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(four_letter,row+5), 'x', center_format)
                    worksheet.write('%s%s'%(four_letter,row+6), 'x', workbook.add_format({'bold': 0,'align' : 'center','bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+5), round(desain.contract_id.wage*0.65/24), workbook.add_format({'num_format': '#,##0','right':1}))
                    worksheet.write('%s%s'%(five_letter,row+6), round(desain.contract_id.wage*0.65/24), workbook.add_format({'num_format': '#,##0','bold': 0,'bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(six_letter,row+5), "'=", center_format)
                    worksheet.write('%s%s'%(six_letter,row+6), "'=", workbook.add_format({'bold': 0,'align' : 'center','bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+5), ov1, workbook.add_format({'num_format': '#,##0','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(seven_letter,row+6), ov2, workbook.add_format({'num_format': '#,##0','bold': 0,'bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+5),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+6),'',workbook.add_format({'bold': 0,'right': 1,'bottom':1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(seven_letter,row+7), round(((desain.contract_id.wage/24)*presences1) + ((desain.contract_id.wage/24)*presences2) + ov1 + ov2), workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(one_letter,row+7),'',workbook.add_format({'bold': 0,'left': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+7),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+8),'U MKN',workbook.add_format({'bold': 0,'bottom': 1,'left': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+8), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(tree_letter,row+8),"",workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(four_letter,row+8),'x',workbook.add_format({'bold': 0,'align' : 'center','bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(five_letter,row+8),desain.contract_id.meals,workbook.add_format({'bold': 0,'bottom': 1,'align' : 'center','valign' : 'vright'}))
                    worksheet.write('%s%s'%(six_letter,row+8),"'=",workbook.add_format({'bold': 0,'align' : 'center','bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(seven_letter,row+8),desain.contract_id.meals*(presences1+presences2),workbook.add_format({'num_format': '#,##0','bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+8),'+',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    col_range += 1

                    worksheet.write('%s%s'%(seven_letter,row+9),round(((desain.contract_id.wage/24)*presences1) + ((desain.contract_id.wage/24)*presences2) + ov1 + ov2 - (desain.contract_id.meals*(presences1+presences2))), workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(one_letter,row+9),'',workbook.add_format({'bold': 0,'left': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+9),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+10),'S POKOK',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+10),SP,workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+10),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+11),'S WAJIB',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+11),SW,workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+11),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+12),'KB KAS',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+12),KAS,workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+12),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+13),'KOREKSI',workbook.add_format({'bold': 0,'left': 1,'align': 'left','bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+13),KRSN,workbook.add_format({'num_format': '#,##0','bottom':1,'valign':'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+13),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+13), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(tree_letter,row+13),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(four_letter,row+13),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(five_letter,row+13),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(six_letter,row+13),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    #worksheet.write('%s%s'%(seven_letter,row+13),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+14),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+14),'TOTAL',center1_format)
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+14,seven_letter,row+14),round(((desain.contract_id.wage/24)*presences1) + ((desain.contract_id.wage/24)*presences2) + ov1 + ov2 - (desain.contract_id.meals*(presences1+presences2)) + SP + SW + KAS + KRSN),workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+14),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+15),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+15),'REAL',workbook.add_format({'bold': 0,'bottom': 1,'font_size':15,'bold':1,'align': 'center','valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+15,seven_letter,row+15),NET,workbook.add_format({'num_format': '#,##0','bold': 0,'bottom': 1,'font_size':15,'bold':1,'align': 'right','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+15),'',workbook.add_format({'bold': 0,'right':1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+16),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+16),desain.employee_id.bank_account_id.bank_id.name,workbook.add_format({'bold': 0,'font_size':15,'bold':1,'align': 'center','valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+16,seven_letter,row+16),NET,workbook.add_format({'num_format': '#,##0','bold': 0,'font_size':15,'bold':1,'align': 'right','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+16),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+17),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+17),'CASH',center1_format)
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+17,seven_letter,row+17),'-',workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+17),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+18),'',workbook.add_format({'bold': 0,'left': 1,'bottom': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+18),'TOTAL',workbook.add_format({'bold': 1,'bottom': 1,'align': 'center','valign' : 'vright'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+18,seven_letter,row+18),NET,workbook.add_format({'num_format': '#,##0','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+18),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+18), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(tree_letter,row+18),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(four_letter,row+18),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    #worksheet.write('%s%s'%(six_letter,row+18),NET,workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    #worksheet.write('%s%s'%(seven_letter,row+18),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    NETS = terbilang(NET, 'idr', 'idr')
                    worksheet.merge_range('%s%s:%s%s'%(one_letter,row+19,eeg_letter,row+20),NETS,workbook.add_format({'bold': 1,'border': 1,'align':'center','valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+21),'Payroll',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+21), '', workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))
                    worksheet.merge_range('%s%s:%s%s'%(tree_letter,row+21,four_letter,row+21),'Finance',workbook.add_format({'bold': 0,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(five_letter,row+21),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vcenter'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+21,seven_letter,row+21),'Checker',workbook.add_format({'bold': 0,'align':'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+21),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+22),'',workbook.add_format({'bold': 0,'bottom': 1,'left': 1,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+22), '', workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    worksheet.merge_range('%s%s:%s%s'%(tree_letter,row+22,four_letter,row+22),'',workbook.add_format({'bold': 0,'align': 'left','bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(five_letter,row+22),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vcenter'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+22,seven_letter,row+22),'',workbook.add_format({'bold': 0,'bottom': 1,'align':'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+22),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    
                    x +=1
                    if x == jum :
                        row += 23
                        desain_brand_ids -= five_desain_ids
                
                elif desain.contract_id.type_id.name == "BULANAN" or desain.contract_id.type_id.name == "STAFF" :
                    
                    worksheet.set_column('A:A', 12)
                    worksheet.set_column('B:D', 3)
                    worksheet.set_column('E:E', 12)
                    worksheet.set_column('F:F', 3)
                    worksheet.set_column('G:G', 17)
                    worksheet.set_column('H:H', 3)

                    worksheet.set_column('I:I', 12)
                    worksheet.set_column('J:K', 3)
                    worksheet.set_column('M:M', 12)
                    worksheet.set_column('N:N', 3)
                    worksheet.set_column('O:O', 17)
                    worksheet.set_column('P:P', 3)

                    worksheet.set_column('Q:Q', 12)
                    worksheet.set_column('R:T', 3)
                    worksheet.set_column('U:U', 12)
                    worksheet.set_column('V:V', 3)
                    worksheet.set_column('W:W', 17)
                    worksheet.set_column('X:X', 3)

                    worksheet.set_column('Y:Y', 12)
                    worksheet.set_column('Z:AB', 3)
                    worksheet.set_column('AC:AC', 12)
                    worksheet.set_column('AD:AD', 3)
                    worksheet.set_column('AE:AE', 17)
                    worksheet.set_column('AF:AF', 3)

                    presences = 0
                    overtime = 0
                    SP = 0
                    SW = 0
                    KAS = 0
                    KRSN = 0
                    NET = 0
                    TGP = 0
                    TPH = 0
                    BBL = 0
                    OVTB = 0
                    MEALS = 0

                    for line in desain.worked_days_line_ids :
                        if line.code == 'Presences' :
                            presences = line.number_of_days
                        elif line.code == 'Overtime' :
                            overtime = line.number_of_hours
                            if desain.contract_id.wage > desain.contract_id.umk :
                                ov = overtime * (desain.contract_id.umk/56/4*1.5)  
                            else : 
                                ov = overtime * (desain.contract_id.wage/56/4*1.5)

                    for nominal in desain.line_ids :
                        if nominal.code == 'SP' :
                            SP = nominal.amount
                        elif nominal.code == 'SW' :
                            SW = nominal.amount
                        elif nominal.code == 'KAS' :
                            KAS = nominal.amount
                        elif nominal.code == 'KRSN' :
                            KRSN = nominal.amount
                        elif nominal.code == 'NET' :
                            NET = nominal.amount
                        elif nominal.code == 'TGP' :
                            TGP = nominal.amount
                        elif nominal.code == 'TPH' :
                            TPH = nominal.amount
                        elif nominal.code == 'BBL' :
                            BBL = nominal.amount
                        elif nominal.code == 'OVTB' :
                            OVTB = nominal.amount
                        elif nominal.code == 'MEALS' :
                            MEALS = nominal.amount

                    bulan = ["","Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]
                    tanggal = desain.date_to[8:10] + "-" + bulan[int(desain.date_to[5:7])] + "-" + desain.date_to[:4]
                    worksheet.write('%s%s'%(one_letter,row), 'NAMA', workbook.add_format({'bold': 0,'top' : 1,'left': 1,'valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(two_letter,row,five_letter,row),desain.employee_id.name,left_format_top)
                    worksheet.write('%s%s'%(six_letter,row), "", center_format_top)
                    worksheet.write('%s%s'%(seven_letter,row),tanggal,workbook.add_format({'bold': 0,'align':'right','top': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row),'',workbook.add_format({'bold': 0,'top': 1,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+1), 'NIK', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(two_letter,row+1,five_letter,row+1),desain.employee_id.nik,left2_format)
                    worksheet.write('%s%s'%(seven_letter,row+1),desain.employee_id.bank_account_id.bank_id.name,workbook.add_format({'bold': 0,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+1),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+2), 'DIV', workbook.add_format({'bold': 0,'bottom': 1,'left': 1,'valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(two_letter,row+2,five_letter,row+2),desain.employee_id.department_id.name,workbook.add_format({'bold': 0,'bottom' : 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(four_letter,row+2), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+2), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(six_letter,row+2), "", workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+2), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+2),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vleft'}))
                    
                    worksheet.write('%s%s'%(one_letter,row+3), 'G POKOK', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+4), 'PREMI', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+3), presences, center_format)
                    worksheet.write('%s%s'%(two_letter,row+4), presences, center_format)
                    worksheet.write('%s%s'%(tree_letter,row+3), 'x', center_format)
                    worksheet.write('%s%s'%(tree_letter,row+4), 'x', center_format)
                    worksheet.write('%s%s'%(four_letter,row+3), '', center_format)
                    worksheet.write('%s%s'%(four_letter,row+4), '', center_format)
                    worksheet.write('%s%s'%(five_letter,row+3), (desain.contract_id.wage*0.7)/25, workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(five_letter,row+4), (desain.contract_id.wage*0.2)/25, workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(six_letter,row+3), "'=", center_format)
                    worksheet.write('%s%s'%(six_letter,row+4), "'=", center_format)
                    worksheet.write('%s%s'%(seven_letter,row+3), TGP, workbook.add_format({'num_format': '#,##0','bold': 0,'align':'right','valign' : 'vright'}))
                    worksheet.write('%s%s'%(seven_letter,row+4), TPH, workbook.add_format({'num_format': '#,##0','bold': 0,'align':'right','valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+3),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+4),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    
                    worksheet.write('%s%s'%(one_letter,row+5), 'BNS BLN', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+6), 'U LEMBUR', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+7), '', workbook.add_format({'bold': 0,'left': 1,'bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+5), '', center_format)
                    worksheet.write('%s%s'%(two_letter,row+6), overtime, workbook.add_format({'bold': 0,'align':'right','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+7), '0', workbook.add_format({'bold': 0,'align':'right','bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(tree_letter,row+5), '', center_format)
                    worksheet.write('%s%s'%(tree_letter,row+6), 'x', workbook.add_format({'bold': 0,'align':'center','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(tree_letter,row+7), 'x', workbook.add_format({'bold': 0,'align':'center','bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(four_letter,row+5), '', center_format)
                    worksheet.write('%s%s'%(four_letter,row+6), '', workbook.add_format({'bold': 0,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(four_letter,row+7), '', workbook.add_format({'bold': 0,'bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+5), '', right_format)
                    worksheet.write('%s%s'%(five_letter,row+6), int(ov), workbook.add_format({'num_format': '#,##0','bold': 0,'align':'right' ,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+7), '', workbook.add_format({'bold': 0,'bottom':1,'align':'right' ,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(six_letter,row+5), "'", center_format)
                    worksheet.write('%s%s'%(six_letter,row+6), "'=", workbook.add_format({'bold': 0,'align':'center','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(six_letter,row+7), "'=", workbook.add_format({'bold': 0,'align':'center','bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+5), int(BBL), workbook.add_format({'num_format': '#,##0','bold': 0,'align':'right','valign' : 'vright','align':'right'}))
                    worksheet.write('%s%s'%(seven_letter,row+6), int(OVTB), workbook.add_format({'num_format': '#,##0','bold': 0,'align':'right','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+7), '0', workbook.add_format({'bold': 0,'align':'right','bottom':1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+5),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+6),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+7),'',workbook.add_format({'bold': 0,'right': 1,'bottom':1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(seven_letter,row+8), TGP+TPH+BBL+OVTB,workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(one_letter,row+8),'',workbook.add_format({'bold': 0,'left': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+8),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+9),'U MKN',workbook.add_format({'bold': 0,'bottom': 1,'left': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+9), presences, workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(tree_letter,row+9),"x",workbook.add_format({'bold': 0,'align':'center','bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(four_letter,row+9),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(five_letter,row+9),desain.contract_id.meals,workbook.add_format({'bold': 0,'align':'right','bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(six_letter,row+9),"'=",workbook.add_format({'bold': 0,'bottom': 1,'align':'center','valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(seven_letter,row+9),MEALS,workbook.add_format({'num_format': '#,##0','bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+9),'+',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    col_range += 1

                    worksheet.write('%s%s'%(seven_letter,row+10),TGP+TPH+BBL+OVTB+MEALS,workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(one_letter,row+10),'',workbook.add_format({'bold': 0,'left': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+10),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+11),'S POKOK',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+11),SP,workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+11),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+12),'S WAJIB',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+12),SW,workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+12),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+13),'KB KAS',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+13),KAS,workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+13),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+14),'KOREKSI',workbook.add_format({'bold': 0,'left': 1,'align': 'left','bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+14),KRSN,workbook.add_format({'num_format': '#,##0','bold': 0,'bottom': 1,'align': 'right','valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+14),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+14), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(tree_letter,row+14),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(four_letter,row+14),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(five_letter,row+14),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(six_letter,row+14),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))

                    worksheet.write('%s%s'%(one_letter,row+15),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+15),'TOTAL',center1_format)
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+15,seven_letter,row+15),TGP+TPH+BBL+OVTB+MEALS+SP+SW+KAS+KRSN,workbook.add_format({'num_format': '#,##0','valign':'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+15),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+16),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+16),'REAL',workbook.add_format({'bold': 0,'bottom': 1,'font_size':15,'bold':1,'align': 'center','valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+16,seven_letter,row+16),NET,workbook.add_format({'num_format': '#,##0','bold': 0,'bottom': 1,'font_size':15,'bold':1,'align': 'right','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+16),'',workbook.add_format({'bold': 0,'right':1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+17),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+17),desain.employee_id.bank_account_id.bank_id.name,workbook.add_format({'bold': 0,'font_size':15,'bold':1,'align': 'center','valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+17,seven_letter,row+17),NET,workbook.add_format({'num_format': '#,##0','bold': 0,'font_size':15,'bold':1,'align': 'right','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+17),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+18),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+18),'CASH',center1_format)
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+18,seven_letter,row+18),'-',right1_format)
                    worksheet.write('%s%s'%(eeg_letter,row+18),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+19),'',workbook.add_format({'bold': 0,'left': 1,'bottom': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+19),'TOTAL',workbook.add_format({'bold': 1,'bottom': 1,'align': 'center','valign' : 'vright'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+19,seven_letter,row+19),NET,workbook.add_format({'num_format': '#,##0','bold': 0,'align':'right','valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+19),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+19), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(tree_letter,row+19),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(four_letter,row+19),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    #worksheet.write('%s%s'%(six_letter,row+18),NET,workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    #worksheet.write('%s%s'%(seven_letter,row+18),'',workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    NETS = terbilang(NET, 'idr', 'idr')
                    worksheet.merge_range('%s%s:%s%s'%(one_letter,row+20,eeg_letter,row+21),NETS,workbook.add_format({'bold': 1,'border': 1,'align':'center','valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+22),'Payroll',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+22), '', workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))
                    worksheet.merge_range('%s%s:%s%s'%(tree_letter,row+22,four_letter,row+22),'Finance',workbook.add_format({'bold': 0,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(five_letter,row+22),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vcenter'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+22,seven_letter,row+22),'Checker',workbook.add_format({'bold': 0,'align':'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+22),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+23),'',workbook.add_format({'bold': 0,'bottom': 1,'left': 1,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+23), '', workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    worksheet.merge_range('%s%s:%s%s'%(tree_letter,row+23,four_letter,row+23),'',workbook.add_format({'bold': 0,'align': 'left','bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(five_letter,row+23),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vcenter'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+23,seven_letter,row+23),'',workbook.add_format({'bold': 0,'bottom': 1,'align':'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+23),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    
                    x +=1
                    if x == jum :
                        row += 24
                        desain_brand_ids -= five_desain_ids   

                elif desain.contract_id.type_id.name == "BORONGAN" :  
                    #import pdb;pdb.set_trace()
                    #import pdb;pdb.set_trace()
                    presences1 = 0
                    presences2 = 0
                    SP = 0
                    SW = 0
                    UBR1 = 0
                    UBR2 = 0
                    KRJN1 = 0
                    KRJN2 = 0
                    BNPT1 = 0
                    BNPT2 = 0
                    for line in desain.worked_days_line_ids :
                        if line.code == 'Presences1' :
                            presences1 = line.number_of_days
                        elif line.code == 'Presences2' :
                            presences2 = line.number_of_days

                    for nominal in desain.line_ids :
                        if nominal.code == 'SP' :
                            SP = nominal.amount
                        elif nominal.code == 'SW' :
                            SW = nominal.amount
                        elif nominal.code == 'UBR1' :
                            UBR1 = nominal.amount
                        elif nominal.code == 'UBR2' :
                            UBR2 = nominal.amount
                        elif nominal.code == 'KRJN1' :
                            KRJN1 = nominal.amount
                        elif nominal.code == 'KRJN2' :
                            KRJN2 = nominal.amount
                        elif nominal.code == 'BNPT1' :
                            BNPT1 = nominal.amount
                        elif nominal.code == 'BNPT2' :
                            BNPT2 = nominal.amount
                        elif nominal.code == 'NET' :
                            NET = nominal.amount
                    bulan = ["","Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]
                    tanggal = desain.date_to[8:10] + "-" + bulan[int(desain.date_to[5:7])] + "-" + desain.date_to[:4]
                    worksheet.write('%s%s'%(one_letter,row), 'NAMA', workbook.add_format({'bold': 0,'top' : 1,'left': 1,'valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(two_letter,row,five_letter,row),desain.employee_id.name,left_format_top)
                    worksheet.write('%s%s'%(six_letter,row), "", center_format_top)
                    worksheet.write('%s%s'%(seven_letter,row),tanggal,workbook.add_format({'bold': 0,'align':'right','top': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row),'',workbook.add_format({'bold': 0,'top': 1,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+1), 'DIV', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(two_letter,row+1,five_letter,row+1),desain.employee_id.department_id.name,workbook.add_format({'bold': 0,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(four_letter,row+1), '', workbook.add_format({'bold': 0,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+1), '', workbook.add_format({'bold': 0,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(six_letter,row+1), "", workbook.add_format({'bold': 0,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+1), '', workbook.add_format({'bold': 0,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+1),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))
                    
                    worksheet.write('%s%s'%(one_letter,row+2), 'UT', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+3), '', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+2), '1', center_format)
                    worksheet.write('%s%s'%(two_letter,row+3), '2', center_format)
                    worksheet.write('%s%s'%(tree_letter,row+2), '6', center_format)
                    worksheet.write('%s%s'%(tree_letter,row+3), '6', center_format)
                    worksheet.write('%s%s'%(four_letter,row+2), 'x', center_format)
                    worksheet.write('%s%s'%(four_letter,row+3), 'x', center_format)
                    worksheet.write('%s%s'%(five_letter,row+2), desain.contract_id.uang_transport, right_format)
                    worksheet.write('%s%s'%(five_letter,row+3), desain.contract_id.uang_transport, right_format)
                    worksheet.write('%s%s'%(six_letter,row+2), "'=", center_format)
                    worksheet.write('%s%s'%(six_letter,row+3), "'=", center_format)
                    worksheet.write('%s%s'%(seven_letter,row+2), desain.contract_id.uang_transport * presences1, workbook.add_format({'align':'right','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(seven_letter,row+3), desain.contract_id.uang_transport * presences2, workbook.add_format({'align':'right','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+2),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+3),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    
                    worksheet.write('%s%s'%(one_letter,row+4), 'UPAH', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+5), '', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+4), '1', center_format)
                    worksheet.write('%s%s'%(two_letter,row+5), '2', center_format)
                    worksheet.write('%s%s'%(tree_letter,row+4), '', center_format)
                    worksheet.write('%s%s'%(tree_letter,row+5), '', center_format)
                    worksheet.write('%s%s'%(four_letter,row+4), '', center_format)
                    worksheet.write('%s%s'%(four_letter,row+5), '', center_format)
                    worksheet.write('%s%s'%(five_letter,row+4), '', right_format)
                    worksheet.write('%s%s'%(five_letter,row+5), '', right_format)
                    worksheet.write('%s%s'%(six_letter,row+4), "", center_format)
                    worksheet.write('%s%s'%(six_letter,row+5), "", center_format)
                    worksheet.write('%s%s'%(seven_letter,row+4), UBR1, workbook.add_format({'align':'right','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(seven_letter,row+5), UBR2, workbook.add_format({'align':'right','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+4),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+5),'',workbook.add_format({'bold': 0,'right': 1,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+6), 'KRJN', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+7), '', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+6), '1', center_format)
                    worksheet.write('%s%s'%(two_letter,row+7), '2', center_format)
                    worksheet.write('%s%s'%(seven_letter,row+6), KRJN1, workbook.add_format({'align':'right','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(seven_letter,row+7), KRJN2, workbook.add_format({'align':'right','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+6),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+7),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(one_letter,row+8), 'BNS/POT', workbook.add_format({'bold': 0,'left': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(one_letter,row+9), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(two_letter,row+8), '1', center_format)
                    worksheet.write('%s%s'%(two_letter,row+9), '2', workbook.add_format({'bold': 0,'bottom': 1,'align' : 'center','valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(tree_letter,row+8), '', center_format)
                    worksheet.write('%s%s'%(tree_letter,row+9), '', workbook.add_format({'bold': 0,'bottom': 1,'align' : 'center','valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(four_letter,row+8), '', center_format)
                    worksheet.write('%s%s'%(four_letter,row+9), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'center'}))
                    worksheet.write('%s%s'%(five_letter,row+8), '', right_format)
                    worksheet.write('%s%s'%(five_letter,row+9), '', workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(six_letter,row+8), "", center_format)
                    worksheet.write('%s%s'%(six_letter,row+9), "", workbook.add_format({'bold': 0,'bottom': 1,'valign' : 'vcenter'}))
                    worksheet.write('%s%s'%(seven_letter,row+8),BNPT1, workbook.add_format({'align':'right','bold': 0,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(seven_letter,row+9),BNPT2, workbook.add_format({'align':'right','bold': 0,'bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+8),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+9),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vleft'}))

                    worksheet.write('%s%s'%(seven_letter,row+10), (desain.contract_id.uang_transport * presences1) + (desain.contract_id.uang_transport * presences2) + UBR1 + UBR2 + KRJN1 + KRJN2 + BNPT1 + BNPT2 ,right_format)
                    worksheet.write('%s%s'%(one_letter,row+10),'',workbook.add_format({'bold': 0,'left': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+10),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+11),'S POKOK',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+11),SP,right_format)
                    worksheet.write('%s%s'%(eeg_letter,row+11),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+12),'S WAJIB',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+12),SW,right_format)
                    worksheet.write('%s%s'%(eeg_letter,row+12),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+13),'UPAH HARIAN',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+13),'-',right_format)
                    worksheet.write('%s%s'%(eeg_letter,row+13),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+14),'KB MKN',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+14),'-',right_format)
                    worksheet.write('%s%s'%(eeg_letter,row+14),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+15),'SRGM',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+15),'-',right_format)
                    worksheet.write('%s%s'%(eeg_letter,row+15),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+16),'KRK/DLL',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(seven_letter,row+16),'-',right_format)
                    worksheet.write('%s%s'%(eeg_letter,row+16),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+17),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+17),'TOTAL',center1_format)
                    worksheet.write('%s%s'%(seven_letter,row+17),NET,right_format)
                    worksheet.write('%s%s'%(eeg_letter,row+17),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+18),'',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(five_letter,row+18),'REAL',workbook.add_format({'bold': 0,'bottom': 1,'font_size':15,'bold':1,'align': 'center','valign' : 'vleft'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+18,seven_letter,row+18),NET,workbook.add_format({'bold': 0,'bottom': 1,'font_size':15,'bold':1,'align': 'right','valign' : 'vleft'}))
                    worksheet.write('%s%s'%(eeg_letter,row+18),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))
                    NETS = terbilang(NET, 'idr', 'idr')
                    worksheet.merge_range('%s%s:%s%s'%(one_letter,row+19,eeg_letter,row+19),NETS,workbook.add_format({'bold': 1,'border': 1,'align':'center','valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+20),'Payroll',workbook.add_format({'bold': 0,'left': 1,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+20), '', workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))
                    worksheet.merge_range('%s%s:%s%s'%(tree_letter,row+20,four_letter,row+20),'Finance',workbook.add_format({'bold': 0,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(five_letter,row+20),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vcenter'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+20,seven_letter,row+20),'Checker',workbook.add_format({'bold': 0,'align':'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+20),'',workbook.add_format({'bold': 0,'right': 1,'valign' : 'vright'}))

                    worksheet.write('%s%s'%(one_letter,row+21),'',workbook.add_format({'bold': 0,'bottom': 1,'left': 1,'align': 'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(two_letter,row+21), '', workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    worksheet.merge_range('%s%s:%s%s'%(tree_letter,row+21,four_letter,row+21),'',workbook.add_format({'bold': 0,'align': 'left','bottom': 1,'valign' : 'vright'}))
                    worksheet.write('%s%s'%(five_letter,row+21),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vcenter'}))
                    worksheet.merge_range('%s%s:%s%s'%(six_letter,row+21,seven_letter,row+21),'',workbook.add_format({'bold': 0,'bottom': 1,'align':'left','valign' : 'vright'}))
                    worksheet.write('%s%s'%(eeg_letter,row+21),'',workbook.add_format({'bold': 0,'bottom': 1,'right': 1,'valign' : 'vright'}))
                    
                    x +=1
                    if x == jum :
                        row += 22
                        desain_brand_ids -= five_desain_ids

        #sampai sini
        #import pdb;pdb.set_trace()
        workbook.close()
        result = base64.encodestring(fp.getvalue())
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        filename = 'Slip Gaji %s'%(date_string)
        filename += '%2Exlsx'
        self.write({'file_data':result})
        url = "web/content/?model="+self._name+"&id="+str(self.id)+"&field=file_data&download=true&filename="+filename
        return {
            'name': 'Slip Gaji',
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }


    @api.model
    def default_get(self, fields_list):
        warning = ''
        skipped = []
        ctx = self.env.context.copy()
        obj = self.env['hr.payslip']
        for po in ctx.get('active_ids',[]):
            po_id = obj.browse(po)
            skipped.append(po_id.name)
        if skipped:
            warning = 'Slip Gaji '+', '.join(skipped)
        return {'warning' : warning}
