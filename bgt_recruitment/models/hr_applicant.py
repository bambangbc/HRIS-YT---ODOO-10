from odoo import api, fields, models, _
import datetime
from dateutil import relativedelta

class Hr_applicant(models.Model):
    _name = 'hr.applicant'
    _inherit = 'hr.applicant'

    
    #additional field
    no_ktp = fields.Char(string="NIK KTP")
    gender = fields.Selection([('male', 'Laki-Laki'), 
                               ('female', 'Perempuan')], string='Jenis Kelamin')
    place_of_birth          =  fields.Char(string="Tempat Lahir")
    birthday                = fields.Date(string="Tanggal Lahir")
    alamat_domisili         = fields.Char(string="Alamat Domisili")
    alamat_ktp              = fields.Char(string="Alamat KTP")
    religion_id             = fields.Many2one(comodel_name="hr.religion", string='Agama')
    country_id              = fields.Many2one(string="Kewarganegaraan", comodel_name="res.country")
    anak_ke                 = fields.Char(string="Anak Ke")
    hobi                    = fields.Char(string="Hobi")
    marital                 = fields.Selection([('single', 'Belum Menikah'), 
                                                ('married', 'Menikah'),
                                                ('widow','Janda'),
                                                ('widower','Duda')], string='Marital Status')
    jumlah_anak             = fields.Char(string="jumlah Anak")
    type_id                 = fields.Many2one(comodel_name="hr.recruitment.degree", string="Pendidikan")        

    family_ids = fields.One2many(comodel_name="hr.applicant.family", string="Family", inverse_name="applicant_id")
    education_formal_ids = fields.One2many(comodel_name="hr.applicant.education.formal", string="Education Formal", inverse_name="applicant_id")
    education_nonformal_ids = fields.One2many(comodel_name="hr.applicant.education.nonformal", string="Education Nonformal", inverse_name="applicant_id")
    organization_ids = fields.One2many(comodel_name="hr.applicant.organization", string="Organization", inverse_name="applicant_id")
    skill_ids = fields.One2many(comodel_name="hr.applicant.skills", string="Skills", inverse_name="applicant_id")
    work_ids = fields.One2many(comodel_name="hr.applicant.work", string="Work", inverse_name="applicant_id")
    scholarship_ids = fields.One2many(comodel_name="hr.applicant.scholarship", string="Beasiswa", inverse_name="applicant_id")

    kelebihan = fields.Text(string="Uraikan Kelebihan diri Anda")
    kekurangan = fields.Text(string="Uraikan Kelemahan diri Anda")
    deskripsi_diri  = fields.Text(string="Deskripsikan diri anda")
    tujuan_bekerja  = fields.Text(string="Tujuan anda bekerja")
    alasan_memilih_perusahaan  = fields.Text(string="Mengapa Anda ingin bekerja di Perusahaan ini?")
    harapan_gaji  = fields.Char(string="Gaji yang diharapkan")
    harapan_fasilitas = fields.Text(string="Fasilitas yang diharapkan")
    work_date = fields.Date(string="Kapan Anda dapat mulai bekerja")
    bekerja_dibawah_tekanan = fields.Text(string="Bagaimana cara anda bekerja d ibawah tekanan?")
    lingkungan_yang_disukai = fields.Text(string="Lingkungan kerja seperti apa yang anda sukai?")
    bekerja_diluar_daerah = fields.Selection([('ya', 'Ya'), 
                                              ('tidak', 'Tidak')], string="Bersediakah Anda ditempatkan diluar daerah?")
    kontrak_2_tahun = fields.Selection([('ya', 'Ya'), 
                                        ('tidak', 'Tidak')], string="Bersedia jika dikontrak selama 2 tahun?")
    pekerjaan_yang_dilamar = fields.Char(string="Pilih pekerjaan yang dilamar (2 pilihan)")
    gambaran_diri = fields.Text(string="Gambarkan pekerjaan seperti apa pada posisi yang anda lamar")
    pernah_kecelakaan = fields.Selection([('ya', 'Ya'), 
                                          ('tidak', 'Tidak')], string="Pernah Mengalami Kecelakaan")
    tahun_kecelakaan = fields.Char(string="Tahun Kecelakaan")
    pernah_dirawat_di_rumahsakit = fields.Selection([('ya', 'Ya'), 
                                                     ('tidak', 'Tidak')], string="Pernah Dirawat di Rumahsakit")
    tahun_dirawat_di_rumahsakit = fields.Char(string="Tahun Dirawat")
    penyebab_dirawat_di_rumahsakit = fields.Char(string="Penyebab")

    _sql_constraints = [
        ('unique_no_ktp', 'unique(no_ktp)', 'NIK KTP sudah pernah digunakan pelamar lain !')
    ]

    @api.multi
    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        employee = False
        for applicant in self:
            #create partner
            data = {
                'name': applicant.partner_name,
                'company_type':'person',
                'is_company': False,
                'street':applicant.alamat_domisili,
                'street2':applicant.alamat_ktp,
                'phone':applicant.partner_phone,
                'mobile':applicant.partner_mobile,
                'email':applicant.email_from,
            }
            partner = self.env['res.partner'].create(data)

            appl = self.env['hr.applicant'].search([('id','=',applicant.id)])
            appl.write({'partner_id': partner.id})

            address_id = contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.name_get()[0][1]
                        
                applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                employee = self.env['hr.employee'].create({'name': applicant.partner_name or contact_name,
                                               'job_id': applicant.job_id.id,
                                               'department_id': applicant.department_id.id or False,
                                               'address_id': applicant.company_id and applicant.company_id.partner_id and applicant.company_id.partner_id.id or False,
                                               'work_email': applicant.department_id and applicant.department_id.company_id and applicant.department_id.company_id.email or False,
                                               'work_phone': applicant.department_id and applicant.department_id.company_id and applicant.department_id.company_id.phone or False,
                                               'identification_id':applicant.no_ktp,
                                               'religion_id':applicant.religion_id.id,
                                               'place_of_birth':applicant.place_of_birth,
                                               'birthday':applicant.birthday,
                                               'gender':applicant.gender,
                                               'marital': applicant.marital,
                                               'children': applicant.jumlah_anak,
                                               'address_home_id':partner.id,
                                               'jenjang':applicant.type_id.id,
                                               'nik':False,
                                               'no_telepon':applicant.partner_phone,
                                               'no_hp':applicant.partner_mobile,
                                               'email':applicant.email_from,
                                               'country_id':applicant.country_id.id,
                                               'alamat_ktp':applicant.alamat_ktp,
                                               'alamat_domisili':applicant.alamat_domisili,
                                               })
                applicant.write({'emp_id': employee.id})

                if applicant.family_ids:
                    for fam in applicant.family_ids:
                        family={
                            'employee_id':employee.id,
                            'family':fam.family,
                            'name':fam.name,
                            'jenis_kelamin':fam.jenis_kelamin,
                            'jenjang':fam.jenjang.id,
                            'age':fam.age,
                            'address':fam.address,
                            'work':fam.work,}
                        self.env['hr.employee.family'].create(family)

                if applicant.education_formal_ids:
                    for eduf in applicant.education_formal_ids:
                        educationf={
                            'employee_id':employee.id,
                            'jenjang':eduf.jenjang.id,
                            'name':eduf.name,
                            'lokasi':eduf.lokasi,
                            'jurusan':eduf.jurusan,
                            'start_year':eduf.start_year,
                            'end_year':eduf.end_year,
                            'ipk':eduf.ipk,
                            'sertifikat':eduf.sertifikat,}
                        self.env['hr.employee.education.formal'].create(educationf)

                if applicant.education_nonformal_ids:
                    for edun in applicant.education_nonformal_ids:
                        educationn={
                            'employee_id':employee.id,
                            'name':edun.name,
                            'lokasi':edun.lokasi,
                            'keterampilan':edun.keterampilan,
                            'tahun':edun.tahun,
                            'sertifikat':edun.sertifikat,
                            'keterangan':edun.keterangan,}
                        self.env['hr.employee.education.nonformal'].create(educationn)

                if applicant.organization_ids:
                    for org in applicant.organization_ids:
                        organization={
                            'employee_id':employee.id,
                            'name':org.name,
                            'jabatan':org.jabatan,
                            'kegiatan':org.kegiatan,
                            'usia':org.usia,
                            'periode':org.periode,}
                        self.env['hr.employee.organization'].create(organization)

                if applicant.work_ids:
                    for wo in applicant.work_ids:
                        work={
                            'employee_id':employee.id,
                            'name':wo.name,
                            'bidang':wo.bidang,
                            'alamat':wo.alamat,
                            'jabatan':wo.jabatan,
                            'deskripsi':wo.deskripsi,
                            'periode':wo.periode,
                            'alasan_resign':wo.alasan_resign,
                            'last_salary':wo.last_salary,
                            'sertifikat':wo.sertifikat,
                            }
                        self.env['hr.employee.work'].create(work)

                if applicant.scholarship_ids:
                    for sc in applicant.scholarship_ids:
                        scholarship={
                            'employee_id':employee.id,
                            'jenjang':sc.jenjang.id,
                            'lembaga':sc.lembaga,
                            'tahun':sc.tahun,
                            'ikatan_dinas':sc.ikatan_dinas,}
                        self.env['hr.employee.scholarship'].create(scholarship)
                 

                if applicant.skill_ids:
                    for skill in applicant.skill_ids:
                        skills={
                            'employee_id':employee.id,
                            'jenis_keterampilan':skill.jenis_keterampilan,
                            'keterampilan':skill.keterampilan,}
                        self.env['hr.employee.skills'].create(skills)

                applicant.job_id.message_post(
                    body=_('New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
                employee._broadcast_welcome()
            else:
                raise UserError(_('You must define an Applied Job and a Contact Name for this applicant.'))

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        if employee:
            dict_act_window['res_id'] = employee.id
        dict_act_window['view_mode'] = 'form,tree'
        return dict_act_window