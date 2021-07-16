import time
import calendar
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from collections import OrderedDict

class laporan_rekap_absen_perorangan(models.Model):
    _name = "laporan.rekap.absen"

    name = fields.Many2one('hr.employee', 'Nama Karyawan')
    department_id = fields.Many2one('hr.department', 'Department')
    shift_id = fields.Many2one('resource.calendar', 'Shift')
    log_in = fields.Datetime('Log In')
    log_out = fields.Datetime('Log Out')