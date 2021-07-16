from odoo import api, fields, models, _

class Hr_Domisili_Provinsi(models.Model):
    _name = 'hr.domisili.provinsi'

    name = fields.Char(string="Name", required=True)

class Hr_Domisili_Kota(models.Model):
    _name = 'hr.domisili.kota'

    name = fields.Char(string="Name", required=True)
    provinsi_id = fields.Many2one(string="Provinsi", required=True, comodel_name="hr.domisili.provinsi" )

class Hr_Domisili_Kecamatan(models.Model):
    _name = 'hr.domisili.kecamatan'

    name = fields.Char(string="Name", required=True)
    kota_id = fields.Many2one(string="Kota / Kabupaten", required=True, comodel_name="hr.domisili.kota")

class Hr_Domisili_Kelurahan(models.Model):
    _name = 'hr.domisili.kelurahan'

    name = fields.Char(string="Name", required=True)
    kecamatan_id = fields.Many2one(string="Kecamatan", required=True, comodel_name="hr.domisili.kecamatan")