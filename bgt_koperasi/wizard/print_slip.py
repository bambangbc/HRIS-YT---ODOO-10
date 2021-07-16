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

import xlsxwriter
import base64
from odoo import fields, models, api
from cStringIO import StringIO
import pytz
from pytz import timezone
from datetime import datetime
import PIL
import io

class SlipKoperasi(models.TransientModel):
    _name = "slip.koperasi"
    _description = "Slip Koperasi"

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))

    file_data = fields.Binary('File', readonly=True)

    @api.multi
    def action_print(self):
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet('Slip')
       # worksheet.set_column('A:J', 12)

        #konten di sini
        active_ids = self._context.get('active_ids')
        koperasi_ids = self.env['hr.koperasi'].browse(active_ids)
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
            'border': 1,
            'valign': 'vcenter',
        })
        title_format.set_text_wrap()
        result_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
        })
        result_format.set_text_wrap()
        image_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        row = 1
        column = 1
        no_sheet = 1
        ##import pdb;pdb.set_trace()
        for kop in koperasi_ids :
            col = {1:['A','B','C','D'], 2:['F','G','H','I','J'], 3:['L','M','N','O'], 4:['Q','R','S','T']}
            while koperasi_ids :
                four_slip = koperasi_ids[0:4]
                col_range = 1

                tes = col[col_range][0]

                worksheet.write(row, 0, 'testod')
                import pdb;pdb.set_trace()
                col_range += 1

                row += 1
                koperasi_ids -= four_slip
        workbook.close()
        result = base64.encodestring(fp.getvalue())
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        filename = 'Slip Koperasi %s'%(date_string)
        filename += '%2Exlsx'
        self.write({'file_data':result})
        url = "web/content/?model="+self._name+"&id="+str(self.id)+"&field=file_data&download=true&filename="+filename
        return {
            'name': 'Slip Payslip',
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

SlipKoperasi()