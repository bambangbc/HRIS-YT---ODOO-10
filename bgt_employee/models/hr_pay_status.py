from odoo import api, fields, models, _

class Hr_Pay_Status(models.Model):
    _name = 'hr.pay.status'

    name = fields.Char(string="Name", required=True)