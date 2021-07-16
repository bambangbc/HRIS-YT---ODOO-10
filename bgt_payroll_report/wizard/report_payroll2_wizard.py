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
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import xlsxwriter, base64, pytz, string, re
from cStringIO import StringIO
from datetime import datetime, timedelta
from pytz import timezone
from string import ascii_uppercase
import itertools
import xlwt


class HRPayrollReport2Wizard(models.TransientModel):
    _name = "hr.payroll.report2.wizard"


    date_to = fields.Date(string='Date', required=True,
         default=time.strftime('%Y-%m-25'))
    contract_type_id = fields.Many2one("hr.contract.type",string="Contract Type", required=True)
    level_id = fields.Many2one("hr.job.level",string="Job Level", required=True)
    bank = fields.Many2one("res.bank", "Payment Methode", required=True)
    department_ids = fields.Many2many("hr.department",string="Department")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    	], string='Payslip Status', default='done', required=True)

    @api.multi
    def query_report2(self):
    	payslip = self.env['hr.payslip']
    	payslipline = self.env['hr.payslip.line']
    	department = self.env['hr.department']
    	lines = self.env['hr.payroll.report2']
    	# hapus record existing
        self._cr.execute("DELETE FROM hr_payroll_report2")

    	date = self.date_to
    	type = self.contract_type_id.id 
    	level = self.level_id.id
    	bank = self.bank.id
    	state = self.state
    	if not self.department_ids :
    		depts = department.search([])
    	else :
    		depts = self.department_ids
    	sequence = 0
    	tunjangan = 0.0
    	lembur = 0.0
    	upah = 0.0
    	total = 0.0
    	for dep in depts :
	    	ovt = sum(payslipline.search([('code','ilike','OVT'),
	    								('slip_id.date_to','=',date),
	    								('slip_id.state','=',state),
	    								('slip_id.employee_id.level_id.id','=',level),
	    								('slip_id.contract_id.type_id.id','=',type),
	    								('slip_id.contract_id.department_id.id','=',dep.id),
	    								('slip_id.employee_id.bank_account_id.bank_id.id','=',bank)]).mapped('amount'))
	    	tj = sum(payslipline.search([('code','ilike','TJ'),
	    								('slip_id.date_to','=',date),
	    								('slip_id.state','=',state),
	    								('slip_id.employee_id.level_id.id','=',level),
	    								('slip_id.contract_id.type_id.id','=',type),
	    								('slip_id.contract_id.department_id.id','=',dep.id),
	    								('slip_id.employee_id.bank_account_id.bank_id.id','=',bank)]).mapped('amount'))
	    	net = sum(payslipline.search([('code','ilike','Net'),
	    								('slip_id.date_to','=',date),
	    								('slip_id.state','=',state),
	    								('slip_id.employee_id.level_id.id','=',level),
	    								('slip_id.contract_id.type_id.id','=',type),
	    								('slip_id.contract_id.department_id.id','=',dep.id),
	    								('slip_id.employee_id.bank_account_id.bank_id.id','=',bank)]).mapped('amount'))
	    	lines.create({'sequence' : sequence,
	    					'name' : dep.name,
	    					'bank' : bank,
	    					'contract_type_id' : type,
    						'department_id' : dep.id,
    						'level_id' :level,
    						'date_to' : date,
    						'tunjangan' : tj,
    						'lembur' : ovt,
    						'upah' : net - tj - ovt,
    						'total' : net})
    		sequence += 1
    		tunjangan += tj
    		lembur += ovt
    		upah += (net-tj-ovt)
    		total += net
    	if total == 0.0 :
    		raise UserError(_('Tidak ada data yang ditemukan !'))
    	lines.create({'sequence' : sequence,
	    					'name' : "TOTAL",
	    					'bank' : False,
	    					'contract_type_id' : False,
    						'department_id' : False,
    						'level_id' :False,
    						'date_to' : False,
    						'tunjangan' : tunjangan ,
    						'lembur' : lembur ,
    						'upah' : upah,
    						'total' : total})
    	return {
            'name' : _('Report '+self.bank.name+ ' Periode ' +str(date)),
            'view_type': 'form',
            'view_mode': 'tree',         
            'res_model': 'hr.payroll.report2',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'target': 'current',
            'domain' : "[]",
            'context': '{}',
            }

HRPayrollReport2Wizard()