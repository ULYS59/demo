# -*- coding: utf-8 -*-
{
	'name': 'AlloDoc',
	'version': '1.0.0',
	'category': 'Patient',
	'sequence': 1,
	'author': 'Maxime LEPILLIEZ',
	'summary': 'AlloDoc',
	'description': """
Model Patient
======================================

Use to manage Patient !
	""",
	'depends': ["base", "crm" ,"web_calendar", "google_calendar", "web", "calendar"],
	'data': [
	# 'security/test_security.xml',
	'security/ir.model.access.csv',
	'custom_res_partner_view.xml',
	'custom_calendar_view.xml',
	'views/allodoc_report.xml',
	'views/report_fds.xml',
# 	'static/src/xml/custom_quick_create_calendar.xml',
	],
#	'js': [
#		'static/src/js/x_cashier.js',
#	],
#	'css': [
#		'static/src/css/x_cashier.css',
#	],
# 	'qweb': [
# 		
# #		'static/src/xml/x_cashier.xml',
# 	],
	'installable': True,
	'application': True,
	'auto_install': False,
}
