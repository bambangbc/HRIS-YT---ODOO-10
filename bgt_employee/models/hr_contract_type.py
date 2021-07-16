from odoo import api, fields, models, _

class Hr_contract_type(models.Model):
    _name = 'hr.contract.type'
    _inherit = 'hr.contract.type'

    #additional fields

    #group field for BPJS Kesehatan
    bpjs_kes_perusahaan = fields.Float(string="Kontribusi Perusahaan (%)")
    bpjs_kes_karyawan = fields.Float(string="Kontribusi Karyawan (%)")
    bpjs_kes_nominal_max = fields.Float(string="Nominal Max (Rp)")
    bpjs_kes_nominal_min = fields.Float(string="Nominal Min (Rp)")

    #group fields for BPJS Ketenagakerjaan
    bpjs_ket_jkk = fields.Float(string="JKK (%)")
    bpjs_ket_jkm = fields.Float(string="JKM (%)")

    #group fields for pensiun
    pensiun_perusahaan = fields.Float(string="Kontribusi Perusahaan (%)")
    pensiun_karyawan = fields.Float(string="Kontribusi Karyawan (%)")
    pensiun_nominal_max = fields.Float(string="Nominal Max (Rp)")
    pensiun_nominal_min = fields.Float(string="Nominal Min (Rp)")

    #group fields for biaya jabatan
    jabatan_biaya = fields.Float(string="Biaya Jabatan (%)")
    jabatan_nominal_max = fields.Float(string="Nominal Max (Rp)")

    #group fields for JHT
    jht_perusahaan = fields.Float(string="Kontribusi Perusahaan (%)")
    jht_karyawan = fields.Float(string="Kontribusi Karyawan (%)")
    jht_nominal_max = fields.Float(string="Nominal Max (Rp)")
    jht_nominal_min = fields.Float(string="Nominal Min (Rp)")





