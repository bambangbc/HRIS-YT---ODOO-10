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
    "name": "BGT Attendance",
    "version": "0.3",
    "category": "HR",
    "sequence": 20,
    "author": "Bridgetech",
    "website": "www.bridgetech.com",
    "license": "AGPL-3",
    "summary": "",
    "description": """
    * Penyesuaian data Attendance
    * Ada fungsi untuk kirim data dari finger untuk pengecekan data create/update

    """,
    "depends": [
        "base",
        "hr",
        "hr_attendance",
        "bgt_employee",
    ],
    "data": [
        "views/attendance_view.xml",
        "data/data.xml",
        "wizard/rekap_absen.xml",
        "views/hasil_report.xml",
    ],

    "demo": [
    ],

    "test": [
    ],

    "installable": True,
    "auto_install": False,
    "application": True,
}

