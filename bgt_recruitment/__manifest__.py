{
	"name": "BGT Recruitment",
	"version": "1.3",
	"depends": [
		"base",
		"hr",
		"hr_contract",
		"hr_recruitment",
		"website_hr_recruitment",
	],
	"author": "Bridgetech",
	"category": "Extra",
	'website': 'http://www.bridgetech.com',
	"description": """\



""",
	"data": [
		"views/hr_applicant.xml",
		"views/website_recruitment_templates.xml",
        "data/config_data.xml",
        "security/ir.model.access.csv",

	],
	"update_xml": [
        "security/group.xml",
    ],
	"installable": True,
	"auto_install": False,
    "application": True,
}
