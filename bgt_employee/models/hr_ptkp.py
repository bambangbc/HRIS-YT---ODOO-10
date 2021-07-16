from odoo import api, fields, models, _

class Hr_ptkp(models.Model):
    _name = 'hr.ptkp'
    _rec_name = 'kode'

    kode    		 = fields.Char("Kode")
    nominal_bulan    = fields.Float("Nominal Bulan")
    nominal_tahun    = fields.Float("Nominal Tahun")