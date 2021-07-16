##############################################################################
#
#    Copyright (C) 2018 widianajuniar@gmail.com
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import calendar
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from collections import OrderedDict


class HRMutasi(models.Model):
    _inherit = "hr.mutasi"

    @api.multi
    def button_approve(self):
        res = super(HRMutasi, self).button_approve()
        now = str(datetime.now()+timedelta(hours=7))
        contract_type = self.contract_id.type_id
        new_contract_type = self.new_contract_id.type_id
        if contract_type != new_contract_type :
            if contract_type.name == 'Training' and new_contract_type.name == 'Harian' :
                kuota = (int(now[8:10])/12) * new_contract_type.kuota
                # close kuota per employee
                self.employee_id.kuota_ids.filtered(lambda x: x.is_active == True).write({"is_active" : False})
                self.env["hr.kuota"].create({"employee_id"  : self.employee_id.id,
                                            "date"          : now[:10],
                                            "total_kuota"   : int(kuota),
                                            "sisa_kuota"    : int(kuota),
                                            "is_active"     : True,})
            elif contract_type.name == 'Harian' and new_contract_type.name == 'Bulanan' :
                kuota_exist = self.employee_id.kuota_ids.filtered(lambda x: x.is_active == True)
                if kuota_exist :
                    kuota = kuota_exist[0].sisa_kuota
                    if kuota > new_contract_type.kuota :
                        kuota_exist[0].write({"is_active" : False})
                        self.env["hr.kuota"].create({"employee_id"  : self.employee_id.id,
                                                    "date"          : now[:10],
                                                    "total_kuota"   : new_contract_type.kuota,
                                                    "sisa_kuota"    : new_contract_type.kuota,
                                                    "is_active"     : True,})
                else :
                    self.env["hr.kuota"].create({"employee_id"      : self.employee_id.id,
                                                    "date"          : now[:10],
                                                    "total_kuota"   : new_contract_type.kuota,
                                                    "sisa_kuota"    : new_contract_type.kuota,
                                                    "is_active"     : True,})
        return res

HRMutasi()