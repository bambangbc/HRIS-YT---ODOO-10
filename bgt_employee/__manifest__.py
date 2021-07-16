{
	"name": "BGT Employee",
	"version": "1.4",
	"depends": [
		"base",
		"hr",
		"hr_contract",
		"hr_recruitment",
	],
	"author": "Bridgetech",
	"category": "Extra",
	'website': 'http://www.bridgetech.com',
	"description": """\

	* Standard Field & Master HR

""",
	"data": [
		"views/hr_employee.xml",
		#"views/hr_contract.xml",
		"views/configuration.xml",
		"views/hr_contract_type.xml",
		"security/ir.model.access.csv",
		"security/group.xml",
	],
	"installable": True,
	"auto_install": False,
    "application": True,
}
