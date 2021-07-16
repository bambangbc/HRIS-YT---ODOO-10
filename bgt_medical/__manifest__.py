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
    "name": "BGT Medical",
    "version": "0.6",
    "category": "HR",
    "sequence": 20,
    "author": "Bridgetech",
    "website": "www.bridgetech.com",
    "license": "AGPL-3",
    "summary": "",
    "description": """
    * Form pengajuan berobat karyawan

    """,
    "depends": [
        "base",
        "hr",
        "bgt_employee"
    ],
    "data": [
        "views/medical_view.xml",
        "data/data.xml",
        "security/group.xml",
        "security/ir.model.access.csv",
        "reports/surat_untuk_dokter_report.xml",
        "reports/surat_untuk_perusahaan_report.xml",
        "reports/invoice_untuk_finance_report.xml",
        "reports/surat_untuk_perusahaan_dan_dokter_report.xml",
    ],

    "demo": [
    ],

    "test": [
    ],

    "installable": True,
    "auto_install": False,
    "application": True,
}
