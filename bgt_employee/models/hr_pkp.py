from odoo import api, fields, models, _

class Hr_pkp(models.Model):
    _name = 'hr.pkp'
    _rec_name = 'kode'

    kode           = fields.Char("Kode")
    nominal_min    = fields.Float("Nominal Min")
    nominal_max    = fields.Float("Nominal Max")
    pajak		   = fields.Float("Pajak (%)")