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
{
    "name": "BGT Payroll Report",
    "version": "0.2",
    "category": "Payroll",
    "sequence": 20,
    "author": "Bridgetech",
    "website": "www.bridgetech.com",
    "license": "AGPL-3",
    "summary": "",
    "description": """
    * Report-report penyesuaian terkait payroll
    * query tunjangan didapat dari rule dengan kode (ilike) 'TJ'
    * query lembur didapat dari rule dengan kode (ilike) 'OVT'
    * query date didapat dari date end payslip

    """,
    "depends": [
        "base",
        "hr_payroll",
        "bgt_employee",
        "bgt_payroll",
    ],
    "data": [
        "wizard/report_payroll_wizard.xml",
        "wizard/report_payroll2_wizard.xml",
        "views/hr_payroll_report.xml",
        "security/ir.model.access.csv",
    ],

    "demo": [
    ],

    "test": [
    ],

    "installable": True,
    "auto_install": False,
    "application": True,
}

