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


class GenerateBungaWizard(models.TransientModel):
    _name = 'bunga.koperasi.wizard'

    period = fields.Date('Periode Koperasi')
    date_start = fields.Date('Date Start Bunga',default=fields.Datetime.now, required=True)
    date_end = fields.Date('Date End Bunga', default=fields.Datetime.now, required=True )

    @api.multi
    def generate_bunga(self):
        total_bunga = 0
        simpanan_pokok = self.env['hr.koperasi']
        search_pokok = simpanan_pokok.search([('type','=','pokok'),('tanggal_pengajuan','=',self.period),('state','=','done'),('sisa_angsuran','=',0)])
        simpanan_wajib = self.env['hr.koperasi.detail']
        search_wajib = simpanan_wajib.search([('type','=','wajib'),('tanggal_angsuran','>=',self.date_start),('tanggal_angsuran','<=',self.date_end),('paid','=',True)])

        for wajib in search_wajib :
            angsuran = wajib.koperasi_id.angsuran
            bunga = wajib.koperasi_id.riba
            total_bunga += bunga/angsuran
        import pdb;pdb.set_trace()
        #import pdb;pdb.set_trace()
        keuntungan_bunga = total_bunga/len(search_pokok)
        for pokok in search_pokok :
            pokok.write({'keuntungan_bunga':keuntungan_bunga})
        # hapus record existing
        self._cr.execute("DELETE FROM hr_rekap_koperasi")



GenerateBungaWizard()