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
    "name": "BGT Koperasi",
    "version": "0.5",
    "category": "HR",
    "sequence": 20,
    "author": "Bridgetech",
    "website": "www.bridgetech.com",
    "license": "AGPL-3",
    "summary": "",
    "description": """
    * Tambah menu koperasi
    * Pengajuan dana koperasi karyawan yang dipotong dari payroll
    * Rekapitulasi mutasi pinjaman dan simpanan koperasi
    * print slip koperasi per employee

    """,
    "depends": ["base",
                "hr",
                "hr_payroll",
                "bgt_employee"],
    "data":[
        "security/group.xml",
        "security/ir.model.access.csv",
        "data/data.xml",
        "wizard/print_slip.xml",
        "wizard/rekapitulasi_wizard.xml",
        "wizard/generate_bunga.xml",
        "views/menu.xml",
        "views/hr_koperasi_view.xml",
        "views/hr_payslip.xml",
        "views/hr_contract_view.xml",
        "report/tanda_terima_koperasi.xml",
        "report/tanda_terima_bpkb.xml",
        "report/telah_dikembalikan_bpkb.xml",
        ],
    "demo": [],
    "test": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}