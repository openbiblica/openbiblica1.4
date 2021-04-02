from odoo import api, fields, models

class Users(models.Model):
    _inherit = "res.users"

    allow_word_mapping = fields.Boolean(default=False)
    my_bible_ids = fields.One2many('openbiblica.bible', 'create_id', 'My Bible Projects')
    my_dictionary_ids = fields.One2many('openbiblica.dictionary','create_id', 'My Dictionary Projects')

    dictionary_team_ids = fields.Many2many('openbiblica.dictionary', 'dictionary_team_rel', 'did', 'uid', string='Dictionaries Team')
    bible_team_ids = fields.Many2many('openbiblica.bible', 'dictionary_bible_rel', 'bid', 'uid', string='Bible Team')






