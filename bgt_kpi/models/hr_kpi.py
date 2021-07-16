# -*- coding: utf-8 -*-
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

import datetime
import logging
import re
import uuid
from urlparse import urljoin
from collections import Counter, OrderedDict
from itertools import product

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

from odoo.addons.website.models.website import slug

email_validator = re.compile(r"[^@]+@[^@]+\.[^@]+")
_logger = logging.getLogger(__name__)


class Survey(models.Model):

    _inherit = 'survey.survey'
    _description = 'Employee Survey'

    def _default_page_template(self):
        page = self.env['survey.page'].search([('survey_id', '=', False)])
        if page :
            return page

    title = fields.Text('Title', required=True, translate=True)
    contract_id = fields.Many2one('hr.contract','Employee', copy=False)
    default_page_ids = fields.Many2many('survey.page',string='Default Page', copy=False, default=_default_page_template)

    @api.onchange('contract_id')
    def onchange_contratc_id(self):
        for i in self:
            if i.contract_id:
                employee = 'Nama : '+i.contract_id.employee_id.name+'\n'
                nik = 'NIK : '+i.contract_id.employee_id.nik+'\n'
                jabatan = 'Jabatan : '+i.contract_id.employee_id.job_id.name+'\n'
                divisi = 'Divisi : '+i.contract_id.employee_id.department_id.name
                i.title = employee+nik+jabatan+divisi

    @api.multi
    def assign_template_page(self):
        self.ensure_one()
        for i in self:
            if not i.default_page_ids :
                raise UserError(_('Default template harus diisi !'))
            if i.page_ids:
                raise UserError(_('Pages and Questions not empty !'))
            for ix in i.default_page_ids :
                ix.copy({'survey_id' : i.id})
            return True


    @api.multi
    def unlink(self):
        for i in self:
            if i.stage_id.name != 'Draft' :
                raise UserError(_('Data yang bisa dihapus hanya yg berstatus draft'))
        return super(Survey, self).unlink()

Survey()


class SurveyPage(models.Model):
    _inherit = 'survey.page'

    survey_id = fields.Many2one('survey.survey', string='Survey', ondelete='cascade', required=False)

SurveyPage()