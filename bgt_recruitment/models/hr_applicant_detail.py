from odoo import api, fields, models, _
import datetime
from dateutil import relativedelta

class Hr_applicant_family(models.Model):
    _name = 'hr.applicant.family'

    family  = fields.Selection([('suami_istri', 'Istri / Suami'),
                                ('saudara_kandung', 'Saudara Kandung'),
                                ('ayah', 'Ayah'), 
                                ('ibu', 'Ibu'), 
                                ('anak1', 'Anak ke 1'),
                                ('anak2', 'Anak ke 2'),
                                ('anak3', 'Anak ke 3'),],string='Anggota Keluarga', required=True)
    name = fields.Char(string="Name", required=True)
    jenis_kelamin = fields.Selection([('l', 'Laki-Laki'), 
                                    ('p', 'Perempuan'),],  string='Jenis Kelamin', required=True)
    jenjang  = fields.Many2one(comodel_name="hr.recruitment.degree", string="Pendidikan")
    age = fields.Integer(string="Usia", required=True)
    address = fields.Char(string="Alamat", required=True)
    work = fields.Char(string="Pekerjaan", required=True)
    applicant_id = fields.Many2one(comodel_name="hr.applicant", string="applicant")


class Hr_applicant_education_formal(models.Model):
    _name = 'hr.applicant.education.formal'

    jenjang  = fields.Many2one(comodel_name="hr.recruitment.degree", string="Jenjang", required=True)
    name = fields.Char(string="Nama Sekolah", required=True)
    lokasi = fields.Char(string="Lokasi", required=True)
    jurusan = fields.Char(string="Jurusan", required=True)
    start_year = fields.Char(string="Tahun Masuk", required=True)
    end_year= fields.Char(string="Tahun Keluar", required=True)
    ipk = fields.Char(string="IPK")
    sertifikat = fields.Boolean(string="Sertifikat")
    applicant_id = fields.Many2one(comodel_name="hr.applicant", string="applicant")

class Hr_applicant_education_nonformal(models.Model):
    _name = 'hr.applicant.education.nonformal'

    name = fields.Char(string="Nama Lembaga Kursus / Training", required=True)
    lokasi = fields.Char(string="Lokasi", required=True)
    keterampilan = fields.Char(string="Keterampilan", required=True)
    tahun = fields.Char(string="Tahun", required=True)
    sertifikat = fields.Boolean(string="Sertifikat")
    keterangan = fields.Char(string="Keterangan", required=True)
    applicant_id = fields.Many2one(comodel_name="hr.applicant", string="applicant")

class Hr_applicant_organization(models.Model):
    _name = 'hr.applicant.organization'

    name = fields.Char(string="Nama Organisasi", required=True)
    jabatan = fields.Char(string="Jabatan", required=True)
    kegiatan = fields.Char(string="Kegiatan", required=True)
    usia = fields.Integer(string="Usia", required=True)
    periode = fields.Char(string="Periode", required=True)
    applicant_id = fields.Many2one(comodel_name="hr.applicant", string="applicant")

class Hr_applicant_work(models.Model):
    _name = 'hr.applicant.work'

    name = fields.Char(string="Nama Perusahaan", required=True)
    bidang = fields.Char(string="Bidang", required=True)
    alamat = fields.Char(string="Alamat Perusahaan", required=True)
    jabatan = fields.Char(string="Jabatan", required=True)
    deskripsi = fields.Char(string="Deskripsi Pekerjaan", required=True)
    periode = fields.Char(string="Periode", required=True)
    alasan_resign = fields.Char(string="Alasan Berhenti Bekerja", required=True)
    last_salary = fields.Float(string="Gaji Terakhir", required=True)
    sertifikat = fields.Boolean(string="Sertifikat", required=True)
    applicant_id = fields.Many2one(comodel_name="hr.applicant", string="applicant")


class Hr_applicant_scholarship(models.Model):
    _name = 'hr.applicant.scholarship'

    jenjang  = fields.Many2one(comodel_name="hr.recruitment.degree", string="Jenjang Pendidikan", required=True)
    lembaga = fields.Char(string="Lembaga Pemberi", required=True)
    tahun = fields.Char(string='Tahun', require=True)
    ikatan_dinas = fields.Char(string='Ikatan Dinas', required=True)
    applicant_id = fields.Many2one(comodel_name="hr.applicant")


class Hr_applicant_skills(models.Model):
    _name = 'hr.applicant.skills'

    jenis_keterampilan = fields.Selection([('work_skills', 'Work Skills'), 
                                           ('software_skills', 'Software Skills'), 
                                           ('languange_skills', 'Language Skills'),],string='Jenis Keterampilan', required=True)
    keterampilan = fields.Char(string="Keterampilan")
    applicant_id = fields.Many2one(comodel_name="hr.applicant", string="applicant", required=True)
