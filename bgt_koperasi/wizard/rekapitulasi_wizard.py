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


class RekapKoperasiWizard(models.TransientModel):
    _name = 'rekap.koperasi.wizard'

    date_start = fields.Date('Date Start' )
    date_end = fields.Date('Date End', default=fields.Datetime.now, required=True )


    @api.multi
    def query_rekap(self):
        koperasi = self.env['hr.koperasi']
        koperasi_detail = self.env['hr.koperasi.detail']
        rekap = self.env['hr.rekap.koperasi']
        # hapus record existing
        self._cr.execute("DELETE FROM hr_rekap_koperasi")

        starting_balance = 0.0
        starting_balance_date = False
        if self.date_start :
            starting_balance_date = self.date_start
            # search starting balance
            balance_header = koperasi.search([('tgl_pencairan','<',self.date_start),
                                    ('pencairan','>',0.0),
                                    ('state','in',('validate','done'))], order="tgl_pencairan asc")
            balance_details = koperasi_detail.search([('tanggal_angsuran','<',self.date_start),
                                    ('paid','=',True),
                                    ('koperasi_id.state','in',('validate','done'))], order="tanggal_angsuran asc")
            bal_header = 0.0
            if balance_header :
                bal_header = sum(balance_header.mapped('pencairan'))
            bal_details = 0.0
            if balance_details :
                bal_details = sum(balance_details.mapped('nominal'))
            starting_balance = bal_details - bal_header # pemasukan dikurangi pengeluaran

            details = koperasi_detail.search([('tanggal_angsuran','>=',self.date_start),
                                    ('tanggal_angsuran','<=',self.date_end),
                                    ('paid','=',True),
                                    ('koperasi_id.state','in',('validate','done'))], order="tanggal_angsuran asc")

        else :
            details = koperasi_detail.search([('tanggal_angsuran','<=',self.date_end),
                                    ('paid','=',True),
                                    ('koperasi_id.state','in',('validate','done'))], order="tanggal_angsuran asc")
        rekap.create({'sequence'     : 0,
                        'date'      : starting_balance_date,
                        'description' : 'Saldo Awal',
                        'debit'     : 0.0,
                        'credit'    : 0.0,
                        'balance'   : starting_balance})
        if not details :
            raise UserError(_('Tidak ada data untuk ditampilkan !'))
        
        sequence = 1
        koperasiID = []
        balance = starting_balance
        for det in details :
            if det.koperasi_id :
                type = det.koperasi_id.employee_id.contract_id.type_id.name
                if det.koperasi_id.id not in koperasiID :
                    if det.koperasi_id.type == 'pokok' : # nabung
                        desc = 'Pengembalian Simpanan Pokok '+ det.koperasi_id.employee_id.name
                    else : # peminjaman
                        desc = 'Pinjaman Karyawan '+ det.koperasi_id.employee_id.name
                    debit = 0.0
                    credit = det.koperasi_id.pinjaman
                else :
                    if det.koperasi_id.type == 'pokok' : # nabung
                        desc = 'Simpanan Pokok '+ det.koperasi_id.employee_id.name
                    else : # peminjaman
                        desc = 'Simpanan Wajib '+ det.koperasi_id.employee_id.name
                    debit = det.nominal
                    credit = 0.0
                balance = starting_balance + credit - debit
                datas = {'sequence'         : sequence,
                            'date'          : det.tanggal_angsuran,
                            'description'   : desc,
                            'type'          : type,
                            'debit'         : debit,
                            'credit'        : credit,
                            'balance'       : balance}
                rekap.create(datas)
                koperasiID.append(det.koperasi_id.id)
                sequence += 1
        rekap.create({'sequence'     : 999999,
                        'date'      : self.date_end,
                        'description' : 'Saldo Akhir',
                        'debit'     : 0.0,
                        'credit'    : 0.0,
                        'balance'   : balance})
        view_id = self.env.ref('bgt_koperasi.view_hr_rekap_koperasi_tree').id

        return {
            'name': _('Rekapitulasi Koperasi'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'hr.rekap.koperasi',
            'views': [(view_id, 'tree')],
            'view_id': view_id,
            'target': 'current',
            'limit' : 999999,
            #'res_id': self.ids[0],
            'context': {}}

RekapKoperasiWizard()