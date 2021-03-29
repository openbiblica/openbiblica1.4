import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers
import werkzeug.utils
import base64

from odoo import http, SUPERUSER_ID
from odoo.http import request


#test comment

class WebsiteBiblicaAjax(http.Controller):

    @http.route(['/download/<int:book_id>'], type='http', auth="public", website=True)
    def download_file(self, book_id=0):
        status, headers, content = request.env['ir.http'].sudo().binary_content(
            model='openbiblica.book', id=book_id, field='files')
        if status == 304:
            response = werkzeug.wrappers.Response(status=status, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200:
            response = request.not_found()
        else:
            filename = request.env['openbiblica.book'].sudo().search([('id', '=', book_id)]).name
            content_base64 = base64.b64decode(content)
            name = [('Content-Disposition', 'attachment; filename=' + filename + '.usfm;')]
            response = request.make_response(content_base64, name)
        return response

    @http.route(['/get/langs'], type='json', auth="public", website=True)
    def langs_data(self):
        bibs = request.env['openbiblica.bible'].sudo().search([])
        lngs = request.env['openbiblica.lang'].sudo().search([('id', 'in', bibs.mapped('lang_id.id'))])
        vals = [{'id': lang.id, 'name': lang.name} for lang in lngs]
        return vals

    @http.route(['/get/bibles'], type='json', auth="public", methods=['POST'], website=True)
    def bibles_data(self, **kwargs):
        if not kwargs.get('lang_id'):
            return None
        bibs = request.env['openbiblica.bible'].sudo().search([('lang_id', '=', int(kwargs.get('lang_id')))])
        vals = [{'id': bible.id, 'name': bible.name} for bible in bibs]
        return vals

    @http.route(['/get/book'], type='json', auth="public", methods=['POST'], website=True)
    def books_data(self, **kwargs):
        if not kwargs.get('bible_id'):
            return None
        books = request.env['openbiblica.book'].sudo().search([('bible_id', '=', int(kwargs.get('bible_id')))])
        vals = [{'id': book.id, 'name': book.name} for book in books]
        return vals

    @http.route(['/get/chapter'], type='json', auth="public", methods=['POST'], website=True)
    def chapters_data(self, **kwargs):
        if not kwargs.get('book_id'):
            return None
        chapters = request.env['openbiblica.chapter'].sudo().search([('book_id', '=', int(kwargs.get('book_id')))])
        vals = []
        for chapter in chapters:
            vals += [{'id': chapter.id, 'name': chapter.name}]
        return vals

    @http.route(['/get/verse'], type='json', auth="public", methods=['POST'], website=True)
    def verses_data(self, **kwargs):
        if not kwargs.get('chapter_id'):
            return None
        verses = request.env['openbiblica.verse'].sudo().search([('chapter_id.id', '=', int(kwargs.get('chapter_id'))),
                                                         ('name', '!=', ' ')])
        vals = [{'id': verse.id, 'name': verse.name} for verse in verses]
        return vals

    @http.route(['/get/chapter'], type='json', auth="public", methods=['POST'], website=True)
    def chapters_data(self, **kwargs):
        if not kwargs.get('book_id'):
            return None
        chapters = request.env['openbiblica.chapter'].sudo().search([
            ('book_id.id', '=', int(kwargs.get('book_id')))])
        vals = [{'id': chapter.id, 'name': chapter.name} for chapter in chapters]
        return vals

    @http.route(['/add/chapter'], type='json', auth="user", methods=['POST'], website=True)
    def add_chapters(self, **kwargs):
        if not kwargs.get('book_id'):
            return
        user_id = request.env.user
        book_id = request.env['openbiblica.book'].sudo().search([("id", "=", int(kwargs.get('book_id')))])
        if book_id.create_id == user_id:
            seq = len(book_id.chapter_ids) + 1
            request.env['openbiblica.chapter'].sudo().create({
                'book_id': book_id.id,
                'create_id': user_id.id,
                'name': kwargs.get('name'),
                'sequence': seq,
                'forum_id': book_id.forum_id.id,
            })
        return

    @http.route(['/get/dictionary'], type='json', auth="public", methods=['POST'], website=True)
    def dictionary_data(self, **kwargs):
        word_id = request.env['openbiblica.word'].sudo().search([('id', '=', int(kwargs.get('word_id')))])
        meaning_ids = request.env['openbiblica.meaning'].sudo().search([
            ('id', 'in', word_id.meaning_ids.id),
            ('lang_id', '=', int(kwargs.get('lang_id')))
        ])
        # meaning_ids = word_id.meaning_ids.search([('lang_id', '=', int(kwargs.get('lang_id')))])
        vals = [{'name': dict_id.name} for dict_id in meaning_ids]
        return vals

    @http.route(['/add/dictionary'], type='json', auth="user", methods=['POST'], website=True)
    def add_dictionary(self, **kwargs):
        if not kwargs.get('meaning_id'):
            return
        word_id = request.env['openbiblica.word'].sudo().search([('id', '=', int(kwargs.get('word_id')))])
        lang_id = request.env['openbiblica.lang'].sudo().search([('id', '=', int(kwargs.get('lang_id')))])
        meaning = kwargs.get('meaning_id').lower()
        meaning_id = request.env['openbiblica.meaning'].sudo().search([
            ('name', '=', meaning), ("lang_id", "=", lang_id.id)])
        if not meaning_id:
            meaning_id = request.env['openbiblica.meaning'].create({
                'name': meaning,
                'lang_id': lang_id.id,
            })
        word_id.update({
            'meaning_ids': [(4, meaning_id.id)]
        })
        return

    @http.route(['/un_dict/<model("openbiblica.meaning"):meaning_id>/<model("openbiblica.word"):word_id>'], type='http', auth='user', website=True)
    def un_dictionary(self, meaning_id=0, word_id=0):
        word_id.update({
            'meaning_ids': [(3, meaning_id.id)]
        })
        return request.redirect(request.httprequest.referrer)

    @http.route(['/get/source_langs'], type='json', auth="public", website=True)
    def source_langs_data(self):
        dicts = request.env['openbiblica.dictionary'].sudo().search([])
        lngs = request.env['openbiblica.lang'].sudo().search([('id', 'in', dicts.mapped('source_lang_id.id'))])
        vals = [{'id': lang.id, 'name': lang.name} for lang in lngs]
        return vals

    @http.route(['/get/target_langs'], type='json', auth="public", website=True)
    def target_langs_data(self, **kwargs):
        if not kwargs.get('source_lang_id'):
            return None
        dicts = request.env['openbiblica.dictionary'].sudo().search([('source_lang_id', '=', int(kwargs.get('source_lang_id')))])
        lngs = request.env['openbiblica.lang'].sudo().search([('id', 'in', dicts.mapped('target_lang_id.id'))])
        vals = [{'id': lang.id, 'name': lang.name} for lang in lngs]
        return vals

    @http.route(['/get/dictionaries'], type='json', auth="public", website=True)
    def dictionaries_data(self, **kwargs):
        if not kwargs.get('source_lang_id'):
            return None
        if not kwargs.get('target_lang_id'):
            return None
        dicts = request.env['openbiblica.dictionary'].sudo().search([('source_lang_id', '=', int(kwargs.get('source_lang_id'))),
                                                                     ('target_lang_id', '=', int(kwargs.get('target_lang_id')))])
        vals = [{'id': d.id, 'name': d.name} for d in dicts]
        return vals

