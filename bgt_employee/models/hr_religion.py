from odoo import api, fields, models, _

class Hr_Religion(models.Model):
    _name = 'hr.religion'

    name = fields.Char(string="Name", required=True)