# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers
import werkzeug.utils
import logging
import base64
import json
import re

from odoo import http, modules, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WebsiteBiblica(http.Controller):
    _items_per_page = 20
    _comment_per_page = 5
    _verse_per_page = 10
    
    @http.route('/bibles', type='http', auth="public", website=True, csrf=False)
    def biblicas(self):
        values = {
            'biblicas': request.env['openbiblica.bible'].sudo().search([]),
        }
        return request.render("openbiblica.biblicas", values)

    @http.route('/create/bible', type='http', auth="user", website=True)
    def create_biblica(self):
        values = {
            'langs': request.env['openbiblica.lang'].sudo().search([]),
        }
        return request.render("openbiblica.bible_editor", values)

    @http.route(['/save/bible'], type='http', auth="user", methods=['POST'], website=True)
    def save_biblica(self, **kwargs):
        user_id = request.env.user
        if kwargs.get('lang_name'):
            lang_id = request.env['openbiblica.lang'].search([("name", "=", kwargs.get('lang_name'))])
            if not lang_id:
                lang_id = request.env['openbiblica.lang'].create({
                    'name': kwargs.get('lang_name'),
                    'direction': kwargs.get('direction'),
                })
        elif kwargs.get('lang_id'):
            lang_id = request.env['openbiblica.lang'].search([("id", "=", kwargs.get('lang_id'))])
        else:
            return request.redirect(request.httprequest.referrer)
        if kwargs.get('bible_id'):
            bible_id = request.env['openbiblica.bible'].search([("id", "=", kwargs.get('bible_id'))])
            if bible_id.create_id != user_id:
                return request.redirect('/my/home')
            bible_id.update({
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'lang_id': lang_id.id,
            })
        else:
            bible_id = request.env['openbiblica.bible'].sudo().create({
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'create_id': user_id.id,
                'lang_id': lang_id.id,
            })
        return request.redirect('/bible/%s' % slug(bible_id))

    @http.route('/edit/bible', type='http', auth="user", website=True)
    def edit_biblica(self, **kwargs):
        bible_id = request.env['openbiblica.bible'].search([("id", "=", kwargs.get('bible_id'))])
        if bible_id.create_id == request.env.user or request.env.user in bible_id.team_ids:
            values = {
                'bible_id': bible_id,
                'langs': request.env['openbiblica.lang'].sudo().search([]),
            }
            return request.render("openbiblica.bible_editor", values)
        else:
            return request.redirect(request.httprequest.referrer)

    @http.route(['/remove/bible/<model("openbiblica.bible"):bible_id>'], type='http', auth='user', website=True)
    def remove_biblica(self, bible_id=0):
        if bible_id.create_id == request.env.user:
            while bible_id.book_ids:
                book_id = request.env['openbiblica.book'].search([('bible_id', '=', bible_id.id)])[0]
                if not book_id.chapter_ids:
                    book_id.files = None
                    book_id.unlink()
                    continue
                values = {
                    'chapter_id': book_id.chapter_ids[0].id,
                    'bible_id': bible_id.id,
                }
                return request.render("openbiblica.remove", values)
            bible_id.unlink()
            return request.redirect('/my/home')
        return request.redirect('/')

    @http.route(['/bible/<model("openbiblica.bible"):bible_id>',
                 '/bible/<model("openbiblica.bible"):bible_id>/page/<int:page>'],
                type='http', auth="public", website=True, csrf=False)
    def view_biblica(self, bible_id=0, page=1):
        values = {}
        values.update({
            'user_id': request.env.user,
            'bible_id': bible_id,
        })
        return request.render("openbiblica.view_biblica", values)

    @http.route(['/add/book'], type='http', auth="user", website=True)
    def add_book(self, **kwargs):
        bible_id = request.env['openbiblica.bible'].sudo().search([('id', '=', kwargs.get('bible_id'))])
        if bible_id.create_id == request.env.user or request.env.user in bible_id.team_ids:
            books = request.env['openbiblica.book'].sudo().search([('bible_id', '=', bible_id.id)])
            sequence = len(books) + 1
            values = {
                'bible_id': bible_id,
                'sequence': sequence,
                'name': kwargs.get('name'),
            }
            return request.render("openbiblica.book_form", values)
        else:
            return request.redirect(request.httprequest.referrer)

    @http.route(['/save/book'], type='http', auth="user", website=True)
    def save_book(self, **kwargs):
        bible_id = request.env['openbiblica.bible'].sudo().search([('id', '=', kwargs.get('bible_id'))])
        user_id = request.env.user
        if bible_id.create_id == user_id or user_id in bible_id.team_ids:
            if kwargs.get('book_id'):
                book_id = request.env['openbiblica.book'].sudo().search([('id', '=', kwargs.get('book_id'))])
                book_id.update({
                    'name': kwargs.get('name'),
                    'description': kwargs.get('description'),
                    'title_id': kwargs.get('title_id'),
                    'title_ide': kwargs.get('title_ide'),
                    'title': kwargs.get('title'),
                    'title_short': kwargs.get('title_short'),
                    'title_abrv': kwargs.get('title_abrv'),
                    'source_id': kwargs.get('source_book_id'),
                    'dictionary_id': kwargs.get('dictionary_id'),
                })
            else:
                book_id = request.env['openbiblica.book'].sudo().create({
                    'name': kwargs.get('name'),
                    'description': kwargs.get('description'),
                    'title_id': kwargs.get('title_id'),
                    'title_ide': kwargs.get('title_ide'),
                    'title': kwargs.get('title'),
                    'title_short': kwargs.get('title_short'),
                    'title_abrv': kwargs.get('title_abrv'),
                    'source_id': kwargs.get('source_book_id'),
                    'dictionary_id': kwargs.get('dictionary_id'),
                    'sequence': kwargs.get('sequence'),
                    'create_id': user_id.id,
                    'bible_id': bible_id.id,
                })
            if book_id.files:
                book_id.files = None
            if kwargs.get('files'):
                files = kwargs.get('files').read()
                book_id.update({
                    'files': base64.b64encode(files)
                })
            return request.redirect('/book/%s' % slug(book_id))
        else:
            return request.redirect('/bible/%s' % slug(bible_id))

    @http.route(['/up/book/<model("openbiblica.book"):book_id>'], type='http', auth="user", website=True)
    def up_book(self, book_id=0):
        bible_id = book_id.bible_id
        if book_id.create_id == request.env.user or request.env.user in book_id.bible_id.team_ids:
            if book_id.sequence != 1:
                seq = book_id.sequence
                pseq = seq - 1
                prev = request.env['openbiblica.book'].sudo().search(
                    [('bible_id', '=', bible_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                book_id.update({'sequence': pseq})
        return request.redirect('/bible/%s' % slug(bible_id))

    @http.route(['/down/book/<model("openbiblica.book"):book_id>'], type='http', auth="user", website=True)
    def down_book(self, book_id=0):
        bible_id = book_id.bible_id
        if book_id.create_id == request.env.user or request.env.user in book_id.bible_id.team_ids:
            if book_id.sequence != len(bible_id.book_ids):
                seq = book_id.sequence
                pseq = seq + 1
                prev = request.env['openbiblica.book'].sudo().search(
                    [('bible_id', '=', bible_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                book_id.update({'sequence': pseq})
        return request.redirect('/bible/%s' % slug(bible_id))

    @http.route(['/edit/book/<model("openbiblica.book"):book_id>'], type='http', auth="user", website=True)
    def edit_book(self, book_id=0):
        bible_id = book_id.bible_id
        if book_id.create_id == request.env.user or request.env.user in book_id.bible_id.team_ids:
            values = {
                'book_id': book_id,
                'bible_id': bible_id,
            }
            return request.render("openbiblica.book_form", values)
        return request.redirect('/bible/%s' % slug(bible_id))

    @http.route(['/remove/book/<model("openbiblica.book"):book_id>'], type='http', auth="user", website=True)
    def remove_book(self, book_id=0):
        if book_id.create_id == request.env.user or request.env.user in book_id.bible_id.team_ids:
            bible_id = book_id.bible_id
            seq = book_id.sequence
            next_books = request.env['openbiblica.book'].search(
                [('bible_id', '=', bible_id.id), ('sequence', '>', seq)])
            for book in next_books:
                nseq = book.sequence - 1
                book.update({'sequence': nseq})
            if book_id.chapter_ids:
                values = {
                    'chapter_id': book_id.chapter_ids[0].id,
                }
                return request.render("openbiblica.remove", values)
            book_id.files = None
            book_id.unlink()
            return request.redirect('/bible/%s' % slug(bible_id))
        return request.redirect('/')

    @http.route(['/book/<model("openbiblica.book"):book_id>',
                 '/book/<model("openbiblica.book"):book_id>/page/<int:page>'],
                type='http', auth="public", website=True, csrf=False)
    def view_book(self, book_id=0, page=1):
        values = {}
        bible_id = book_id.bible_id

        seq = book_id.sequence
        prev_id = request.env['openbiblica.book'].sudo().search(
            [('bible_id', '=', bible_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['openbiblica.book'].sudo().search(
            [('bible_id', '=', bible_id.id), ('sequence', '=', seq + 1)])

        chapter_ids = request.env['openbiblica.chapter'].search([('book_id', '=', book_id.id)])

        values.update({
            'user_id': request.env.user,
            'book_id': book_id,
            'bible_id': bible_id,
            'chapter_ids': chapter_ids,
        })
        return request.render("openbiblica.view_book", values)

    @http.route(['/chapter/<model("openbiblica.chapter"):chapter_id>',
                 '/chapter/<model("openbiblica.chapter"):chapter_id>/<model("openbiblica.lang"):lg_id>',
                 '/chapter/<model("openbiblica.chapter"):chapter_id>/page/<int:page>',
                 '/chapter/<model("openbiblica.chapter"):chapter_id>/page/<int:page>/<model("openbiblica.lang"):lg_id>',
                 ], type='http', auth="public", website=True, csrf=False)
    def view_chapter(self, lg_id=None, chapter_id=0, page=1, **kwargs):
        seq = chapter_id.sequence
        prev_id = request.env['openbiblica.chapter'].sudo().search(
            [('book_id', '=', chapter_id.book_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['openbiblica.chapter'].sudo().search(
            [('book_id', '=', chapter_id.book_id.id), ('sequence', '=', seq + 1)])

        if kwargs.get('select_lang'):
            s_lang = request.env['openbiblica.lang'].sudo().search([('id', '=', kwargs.get('select_lang'))]).id
        elif lg_id:
            s_lang = lg_id.id
        else:
            if not chapter_id.source_id:
                s_lang = request.env['openbiblica.lang'].search([("name", "=", "English")]).id
            else:
                s_lang = chapter_id.lang_id.id

        if kwargs.get('select_source'):
            source = request.env['openbiblica.chapter'].sudo().search(
                [('book_id.id', '=', kwargs.get('select_source')), ('sequence', '=', seq)])
        else:
            source = chapter_id.source_id

        main_verses = request.env['openbiblica.verse']
        if source and len(source.verse_ids) > len(chapter_id.verse_ids):
            verse_domain = [('chapter_id', '=', source.id)]
        else:
            verse_domain = [('chapter_id', '=', chapter_id.id)]

        values = {}
        verse_url_args = {}
        verse_url = '/chapter/%s' % (slug(chapter_id))
        verse_total = main_verses.search_count(verse_domain)
        verse_pager = request.website.pager(
            url=verse_url,
            total=verse_total,
            page=page,
            step=self._verse_per_page,
            url_args=verse_url_args,
        )
        verse_results = main_verses.search(verse_domain, offset=(page - 1) * self._verse_per_page, limit=self._verse_per_page)

        values.update({
            'user_id': request.env.user,
            's_lang': s_lang,
            'langs': request.env['openbiblica.lang'].sudo().search([]),
            'source_id': source,
            'chapter_id': chapter_id,
            'book_id': chapter_id.book_id,
            'bible_id': chapter_id.bible_id,
            'prev_id': prev_id,
            'next_id': next_id,
            'verse_results': verse_results,
            'verse_pager': verse_pager,
            'verse_total': verse_total,
            'page': page,
        })
        return request.render("openbiblica.view_chapter", values)

    @http.route(['/add/chapter'], type='http', auth='user', website=True)
    def add_chapter(self, **kwargs):
        user_id = request.env.user
        book_id = request.env['openbiblica.book'].sudo().search([("id", "=", kwargs.get('book_id'))])
        if book_id.create_id == user_id or user_id in book_id.bible_id.team_ids:
            seq = len(book_id.chapter_ids) + 1
            chapter_id = request.env['openbiblica.chapter'].sudo().create({
                'name': kwargs.get('name'),
                'sequence': seq,
                'book_id': book_id.id,
            })
        return request.redirect(request.httprequest.referrer)

    @http.route(['/up/chapter/<model("openbiblica.chapter"):chapter_id>'], type='http', auth="user", website=True)
    def up_chapter(self, chapter_id=0):
        book_id = chapter_id.book_id
        if chapter_id.create_id == request.env.user or request.env.user in chapter_id.bible_id.team_ids:
            if chapter_id.sequence != 1:
                seq = chapter_id.sequence
                pseq = seq - 1
                prev = request.env['openbiblica.chapter'].sudo().search(
                    [('book_id', '=', book_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                chapter_id.update({'sequence': pseq})
        return request.redirect('/book/%s' % slug(book_id))

    @http.route(['/down/chapter/<model("openbiblica.chapter"):chapter_id>'], type='http', auth="user", website=True)
    def down_chapter(self, chapter_id=0):
        book_id = chapter_id.book_id
        if chapter_id.create_id == request.env.user or request.env.user in chapter_id.bible_id.team_ids:
            if chapter_id.sequence != len(book_id.chapter_ids):
                seq = chapter_id.sequence
                pseq = seq + 1
                prev = request.env['openbiblica.chapter'].sudo().search(
                    [('book_id', '=', book_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                chapter_id.update({'sequence': pseq})
        return request.redirect('/book/%s' % slug(book_id))

    @http.route(['/edit/chapter'], type='http', auth="user", website=True)
    def edit_chapter(self, **kwargs):
        chapter_id = request.env['openbiblica.chapter'].sudo().search([('id', '=', kwargs.get('chapter_id'))])
        book_id = chapter_id.book_id
        if chapter_id.create_id == request.env.user or request.env.user in chapter_id.bible_id.team_ids:
            chapter_id.update({
                'name': kwargs.get('name'),
            })
        return request.redirect('/book/%s' % slug(book_id))

    @http.route(['/remove/chapter/<model("openbiblica.chapter"):chapter_id>'], type='http', auth="user", website=True)
    def remove_chapter(self, chapter_id=0):
        book_id = chapter_id.book_id
        if chapter_id.create_id == request.env.user or request.env.user in chapter_id.bible_id.team_ids:
            seq = chapter_id.sequence
            next_chapters = request.env['openbiblica.chapter'].search(
                [('book_id', '=', book_id.id), ('sequence', '>', seq)])
            for chapter in next_chapters:
                nseq = chapter.sequence - 1
                chapter.update({'sequence': nseq})
            request.env['openbiblica.verse'].search([("chapter_id", "=", chapter_id.id)]).unlink()
            chapter_id.unlink()
        return request.redirect('/book/%s' % slug(book_id))

    @http.route(['/verse/<model("openbiblica.verse"):verse_id>',
                 '/verse/<model("openbiblica.verse"):verse_id>/<int:lang_id>',
                 ], type='http', auth="public", website=True, csrf=False)
    def view_verse(self, verse_id=0, page=1, lang_id=None, **kwargs):
        if kwargs.get('select_lang'):
            s_lang = request.env['openbiblica.lang'].sudo().search([('id', '=', kwargs.get('select_lang'))]).id
        elif lang_id:
            s_lang = lang_id
        else:
            if not verse_id.source_id:
                s_lang = request.env['openbiblica.lang'].search([("name", "=", "English")]).id
            else:
                s_lang = verse_id.lang_id.id

        seq = verse_id.sequence
        prev_id = request.env['openbiblica.verse'].sudo().search(
            [('chapter_id', '=', verse_id.chapter_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['openbiblica.verse'].sudo().search(
            [('chapter_id', '=', verse_id.chapter_id.id), ('sequence', '=', seq + 1)])

        if kwargs.get('select_source'):
            source = request.env['openbiblica.verse'].sudo().search([
                ('book_id.id', '=', kwargs.get('select_source')),
                ('chapter_id.sequence', '=', verse_id.chapter_id.sequence),
                ('sequence', '=', seq)])
        else:
            source = verse_id.source_id
        values = {}
        values.update({
            'user_id': request.env.user,
            's_lang': s_lang,
            'langs': request.env['openbiblica.lang'].sudo().search([]),
            'source_id': source,
            'verse_id': verse_id,
            'chapter_id': verse_id.chapter_id,
            'book_id': verse_id.book_id,
            'bible_id': verse_id.bible_id,
            'prev_id': prev_id,
            'next_id': next_id,
        })
        if verse_id.lang_id.allow_dictionary:
            values.update({
                'word_ids': verse_id._interlinearing_verse(),
            })
        if source.lang_id.allow_dictionary:
            values.update({
                's_word_ids': source._interlinearing_verse(),
            })
        return request.render("openbiblica.view_verse", values)

    @http.route(['/add/verse'], type='http', auth='user', website=True)
    def add_verse(self, **kwargs):
        user_id = request.env.user
        chapter_id = request.env['openbiblica.chapter'].sudo().search([("id", "=", kwargs.get('chapter_id'))])
        seq = len(chapter_id.verse_ids) + 1
        if chapter_id.create_id == user_id or user_id in chapter_id.bible_id.team_ids:
            verse_id = request.env['openbiblica.verse'].sudo().create({
                'content': kwargs.get('content'),
                'chapter': kwargs.get('chapter'),
                'name': kwargs.get('verse'),
                'sequence': seq,
                'chapter_id': chapter_id.id,
                'create_id': user_id.id,
            })
            if chapter_id.is_interlinear:
                self._interlinearing_verse(verse_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/up/verse/<model("openbiblica.verse"):verse_id>'], type='http', auth="user", website=True)
    def up_verse(self, verse_id=0):
        chapter_id = verse_id.chapter_id
        if verse_id.create_id == request.env.user or request.env.user in verse_id.bible_id.team_ids:
            if verse_id.sequence != 1:
                seq = verse_id.sequence
                pseq = seq - 1
                prev = request.env['openbiblica.verse'].sudo().search([('chapter_id', '=', chapter_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                verse_id.update({'sequence': pseq})
        return request.redirect('/chapter/%s' % slug(chapter_id))

    @http.route(['/down/verse/<model("openbiblica.verse"):verse_id>'], type='http', auth="user", website=True)
    def down_verse(self, verse_id=0):
        chapter_id = verse_id.chapter_id
        if verse_id.create_id == request.env.user or request.env.user in verse_id.bible_id.team_ids:
            if verse_id.sequence != len(chapter_id.verse_ids):
                seq = verse_id.sequence
                pseq = seq + 1
                prev = request.env['openbiblica.verse'].sudo().search([('chapter_id', '=', chapter_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                verse_id.update({'sequence': pseq})
        return request.redirect('/chapter/%s' % slug(chapter_id))

    @http.route(['/edit/verse'], type='http', auth="user", website=True)
    def edit_verse(self, **kwargs):
        verse_id = request.env['openbiblica.verse'].sudo().search([('id', '=', kwargs.get('verse_id'))])
        if verse_id.create_id == request.env.user or request.env.user in verse_id.bible_id.team_ids:
            verse_id.update({
                'content': kwargs.get('content'),
                'chapter': kwargs.get('chapter'),
                'name': kwargs.get('verse'),
            })
            if verse_id.is_interlinear:
                self._interlinearing_verse(verse_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/remove/verse/<model("openbiblica.verse"):verse_id>'], type='http', auth="user", website=True)
    def remove_verse(self, verse_id=0):
        chapter_id = verse_id.chapter_id
        if verse_id.create_id == request.env.user or request.env.user in verse_id.bible_id.team_ids:
            seq = verse_id.sequence
            next_verses = request.env['openbiblica.verse'].search([('chapter_id', '=', chapter_id.id), ('sequence', '>', seq)])
            for verse in next_verses:
                nseq = verse.sequence - 1
                verse.update({'sequence': nseq})
            verse_id.unlink()
        return request.redirect('/chapter/%s' % slug(chapter_id))

    @http.route(['/remove/p/'], type='json', auth="public", methods=['POST'], website=True)
    def remove_p(self, **kwargs):
        chapter_id = request.env['openbiblica.chapter'].search([('id', '=', int(kwargs.get('chapter_id')))])
        request.env['openbiblica.verse'].search([("chapter_id", "=", chapter_id.id)]).unlink()
        book_id = chapter_id.book_id
        chapter_id.unlink()

        while book_id.chapter_ids:
            vals = {
                'chapter_id': book_id.chapter_ids[0].id,
                'bible_id': kwargs.get('bible_id'),
            }
            return vals

        bible_id = book_id.bible_id
        book_id.files = None
        book_id.unlink()

        if not kwargs.get('bible_id'):
            vals = {
                'bible_id': bible_id.id,
            }
            return vals

        while bible_id.book_ids:
            book_id = request.env['openbiblica.book'].search([('bible_id', '=', bible_id.id)])[0]
            if not book_id.chapter_ids:
                book_id.files = None
                book_id.unlink()
                continue
            vals = {
                'chapter_id': book_id.chapter_ids[0].id,
                'bible_id': kwargs.get('bible_id'),
            }
            return vals

        bible_id.unlink()
        vals = {}
        return vals

    @http.route(['/search/',
                 '/search/word/<string:keyword>',
                 '/search/word/<string:keyword>/page/<int:page>',
                 '/search/bible/<model("openbiblica.bible"):bible_id>/word/<string:keyword>',
                 '/search/bible/<model("openbiblica.bible"):bible_id>/word/<string:keyword>/page/<int:page>',
                 '/search/page/<int:page>',
                 '/search/lang/<int:s_lang>',
                 ], type='http', auth="public", website=True, csrf=False)
    def search(self, page=1, keyword=None, sorting=None, s_lang=None, bible_id=0, **kwargs):
        if kwargs.get('keyword'):
            keyword = kwargs.get('keyword')

        if not s_lang:
            s_lang = request.env['openbiblica.lang'].search([("name", "=", "English")]).id

        if kwargs.get('verse_id'):
            return request.redirect('/verse/%s' % slug(
                request.env['openbiblica.verse'].sudo().search([('id', '=', kwargs.get('verse_id'))])))

        if not keyword:
            if kwargs.get('chapter_id'):
                return request.redirect('/chapter/%s' % slug(request.env['openbiblica.chapter'].sudo().search([('id', '=', kwargs.get('chapter_id'))])))
            elif kwargs.get('book_id'):
                return request.redirect('/book/%s' % slug(request.env['openbiblica.book'].sudo().search([('id', '=', kwargs.get('book_id'))])))
            elif kwargs.get('bible_id'):
                return request.redirect('/bible/%s' % slug(request.env['openbiblica.bible'].sudo().search([('id', '=', kwargs.get('bible_id'))])))
            elif kwargs.get('language_id'):
                return request.redirect('/language/%s' % slug(request.env['openbiblica.lang'].sudo().search([('id', '=', kwargs.get('language_id'))])))
            elif kwargs.get('langu_id'):
                return request.redirect('/language/%s' % slug(request.env['openbiblica.lang'].sudo().search([('id', '=', kwargs.get('language_id'))])))
            else:
                return request.redirect(request.httprequest.referrer)

        user = request.env.user
        verses = request.env['openbiblica.verse']
        domain = []
        url = '/search'
        url_args = {}
        values = {}

        keyword = keyword.replace('.', ' ')
        url_args['keyword'] = keyword
        values['keyword'] = keyword
        for srch in keyword.split(" "):
            domain += [('content', 'ilike', srch)]

        if kwargs.get('chapter_id'):
            chapter_id = request.env['openbiblica.chapter'].sudo().search([('id', '=', kwargs.get('chapter_id'))])
            url_args['chapter_id'] = chapter_id.id
            values['chapter_id'] = chapter_id.id
            domain += [('chapter_id', '=', chapter_id.id)]
        elif kwargs.get('book_id'):
            content_id = request.env['openbiblica.book'].sudo().search([('id', '=', kwargs.get('book_id'))])
            url_args['content_id'] = content_id.id
            values['content_id'] = content_id.id
            domain += [('content_id', '=', content_id.id)]
        elif kwargs.get('bible_id'):
            bible_id = request.env['openbiblica.bible'].sudo().search([('id', '=', kwargs.get('bible_id'))])
            url_args['bible_id'] = bible_id.id
            values['bible_id'] = bible_id.id
            domain += [('bible_id', '=', bible_id.id)]
        elif kwargs.get('language_id'):
            lang_id = request.env['openbiblica.lang'].sudo().search([('id', '=', kwargs.get('language_id'))])
            url_args['lang_id'] = lang_id.id
            values['lang_id'] = lang_id.id
            domain += [('lang_id', '=', lang_id.id)]
        elif kwargs.get('langu_id'):
            lang_id = request.env['openbiblica.lang'].sudo().search([('id', '=', kwargs.get('langu_id'))])
            url_args['lang_id'] = lang_id.id
            values['lang_id'] = lang_id.id
            domain += [('lang_id', '=', lang_id.id)]

        total = verses.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._items_per_page,
            url_args=url_args,
        )
        results = verses.search(domain, offset=(page - 1) * self._items_per_page, limit=self._items_per_page,
                               order=sorting)

        values.update({
            'user': user,
            'results': results,
            'sorting': sorting,
            'pager': pager,
            'keyword': keyword,
            'total': total,
            's_lang': s_lang,
        })
        return request.render("openbiblica.view_search", values)

    @http.route(['/add/bibleteam'], type='http', auth="user", website=True)
    def add_bibleteam(self, **kwargs):
        bible_id = request.env['openbiblica.bible'].sudo().search([('id', '=', kwargs.get('bible_id'))])
        if bible_id.create_id == request.env.user:
            team_id = request.env['res.users'].sudo().search([('email', '=', kwargs.get('email'))])
            if team_id:
                bible_id.update(
                    {'team_ids': [(4, team_id.id)]}
                )
        return request.redirect(request.httprequest.referrer)

    @http.route(['/remove/bibleteam/<model("openbiblica.bible"):bible_id>/<model("res.users"):team_id>'], type='http', auth="user", website=True)
    def remove_bibleteam(self, bible_id=0, team_id=0):
        if bible_id.create_id == request.env.user:
            bible_id.update(
                {'team_ids': [(3, team_id.id)]}
            )
        return request.redirect(request.httprequest.referrer)
