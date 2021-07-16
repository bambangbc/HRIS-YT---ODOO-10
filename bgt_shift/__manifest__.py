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
    "name": "BGT Shift",
    "version": "0.6",
    "category": "HR",
    "sequence": 20,
    "author": "Bridgetech",
    "website": "www.bridgetech.com",
    "license": "AGPL-3",
    "summary": "",
    "description": """
    * Working schedule / jadwal kerja karyawan
    * Shift dan Non Shift
    * Rolling Shift menggunakan sistem manual diinput dan di approve
    * list employee muncul otomatis sesuai yg login

    """,
    "depends": [
        "base",
        "hr",
        "hr_attendance",
        "bgt_employee",
        "bgt_contract",
    ],
    "data": [
        "security/group.xml",
        "data/data.xml",
        "security/ir.model.access.csv",
        "views/hr_rolling_shift.xml",
        "views/hr_resource_calendar.xml",
        "views/hr_contract.xml",
        "views/hr_attendance_view.xml",

    ],

    "demo": [
    ],

    "test": [
    ],

    "installable": True,
    "auto_install": False,
    "application": True,
}

