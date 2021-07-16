from odoo import api, fields, models, _
import datetime
from dateutil import relativedelta

class Hr_employee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    @api.multi
    @api.depends('name', 'nik')
    def name_get(self):
        result = []
        for i in self:
            name = i.name
            if i.nik :
                name =  '['+i.nik+'] ' + name
            result.append((i.id, name))
        return result

    #additional field
    absen_id                = fields.Char(string="ID Absen")
    no_mesin                = fields.Char(string="No Mesin")
    npwp                    = fields.Char(string="NPWP")
    ptkp_id                 = fields.Many2one(comodel_name="hr.ptkp", string="PTKP Status")
    nik                     = fields.Char(string="NIK")
    bpjs_kesehatan          = fields.Char(string="BPJS Kesehatan", required=False)
    bpjs_ketenagakerjaan 	= fields.Char(string="BPJS Ketenagakerjaan", required=False)
    religion_id             = fields.Many2one(comodel_name="hr.religion", string='Agama')
    work_date               = fields.Date(string="Tanggal Masuk Kerja")
    contract_type_id        = fields.Many2one(string="Status Karyawan", comodel_name="hr.contract.type")
    bank_account            = fields.Char(string="Nama Bank")
    bank_number             = fields.Char(string="No Rek")
    department_id           = fields.Many2one('hr.department', string='Department', required=True)
    job_id                  = fields.Many2one('hr.job', string='Job Title', required=True)
    identification_id       = fields.Char(string='No KTP')
    pasport_id              = fields.Char(string='No Paspor')
    alamat_domisili         = fields.Char(string="Alamat Domisili")
    alamat_ktp              = fields.Char(string="Alamat KTP")
    provinsi_id             = fields.Many2one(comodel_name="hr.domisili.provinsi", string="Provinsi")
    kota_id                 = fields.Many2one(comodel_name="hr.domisili.kota", string="Kota/Kabupaten")
    kecamatan_id            = fields.Many2one(comodel_name="hr.domisili.kecamatan", string="Kecamatan/Kelurahan", domain="[('kota_id'),'=',kota_id]")
    kelurahan_id            = fields.Many2one(comodel_name="hr.domisili.kelurahan", string="Kelurahan", domain="[('kota_id'),'=',kota_id]")
    no_telepon              = fields.Char(string="No Telp")
    no_hp                   = fields.Char(string="No HP")
    married_date            = fields.Date(string="Married Date")
    email            		= fields.Char(string="Email")
    marital                 = fields.Selection([('single', 'Belum Menikah'),
                                                ('married', 'Menikah'),
                                                ('widow','Janda'),
                                                ('widower','Duda')], string='Marital Status')
    gender                  = fields.Selection([
                                                ('male', 'Laki-laki'),
                                                ('female', 'Perempuan'),
                                                ('other', 'Other')
                                            ])
    no_seri_ijazah = fields.Char(string="Nomor Seri Ijazah")

    jenjang  = fields.Many2one(comodel_name="hr.recruitment.degree", string="Jenjang Pendidikan")
    school_name = fields.Char(string="Sekolah")
    jurusan = fields.Char(string="Jurusan")
    status_ijazah = fields.Selection([('ada', 'Ada'),
                                      ('tidak_ada', 'Tidak Ada')], string='Status Ijazah')
    no_seri_ijazah = fields.Char(string="Nomor Seri Ijazah")
    end_year= fields.Char(string="Tahun Keluar")
    tanggal_terima_ijazah = fields.Date(string="Tanggal Terima Ijazah")
    tanggal_terima_ijazah = fields.Date(string="Tanggal Terima Ijazah")

    family_ids = fields.One2many(comodel_name="hr.employee.family", string="Family", inverse_name="employee_id")
    sp_ids = fields.One2many(comodel_name="hr.employee.sp", string="Surat Peringatan", inverse_name="employee_id")
    education_formal_ids = fields.One2many(comodel_name="hr.employee.education.formal", string="Education Formal", inverse_name="employee_id")
    education_nonformal_ids = fields.One2many(comodel_name="hr.employee.education.nonformal", string="Education Nonformal", inverse_name="employee_id")
    organization_ids = fields.One2many(comodel_name="hr.employee.organization", string="Organization", inverse_name="employee_id")
    skill_ids = fields.One2many(comodel_name="hr.employee.skills", string="Skills", inverse_name="employee_id")
    work_ids = fields.One2many(comodel_name="hr.employee.work", string="Work", inverse_name="employee_id")
    scholarship_ids = fields.One2many(comodel_name="hr.employee.scholarship", string="Beasiswa", inverse_name="employee_id")
    level_id = fields.Many2one("hr.job.level","Job Level")
    status_karyawan =fields.Many2one("hr.contract.type","Status Karyawan")

    _sql_constraints = [
        ('unique_nik', 'unique(nik)', 'NIK sudah pernah digunakan employee lain !'),
        ('unique_identification_id', 'unique(identification_id)', 'KTP sudah pernah digunakan employee lain !')
    ]

    #sequence for nik
    # @api.model
    # def create(self, vals):
    #     # import pdb;pdb.set_trace()
    #     if 'nik' in vals :
    #         if not vals['nik']:

    #             first_date_of_the_month = datetime.datetime.now().strftime('%Y-%m-1')
    #             date_now = datetime.datetime.now().date()

    #             month   =   datetime.datetime.now().strftime("%m")
    #             year    =   datetime.datetime.now().strftime("%Y")
    #             cr = self.env.cr

    #             cr.execute("SELECT max(nik) FROM hr_employee")
    #             niklist = cr.fetchall()
    #             if niklist[0][0] is not None and first_date_of_the_month != date_now:
    #                 for n in niklist:
    #                     result = n[0]

    #                     sequence = str(int(result[6:])+1).zfill(4) #increment
    #                     nik = '%s%s%s' % (year,month,sequence)
    #                     vals['nik'] = nik
    #             else:
    #                 number = 1
    #                 string_number = str(number)
    #                 sequence = string_number.zfill(4)
    #                 nik = '%s%s%s' % (year,month,sequence)
    #                 vals['nik'] = nik

    #         return super(Hr_employee, self).create(vals)

    #check for id_number employee if already exist
    @api.onchange('identification_id')
    def _check_user_id(self):
        id_employee = self.identification_id
        if id_employee:
            id_exist  = self.env['hr.employee'].search([('identification_id','=',id_employee)])
            for x in id_exist:
                if x.identification_id == id_employee:
                    warning_mess = {
                        'title': _('Warning!'),
                        'message' : _('Nomor identitas %s sudah pernah di inputkan') % \
                            (self.identification_id)
                    }
                    return {'warning': warning_mess}
        return {}