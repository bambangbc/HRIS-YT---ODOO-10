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
    "name": "BGT Overtime",
    "version": "0.3",
    "category": "HR",
    "sequence": 20,
    "author": "Bridgetech",
    "website": "www.bridgetech.com",
    "license": "AGPL-3",
    "summary": "",
    "description": """
    * Tambah master perhitungan lembur (overtime type)
    * Tambah menu form lembur (overtime form)
    * Onchange department otomatis list employee muncul sesuai dengan dept yang sama
   
    """,
    "depends": ["hr",
                "resource",
                "hr_attendance",
                "bgt_catering"],
    "data":[
        "data/data.xml",
        "security/group.xml",
        "security/ir.model.access.csv",
        "views/hr_overtime_view.xml",
        "views/hr_attendance_view.xml",
        ],
    "installable": True,
    "application": True,
    "auto_install": False,
}

