from odoo import api, fields, models

class langs(models.Model):
    _name = "openbiblica.lang"
    _description = "Langs"

    name = fields.Char('Langs', required=True)
    allow_dictionary = fields.Boolean(default=False)
    dictionary_source_ids = fields.One2many('openbiblica.dictionary', 'source_lang_id', string='Source Dictionaries')
    dictionary_target_ids = fields.One2many('openbiblica.dictionary', 'target_lang_id', string='Target Dictionaries')
    bible_ids = fields.One2many('openbiblica.bible', 'lang_id', string='Bibles')
    direction = fields.Selection([('ltr', 'Left-to-Right'), ('rtl', 'Right-to-Left')], required=True, default='ltr')

    _sql_constraints = [(
        'unique_name',
        'unique(name)',
        'Lang name must be unique!'
    )]

