from odoo import api, fields, models
from transliterate import translit
from transliterate.discover import autodiscover
from transliterate.base import TranslitLanguagePack, registry
from transliterate import detect_language
import re

class Bibles(models.Model):
    _name = "openbiblica.bible"
    _description = "Bible Project"
    _order = "name"

    name = fields.Char(string="Bible Project Name", required=True)
    description = fields.Text('Description')
    lang_id = fields.Many2one('openbiblica.lang', 'Language', required=True)
    create_id = fields.Many2one('res.users', string='Author', required=True)
    team_ids = fields.Many2many('res.users', 'dictionary_bible_rel', 'uid', 'bid', string='Team members')
    source_id = fields.Many2one('openbiblica.bible', 'Main Source')
    source_ids = fields.Many2many('openbiblica.bible', 'bible_source_ids_rel', 'source_id', 'derivative_id',
                                  string='Sources')
    book_ids = fields.One2many('openbiblica.book', 'bible_id', string='Books')
    default_dictionary_id = fields.Many2one('openbiblica.dictionary', 'Default Dictionary')

    is_installed = fields.Boolean(default=False)
    is_interlinear = fields.Boolean(default=False)

class Books(models.Model):
    _name = "openbiblica.book"
    _description = "Books"
    _order = "sequence"

    name = fields.Char(string="Book Name", required=True)
    description = fields.Text('Description')
    title_id = fields.Char(string="File Identifier")
    title_ide = fields.Char(string="Encoding specification")
    title = fields.Char(string="Content Title")
    title_short = fields.Char(string="Content Short")
    title_abrv = fields.Char(string="Content Abbreviation")
    sequence = fields.Integer('Sequence', required=True)

    lang_id = fields.Many2one(related='bible_id.lang_id')
    create_id = fields.Many2one('res.users', string='Author', required=True)
    team_ids = fields.Many2many(related='bible_id.team_ids')

    bible_id = fields.Many2one('openbiblica.bible', 'Bible Project')
    chapter_ids = fields.One2many('openbiblica.chapter', 'book_id', string='Book Chapters')

    source_id = fields.Many2one('openbiblica.book', 'Main Source')
    source_ids = fields.Many2many('openbiblica.book', 'book_source_ids_rel', 'source_id', 'derivative_id',
                                  string='Sources')
    dictionary_id = fields.Many2one('openbiblica.dictionary', 'Dictionary Source')
    default_dictionary_id = fields.Many2one(related='bible_id.default_dictionary_id')

    files = fields.Binary('File Attachment', attachment=True)
    rest = fields.Binary('Undone File Attachment', attachment=True)

    is_installed = fields.Boolean(default=False)
    is_interlinear = fields.Boolean(default=False)


class Chapters(models.Model):
    _name = "openbiblica.chapter"
    _description = "Chapters"
    _order = "sequence"

    name = fields.Char(string="Chapter Name", required=True)
    sequence = fields.Integer('Sequence', required=True)

    book_id = fields.Many2one('openbiblica.book', string='Book')
    bible_id = fields.Many2one(related='book_id.bible_id')
    verse_ids = fields.One2many('openbiblica.verse', 'chapter_id', string='Verse')
    create_id = fields.Many2one('res.users', string='Author')
    lang_id = fields.Many2one(related='bible_id.lang_id')

    source_id = fields.Many2one('openbiblica.chapter', 'Main Source')
    source_ids = fields.Many2many('openbiblica.chapter', 'chapter_source_ids_rel', 'source_id', 'derivative_id',
                                  string='Sources')
    is_interlinear = fields.Boolean(default=False)

class Verses(models.Model):
    _name = "openbiblica.verse"
    _description = "Verses"
    _order = "chapter, sequence"

    name = fields.Char(string="Verse Number")
    sequence = fields.Integer('Sequence', required=True)
    content = fields.Text('Content')

    chapter = fields.Char('Chapter')
    chapter_id = fields.Many2one('openbiblica.chapter', 'Chapter Id')
    book_id = fields.Many2one(related='chapter_id.book_id')
    bible_id = fields.Many2one(related='book_id.bible_id')
    create_id = fields.Many2one('res.users', string='Author')
    lang_id = fields.Many2one(related='bible_id.lang_id')

    source_id = fields.Many2one('openbiblica.verse', 'Main Source')
    source_ids = fields.Many2many('openbiblica.verse', 'verse_source_ids_rel', 'source_id', 'derivative_id',
                                  string='Sources')

    style = fields.Char('Style')
    align = fields.Char('Align')
    insert_paragraph = fields.Boolean('Insert paragraph tab')

    is_interlinear = fields.Boolean(default=False)
    is_mapped = fields.Boolean(default=False)

    def _transliterating(self):
        if self.lang_id.name == 'Greek':
            registry.register(GreekLanguagePack, force=True)
            transliteration = translit(self.content, 'el', reversed=True)
        elif self.lang_id.name == 'Hebrew':
            registry.register(HebrewLanguagePack, force=True)
            transliteration = translit(self.content, 'he', reversed=True)
        return transliteration

    def _interlinearing_verse(self):
        word_ids = []
        if self.lang_id.direction == 'rtl':
            words = self.content.split()
        else:
            words = re.findall(r'\w+|[\[\]??????()]|\S+', self.content)
        for word in words:
            word_id = self.env['openbiblica.word'].search([('name', '=', word), ('lang_id', '=', self.lang_id.id)])
            if not word_id:
                word_id = self.env['openbiblica.word'].create({
                    'name': word,
                    'lang_id': self.lang_id.id,
                })
            word_ids.append(word_id)
        return word_ids

class GreekLanguagePack(TranslitLanguagePack):
    _name = "openbiblica.GreekLanguagePack"
    language_code = "el"
    language_name = "Greek"
    mapping = (
        u"abgdezhiklmnxoprstyfwuABGDEZHIKLMNXOPRSTYFWU",
        u"????????????????????????????????????????????????????????????????????????????????????????",
    )
    reversed_specific_pre_processor_mapping = {
        u"??": u"A", u"??": u"a",    # ??, ??
        u"??": u"A", u"??": u"a",    # ??, ??
        u"??": u"B", u"??": u"b",    # ??, ??
        u"??": u"G", u"??": u"g",    # ??, ??
        u"??": u"D", u"??": u"d",    # ??, ??
        u"??": u"E", u"??": u"e",    # ??, ??
        u"??": u"Z", u"??": u"z",    # ??, ??
        u"??": u"I", u"??": u"i",    # ??, ??
        u"??": u"Th", u"??": u"th",  # ??, ??
        u"??": u"I", u"??": u"i",    # ??, ??
        u"??": u"K", u"??": u"k",    # ??, ??
        u"??": u"L", u"??": u"l",    # ??, ??
        u"??": u"M", u"??": u"m",    # ??, ??
        u"??": u"N", u"??": u"n",    # ??, ??
        u"??": u"X", u"??": u"x",    # ??, ??
        u"??": u"O", u"??": u"o",    # ??, ??
        u"??": u"P", u"??": u"p",    # ??, ??
        u"??": u"R", u"??": u"r",    # ??, ??
        u"??": u"S", u"??": u"s",    # ??, ??
        u"???": u"a",                    # ??
        u"???": u"a",                    # ??
        u"???": u"a",                    # ??
        u"???": u"a",                    # ??
        u"???": u"e",                    # ??
        u"???": u"e",                    # ??
        u"???": u"e",                    # ??
        u"??": u"s",                    # ??
        u"???": u"u",                    # ??
        u"???": u"u",                    # ??
        u"???": u"u",                    # ??
        u"???": u"o",                    # ??
        u"???": u"o",                    # ??
        u"???": u"o",                    # ??
        u"???": u"o",                    # ??
        u"???": u"o",                    # ??
        u"???": u"O",                    # ??
        u"???": u"i",                    # ??
        u"??": u"T", u"??": u"t",    # ??, ??
        u"??": u"Y", u"??": u"u",    # ??, ??
        u"??": u"Ch", u"??": u"ch",  # ??, ??
        u"??": u"Ps", u"??": u"ps",  # ??, ??
        u"??": u"O", u"??": u"o",    # ??, ??
        u"??": u"E", u"??": u"e",    # ??, ??
        u"??": u"I", u"??": u"i",    # ??, ??
        u"??": u"I", u"??": u"i",    # ??, ??
        u"??": u"O", u"??": u"o",    # ??, ??
        u"??": u"Y", u"??": u"u",    # ??, ??
        u"??": u"O", u"??": u"o",    # ??, ??
        u"??": u"I", u"??": u"i",    # ??, ??
        u"??": u"Y", u"??": u"u",    # ??, ??
        u"???": u"o", u"???": u"u",  # ??, ??
        u"???": u"o", u"???": u"u",  # ??, ??
        u"???": u"o", u"???": u"a",  # ??, ??
        u"???": u"e", u"???": u"e",  # ??, ??
        u"???": u"a", u"???": u"e",  # ??, ??
        u"???": u"a", u"???": u"e",  # ??, ??
        u"???": u"o", u"???": u"o",  # ??, ??
        u"???": u"o", u"???": u"e",  # ??, ??
        u"???": u"e", u"???": u"o",  # ??, ??
        u"???": u"i", u"???": u"i",  # ??, ??
        u"???": u"a", u"???": u"e",  # ??, ??
        u"???": u"a", u"???": u"o",  # ??, ??
        u"???": u"u", u"???": u"e",  # ??, ??
        u"???": u"e", u"???": u"e",  # ??, ??
        u"???": u"o", u"???": u"u",  # ??, ??
        u"???": u"o", u"???": u"u",  # ??, ??
        u"???": u"o", u"???": u"a",  # ??, ??
        u"???": u"r", u"???": u"o",  # ??, ??
        u"???": u"i", u"???": u"i",  # ??, ??
        u"???": u"i", u"???": u"e",  # ??, ??
        u"???": u"e", u"???": u"u",  # ??, ??
        u"???": u"e", u"???": u"a",  # ??, ??
        u"???": u"u", u"???": u"e",  # ??, ??
        u"???": u"u", u"???": u"i",  # ??, ??
        u"???": u"e", u"???": u"o",  # ??, ??
        u"???": u"e", u"???": u"o",  # ??, ??
    }


class HebrewLanguagePack(TranslitLanguagePack):
    _name = "openbiblica.HebrewLanguagePack"
    language_code = "he"
    language_name = "Hebrew"
    mapping = (
        u"a",
        u"??",
    )
    reversed_specific_pre_processor_mapping = {
        u"\u0027": u"",  # '

        # Consonants
        u"\u05D0": u"",  # ??
        u"\u05D1": u"V",  # ??
        u"\u05D1" + u"\u05BC": u"B",  # ????
        u"\uFB31": u"B",  # ????
        u"\u05D2": u"G",  # ??
        u"\u05D2" + u"\u05BC": u"G",  # ????
        u"\uFB32": u"G",  # ?????????
        u"\u05D2" + u"\u05F3": u"J",  # ????
        u"\u05D3": u"D",  # ??
        u"\u05D3" + u"\u05BC": u"D",  # ????
        u"\uFB33": u"D",  # ???
        u"\u05D3" + u"\u05F3": u"DH",  # ????
        u"\u05D4": u"H",  # ??
        u"\u05D4" + u"\u05BC": u"H",  # ????
        u"\uFB34": u"H",  # ????
        u"\u05D5": u"V",  # ?????
        u"\u05D5" + u"\u202C": u"V",  # ?????
        u"\u05D5" + u"\u05BC": u"V",  # ????
        # u"\uFB35":             u"V",  # ???  # To vowels u"U"
        u"\u05D6": u"Z",  # ??
        u"\u05D6" + u"\u05BC": u"Z",  # ????
        u"\uFB36": u"Z",  # ??????
        u"\u05D6" + u"\u05F3": u"ZH",  # ????
        u"\u05D7": u"CH",  # ??
        u"\u05D8": u"T",  # ??
        u"\u05D8" + u"\u05BC": u"T",  # ????
        u"\uFB38": u"T",  # ???
        u"\u05D9": u"Y",  # ??
        u"\u05D9" + u"\u05BC": u"Y",  # ????
        u"\u05D9" + u"\u05BC" +
        u"\u202C": u"Y",  # ???????
        u"\uFB39": u"Y",  # ??????
        u"\u05DB": u"CH",  # ??
        u"\u05DB" + u"\u05BC": u"CH",  # ????
        u"\u05DB" + u"\u05BC" +
        u"\u202C": u"CH",  # ????
        u"\uFB3B": u"C",  # ???
        u"\u05DA": u"CH",  # ??
        u"\u05DA" + u"\u05BC": u"CH",  # ????
        u"\u05DA" + u"\u05BC" +
        u"\u202C": u"CH",  # ???????
        u"\uFB3A": u"CH",  # ???
        u"\u05DC": u"L",  # ?????
        u"\u05DC" + u"\u05BC": u"L",  # ????
        u"\uFB3C": u"L",  # ???
        u"\u05DD": u"M",  # ??
        u"\u05DE": u"M",  # ?????
        u"\u05DE" + u"\u05BC": u"M",  # ????
        u"\uFB3E": u"M",  # ??????
        u"\u05DF": u"N",  # ??
        u"\u05E0": u"N",  # ??
        u"\u05E0" + u"\u05BC": u"N",  # ????
        u"\uFB40": u"N",  # ???
        u"\u05E1": u"S",  # ??
        u"\u05E1" + u"\u05BC": u"S",  # ????
        u"\uFB41": u"S",  # ???
        u"\u05E2": u"",  # ??
        u"\u05E3": u"F",  # ??
        u"\u05E3" + u"\u05BC": u"P",  # Possible problem u05BC # ????
        u"\uFB43": u"P",  # ???
        u"\u05E4": u"F",  # ?????
        u"\u05E4" + u"\u05BC": u"P",  # ????
        u"\uFB44": u"P",  # ???
        u"\u05E5": u"TZ",  # ??
        u"\u05E5" + u"\u05F3": u"TSH",  # Possible problem u05F3  # ????
        u"\u05E6": u"TZ",  # ?????
        u"\u05E6" + u"\u05BC": u"TZ",  # ????
        u"\uFB46": u"TZ",  # ??????
        u"\u05E6" + u"\u05F3": u"TSH",  # Possible problem u05F3  # ????
        u"\u05E7": u"Q",  # ??
        u"\u05E7" + u"\u05BC": u"Q",  # ????
        u"\uFB47": u"Q",  # ??????
        u"\u05E8": u"R",  # ??
        u"\u05E8" + u"\u05BC": u"R",  # ????
        u"\uFB48": u"R",  # ???
        u"\u05E9": u"S",  # ??
        u"\u05E9" + u"\u05BC": u"S",  # ????
        u"\uFB49": u"S",  # ??????
        u"\u05E9" + u"\u05C2" +
        u"\u202C": u"S",  # ????
        u"\uFB2B": u"S",  # ???
        u"\u05E9" + u"\u05C1": u"SH",  # ????
        u"\uFB2A": u"SH",  # ???
        u"\u05E9" + u"\u05BC" +
        u"\u05C2" + u"\u202C": u"S",  # ?????????
        u"\uFB2D": u"S",  # ???
        u"\u05EA": u"T",  # ??
        u"\u05EA" + u"\u05BC": u"T",  # ????
        u"\uFB4A": u"T",  # ???
        u"\u05EA" + u"\u05F3": u"T",  # ????

        # Niqqud vowels
        u"\u05B0": u"e",  # ( ????? )
        u"\u05B1": u"e",  # ( ?? )
        u"\u05B2": u"a",  # ( ?? )
        u"\u05B3": u"o",  # ( ?? )
        u"\u05B4": u"i",  # ( ?? )
        u"\u05B5": u"e",  # ( ?? )
        u"\u05B6": u"e",  # ( ?? )
        u"\u05B7": u"a",  # ( ?? )
        u"\u05B8": u"a",  # ( ?? ) # It could be u"A" too
        u"\u05B9": u"o",  # ( ?? )
        u"\u05BB": u"u",  # ( ?? )
        u"\u05D5" + u"\u05BC": u"u",  # ( ???? )
        u"\uFB35": u"u",  # ( ??? )

        u"\u05C3": u":",
        u"\u05C0": u"|",
        u"\u05be": u"-",
        u"\u05f3": u"'",
        u"\u05f4": u"\u0022",
        u"\u05C6": u";",

        u"\u05BD": u",",
        u"\u05BF": u"'",
        u"\u05C1": u"",
        u"\u05C2": u"h",
        u"\u05C4": u"'",
        u"\u05C5": u".",

        u"\u05F0": u"W",
        # u"\u05F1": u"vy",
        # u"\u05F2": u"yy",

        # Diphthongs
        u"\u05B5" + u"\u05D9": u"ei",  # ( ???? )
        u"\u05B6" + u"\u05D9": u"ei",  # ( ???? )
        u"\u05B7" + u"\u05D9": u"ai",  # ( ???? )
        u"\u05B7" + u"\u05D9" +
        u"\u05B0": u"ai",  # ( ?????? )
        u"\u05B7" + u"\u05D9" +
        u"\u05B0" + u"\u202C": u"ai",  # ( ????????? )
        u"\u05B8" + u"\u05D9": u"ai",  # ( ???? )
        u"\u05B8" + u"\u05D9" +
        u"\u202C": u"ai",  # ( ??????? )
        u"\u05B8" + u"\u05D9" +
        u"\u05B0": u"ai",  # ( ?????? )
        u"\u05B8" + u"\u05D9" +
        u"\u05B0" + u"\u202C": u"ai",  # ( ????????? )
        u"\u05B9" + u"\u05D9": u"oi",  # ( ???? )
        u"\u05B9" + u"\u05D9" +
        u"\u05B0": u"oi",  # ( ?????? )
        u"\u05B9" + u"\u05D9" +
        u"\u05B0" + u"\u202C": u"oi",  # ( ????????? )
        u"\u05BB" + u"\u05D9": u"ui",  # ( ???? )
        u"\u05BB" + u"\u05D9" +
        u"\u05B0": u"ui",  # ( ?????? )
        u"\u05BB" + u"\u05D9" +
        u"\u05B0" + u"\u202C": u"ui",  # ( ????????? )
        u"\u05D5" + u"\u05BC" +
        u"\u05D9": u"ui",  # ( ?????? )
        u"\u05D5" + u"\u05BC" +
        u"\u05D9" + u"\u05B0": u"ui",  # ( ???????? )
        u"\u05D5" + u"\u05BC" +
        u"\u05D9" + u"\u05B0" +
        u"\u202C": u"ui",  # ( ??????????? )
    }

