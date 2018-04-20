# -*- coding: utf-8 -*-
{
    'name': 'Autocomplete Google Maps',
    'version': '1.2',
    'author': "Jesus Garcia",
    'maintainer': 'Jesus Garcia<jgmanzanas@visiotechsecurity.com>',
    'category': 'web',
    'description': """
Google places autocomplete address form
==========================================================

This module brings three features:
1. Enabled google places autocomplete address form into partner
form view, it provide autocomplete feature when you typed an address of partner
""",
    'depends': [
        'web',
        'website_google_map'
    ],
    'website': '',
    'data': [
        'views/google_places_template.xml',
        'views/res_partner.xml',
        'views/res_config_view.xml'
    ],
    'demo': [],
    'qweb': ['static/xml/widget_places.xml'],
    'installable': True
}
