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
from odoo import api, fields, models, exceptions, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import dateutil.parser
from odoo.exceptions import ValidationError, RedirectWarning, UserError


class HrKoperasi(models.Model):
    _name = 'hr.koperasi'
    _description = "Pengelolaan Koperasi"
    _order = "name desc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for i in self:
            contract_exist = self.env['hr.contract'].search([('employee_id','=',i.employee_id.id)], order="date_start desc", limit=1)
            if contract_exist:
                i.pinjaman = contract_exist.type_id.default_nominal
                i.angsuran = contract_exist.type_id.default_tenor
                i.riba_percent = contract_exist.type_id.default_bunga


    @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft' :
                raise UserError(_('Data yang bisa dihapus hanya yg berstatus draft'))
        return super(HrKoperasi, self).unlink()

    @api.depends('pinjaman', 'angsuran','type')
    def _compute_riba(self):
        for gr in self:
            if gr.pinjaman > 0.0 :
                gr.riba = gr.angsuran*gr.riba_percent/100*gr.pinjaman
                if gr.type == 'pokok':
                    gr.riba = 0.0
                gr.total_pinjaman = gr.pinjaman + gr.riba
                gr.cicilan_period = (gr.pinjaman + gr.riba)/gr.angsuran

    name = fields.Char('Nomor', default='New', copy=False, readonly=True, )
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=True, track_visibility='onchange')
    tanggal_pengajuan =  fields.Date(string="Tanggal Period", required=False, track_visibility='onchange')
    tanggal_dokumen =  fields.Date(string="Created Date", default=fields.Datetime.now, readonly=True)
    tanggal_angsuran =  fields.Integer(string="Default Tanggal Angsuran", default=20, size=2, track_visibility='onchange')
    pinjaman = fields.Float(string="Nominal Pinjaman", required=True, track_visibility='onchange')
    riba = fields.Float(string="Bunga", required=False, track_visibility='onchange', store=True, compute="_compute_riba")
    total_pinjaman = fields.Float(string="Nominal+Bunga", required=False, track_visibility='onchange', store=True, compute="_compute_riba")
    cicilan_period =  fields.Float(string="Cicilan/Period", required=False,track_visibility='onchange', store=True, compute="_compute_riba")
    angsuran = fields.Integer(string="Tenor", required=True, track_visibility='onchange', default=1)
    riba_percent = fields.Float(string="Bunga(%)", required=True, track_visibility='onchange')
    job_id = fields.Many2one(comodel_name="hr.job", string="Posisi", required=False, related="employee_id.job_id", store=True)
    department_id = fields.Many2one(comodel_name="hr.department", string="Department", required=False, related="employee_id.department_id", store=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('validate', 'Approved'),
                              ('cancel', 'Cancelled'),
                              ('done', 'Done'),
                              ('refuse','Refused')], default='draft', required=True, index=True, track_visibility='onchange')
    kasbon_ids = fields.One2many("hr.koperasi.detail", "koperasi_id", "Detail Pinjaman")
    type = fields.Selection([('pokok','Simpanan Pokok'),('wajib','Simpanan Wajib')],"Type Keanggotaan", track_visibility='onchange', default="pokok" )
    user_id = fields.Many2one("res.users", "Creator", default=lambda self: self.env.user,readonly=True)
    manager_id = fields.Many2one("hr.employee","Manager",related="department_id.manager_id", stror=True)
    start_angsuran = fields.Date("Start Angsuran")
    end_angsuran = fields.Date("End Angsuran")
    sisa_angsuran = fields.Float("Sisa Angsuran", compute="_get_sisa_angsuran", store=True)
    sisa_cicilan = fields.Integer("Sisa Tenor", compute="_get_sisa_angsuran", store=True)
    mekanisme = fields.Selection([('otomatis','Otomatis Payroll'),('manual','Manual')],string="Pembayaran")
    employee_ids = fields.Many2many('hr.employee', string='Ahli Waris',
                                    required=False)
    periode = fields.Selection([('2019','2019'),('2020','2020'),('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),('2025','2025'),('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),('2030','2030')],"Periode")
    notes = fields.Text('Notes')
    tgl_pencairan = fields.Date("Tgl Pencairan")
    pencairan = fields.Float("Pencairan")
    keuntungan_bunga = fields.Float("Keuntungan Dari Bunga", readonly=True)

    no_jaminan = fields.Char("No BPKB")
    name_jaminan = fields.Char("Nama Yang Tertera Di BPKB")
    alamat_jaminan = fields.Char("alamat Yang Tertera Di BPKB")
    tanggal_penyerahan = fields.Date("Tanggal Penyerahan")
    tanggal_pengembalian = fields.Date("Tanggal Pengembalian")

    @api.depends('kasbon_ids','kasbon_ids.paid')
    def _get_sisa_angsuran(self):
        for rec in self:
            if rec.kasbon_ids :
                outstandinng = rec.kasbon_ids.filtered(lambda x: not x.paid)
                if not outstandinng and rec.id:
                    self.env.cr.execute("update hr_koperasi set state='done' where id = %s",
                            ( rec.id,))
                    rec.sisa_angsuran = 0.0
                    rec.sisa_cicilan = 0
                else :
                    # for u in rec.kasbon_ids.filtered(lambda x: not x.paid):
                    #     total += u.nominal
                    rec.sisa_angsuran = sum(rec.kasbon_ids.filtered(lambda x: not x.paid).mapped('nominal'))
                    rec.sisa_cicilan = len(rec.kasbon_ids.filtered(lambda x: not x.paid))

    @api.multi
    def button_done(self):
        return self.write({'state': 'done'})

    @api.multi
    def button_confirm(self):
        if self.total_pinjaman <= 0.0 or self.angsuran <= 0.0:
                raise exceptions.ValidationError(_("Pinjaman dan angsuran harus diisi lebih dari nol !"))
        self._cr.execute('DELETE FROM hr_koperasi_detail where koperasi_id = %d' %(self.id))

        angsuran = self.total_pinjaman / self.angsuran
        if self.start_angsuran :
            i = -1
            start_angsuran = self.start_angsuran
            jml_angsuran = self.angsuran-1
        else :
            i = 0
            start_angsuran = self.tanggal_pengajuan
            #self.write({'start_angsuran' :datetime.strptime(start_angsuran,'%Y-%m-%d') + relativedelta(months=i)})
            jml_angsuran = self.angsuran
        while i < jml_angsuran:
            i = i + 1
            data = {
              'koperasi_id':self.id,
              # 'tanggal_angsuran': datetime.strptime(start_angsuran,'%Y-%m-%d') + relativedelta(months=i, day=self.tanggal_angsuran),
              #'tanggal_angsuran': datetime.strptime(start_angsuran,'%Y-%m-%d') + relativedelta(months=i),
              'nominal':angsuran,
              'cicilan':i,
            }
            self.env['hr.koperasi.detail'].create(data)
        return self.write({'state'          : 'confirm'})


    @api.multi
    def button_validate(self):
        if not self.kasbon_ids :
            raise UserError(_('Detail jadwal pembayaran pinjaman tidak boleh kosong !'))
        return self.write({'state' : 'validate'})

    @api.multi
    def button_cancel(self):
        return self.write({'state' : 'cancel'})

    @api.multi
    def button_set_to_draft(self):
        return self.write({'state' : 'draft'})

    @api.multi
    def button_refuse(self):
        return self.write({'state' : 'refuse'})

    @api.model
    def create(self, vals):
        if not vals.get('name', False) or vals['name'] == 'New':
           sequence = self.env['ir.sequence'].next_by_code('hr.koperasi') or 'Number not found !'
           vals['name'] = sequence
        return super(HrKoperasi, self).create(vals)

    @api.multi
    def write(self, vals):

    	if 'kasbon_ids' in vals:

	    	kasbon_id = self.id

	    	pinjaman = self.env['hr.koperasi'].search([('id','=',kasbon_id)]).total_pinjaman

	    	nominal_noupdate = 0
	    	nominal_update = 0
	    	nominal_create = 0
	    	total_nominal = 0

	    	for line in vals['kasbon_ids']:
	    		print line

	    		#kode 0 berarti record baru
	    		#kode 1 berarti record diupdate
	    		#kode 2 berarti record didelete
	    		#kode 4 berarti record tidak diupdate ataupun didelete

	    		if line[0] == 4 :
	    			kasbon_line = line[1]
	    			kasbon_noupdate = self.env['hr.koperasi.detail'].search([('koperasi_id','=',kasbon_id),
                                                                            ('id','=',kasbon_line)])
	    			for k in kasbon_noupdate:
	    				nominal_noupdate = nominal_noupdate + k.nominal

	    		if line[0] == 0 :
	    			nominal_create = nominal_create + line[2]['nominal']

	    		if line[0] == 1 and 'nominal' in line[2]:
	    			nominal_update = nominal_update + line[2]['nominal']

	    		if line[0] == 1 and 'nominal' not in line[2]:
	    			line_id = line[1]
	    			kasbon_update = self.env['hr.koperasi.detail'].search([('koperasi_id','=',kasbon_id),('id','=',line_id)])
	    			for ku in kasbon_update:
	    				nominal_update = nominal_update + ku.nominal

	    		total_nominal = nominal_noupdate + nominal_create + nominal_update


	    		print nominal_noupdate
	    		print nominal_create
	    		print nominal_update
	    		print total_nominal
	    		print pinjaman

	    	if total_nominal < pinjaman:
	    		raise exceptions.ValidationError(_("Total semua angsuran kurang dari jumlah nominal pinjaman!"))
	    	if total_nominal > pinjaman:
	    		raise exceptions.ValidationError(_("Total semua angsuran melebihi jumlah nominal pinjaman!"))

    	return super(HrKoperasi, self).write(vals)

HrKoperasi()

class HrKoperasiDetail(models.Model):
    _name = 'hr.koperasi.detail'

    koperasi_id = fields.Many2one(comodel_name="hr.koperasi", string="Koperasi")
    tanggal_angsuran =  fields.Date(string="Tanggal Pembayaran", required=False)
    nominal =  fields.Float(string="Nominal", required=True)
    cicilan =  fields.Integer(string="Cicilan Ke", required=True)
    paid = fields.Boolean(String="Paid")
    name = fields.Char("Kode Pinjaman")
    payslip = fields.Char("Payslip")
    employee_id = fields.Many2one("hr.employee","Nama Karyawan", related="koperasi_id.employee_id", store=True)
    nik = fields.Char("NIK",related="koperasi_id.employee_id.nik", store=True)
    department_id = fields.Many2one('hr.department', 'Divisi', related="koperasi_id.employee_id.department_id", store=True)
    job_id = fields.Many2one('hr.job', 'Jabatan', related="koperasi_id.employee_id.job_id", store=True)
    type = fields.Selection([('pokok','Simpanan Pokok'),('wajib','Simpanan Wajib')],"Type Keanggotaan", related="koperasi_id.type", store=True)

    @api.model
    def create(self, vals):
        kasbon_id = vals.get('koperasi_id')
        kasbon = self.env['hr.koperasi.detail'].search([('koperasi_id','=',kasbon_id)])
        cicilan = len(kasbon) + 1
        vals['cicilan'] = cicilan
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.koperasi')
        return super(HrKoperasiDetail, self).create(vals)

HrKoperasiDetail()


class HrRekapKoperasi(models.Model):
    _name = 'hr.rekap.koperasi'
    _rec_name = 'sequence'
    _order = 'sequence asc'

    sequence = fields.Float('Sequence', required=True)
    type = fields.Char('Type')
    date = fields.Date('Tanggal')
    description = fields.Char('Keterangan', required=True)
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')
    balance = fields.Float('Saldo')

HrRekapKoperasi()