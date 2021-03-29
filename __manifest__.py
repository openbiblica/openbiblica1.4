# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Openbiblica',
    'version': '1.4',
    'category': 'Education',
    'description': "Bible Study and Translation Platform",
    'website': 'https://www.openbiblica.com',
    'summary': 'Study and translate bible',
    'sequence': 1,
    'author': 'Openbiblica',
    'depends': ['web', 'website'],
    'data': [
#        'security/note_security.xml',
        'security/ir.model.access.csv',
        'data/language_data.xml',
#        'menus/menu.xml',
        'views/dictionary_views.xml',
        'views/bible_views.xml',
        'web/portal_templates.xml',
        'web/bible_templates.xml',
        'web/book_templates.xml',
        'web/chapter_templates.xml',
        'web/installer_templates.xml',
        'web/verse_templates.xml',
        'web/dictionary_templates.xml',
        #        'views/note_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
