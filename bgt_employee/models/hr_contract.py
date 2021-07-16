from odoo import api, fields, models, _
import datetime

class Hr_contract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    pay_status_id           = fields.Many2one(comodel_name="hr.pay.status", string="Pay Status")