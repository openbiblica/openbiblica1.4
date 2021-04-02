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


class WebsiteDictionary(http.Controller):
    _items_per_page = 20
    _comment_per_page = 5
    _word_per_page = 20

    @http.route('/dictionaries', type='http', auth="public", website=True, csrf=False)
    def dictionaries(self):
        values = {
            'dicts': request.env['openbiblica.dictionary'].sudo().search([]),
        }
        return request.render("openbiblica.dictionaries_template", values)

    @http.route('/create/dictionary', type='http', auth="user", website=True)
    def create_dictionary(self):
        values = {
            'source_langs': request.env['openbiblica.lang'].sudo().search([('allow_dictionary', '=', True)]),
            'langs': request.env['openbiblica.lang'].sudo().search([]),
        }
        return request.render("openbiblica.dictionary_editor", values)

    @http.route(['/save/dictionary'], type='http', auth="user", website=True)
    def save_dictionary(self, **kwargs):
        user_id = request.env.user
        if kwargs.get('source_lang_id'):
            source_lang_id = request.env['openbiblica.lang'].search([("id", "=", kwargs.get('source_lang_id'))])
        else:
            return request.redirect(request.httprequest.referrer)
        if kwargs.get('lang_name'):
            target_lang_id = request.env['openbiblica.lang'].search([("name", "=", kwargs.get('lang_name'))])
            if not target_lang_id:
                target_lang_id = request.env['openbiblica.lang'].create({
                    'name': kwargs.get('lang_name'),
                    'direction': kwargs.get('direction'),
                })
        elif kwargs.get('target_lang_id'):
            target_lang_id = request.env['openbiblica.lang'].search([("id", "=", kwargs.get('target_lang_id'))])
        else:
            return request.redirect(request.httprequest.referrer)
        if kwargs.get('dictionary_id'):
            dictionary_id = request.env['openbiblica.dictionary'].sudo().search([('id', '=', int(kwargs.get('dictionary_id')))])
            if dictionary_id.create_id != user_id:
                return request.redirect('/my/home')
            dictionary_id.update({
                'name': kwargs.get('name'),
                'source_lang_id': source_lang_id.id,
                'target_lang_id': target_lang_id.id,
            })
        else:
            dictionary_id = request.env['openbiblica.dictionary'].sudo().create({
                'name': kwargs.get('name'),
                'create_id': user_id.id,
                'source_lang_id': source_lang_id.id,
                'target_lang_id': target_lang_id.id,
            })

        if kwargs.get('file'):
            dictionary_id.update({
                'files': base64.b64encode(kwargs.get('file').read())
           })

        return request.redirect('/dictionary/%s' % slug(dictionary_id))

    @http.route(['/dictionary/<model("openbiblica.dictionary"):dictionary_id>',
                 '/dictionary/<model("openbiblica.dictionary"):dictionary_id>/sorting/<string:sorting>',
                 '/dictionary/<model("openbiblica.dictionary"):dictionary_id>/page/<int:page>'],
                type='http', auth="public", website=True, csrf=False)
    def view_dictionary(self, dictionary_id=0, page=1, sorting=None):
        values = {}
        words = request.env['openbiblica.word']
        domain = [('lang_id', '=', dictionary_id.source_lang_id.id)]
        url_args = {}
        if sorting:
            try:
                words._generate_order_by(sorting, None)
            except ValueError:
                sorting = False
        else:
            sorting = 'name'
        url_args = {'sorting': sorting}

        url = '/dictionary/%s' % (slug(dictionary_id))
        total = words.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._word_per_page,
            url_args=url_args,
        )
        results = words.search(domain, offset=(page - 1) * self._word_per_page, limit=self._word_per_page, order=sorting)
        
        values.update({
            'user_id': request.env.user,
            'dictionary_id': dictionary_id,
            'results': results,
            'pager': pager,
            'total': total,
            'page': page,
        })
        return request.render("openbiblica.view_dictionary", values)

    @http.route('/edit/dictionary', type='http', auth="user", website=True)
    def edit_dictionary(self, **kwargs):
        dictionary_id = request.env['openbiblica.dictionary'].sudo().search([('id', '=', int(kwargs.get('dictionary_id')))])
        if dictionary_id.create_id == request.env.user:
            values = {
                'dictionary_id': dictionary_id,
                'source_langs': request.env['openbiblica.lang'].sudo().search([('allow_dictionary', '=', True)]),
                'langs': request.env['openbiblica.lang'].sudo().search([]),
            }
            return request.render("openbiblica.dictionary_editor", values)
        else:
            return request.redirect(request.httprequest.referrer)

    @http.route(['/search/dictionary/'],
                type='http', auth="public", website=True, csrf=False)
    def search_dicti(self, **kwargs):
        if not kwargs.get('dicti_id'):
            return request.redirect(request.httprequest.referrer)
        if not kwargs.get('dict_keyword'):
            if not kwargs.get('sorting'):
                return request.redirect('/dictionary/%s' % (kwargs.get('dicti_id')))
            return request.redirect('/dictionary/%s/sorting/%s' % (kwargs.get('dicti_id'), kwargs.get('sorting')))
        if not kwargs.get('sorting'):
            return request.redirect('/search/dictionary/%s/keyword/%s' % (kwargs.get('dicti_id'), kwargs.get('dict_keyword')))
        return request.redirect(
            '/search/dictionary/%s/keyword/%s/sorting/%s' % (kwargs.get('dicti_id'), kwargs.get('dict_keyword'), kwargs.get('sorting')))

    @http.route(['/search/dictionary/<model("openbiblica.dictionary"):dictionary_id>/keyword/<string:keyword>',
                 '/search/dictionary/<model("openbiblica.dictionary"):dictionary_id>/keyword/<string:keyword>/page/<int:page>',
                 '/search/dictionary/<model("openbiblica.dictionary"):dictionary_id>/keyword/<string:keyword>/sorting/<string:sorting>',
                 '/search/dictionary/<model("openbiblica.dictionary"):dictionary_id>/keyword/<string:keyword>/sorting/<string:sorting>/page/<int:page>',
                 ],
                type='http', auth="public", website=True, csrf=False)
    def search_dictionary(self, page=1, keyword=None, dictionary_id=0, sorting=None, **kwargs):
        values = {}
        words = request.env['openbiblica.word']
        domain = []
        url_args = {}
        if not dictionary_id:
            return request.redirect('/my/home')
        url_args['dictionary_id'] = dictionary_id.id
        if not keyword:
            return request.redirect('/dictionary/%s'  % (slug(dictionary_id)))

        keyword = keyword.replace('.', ' ')
        domain += [('name', 'ilike', keyword)]
        values['keyword'] = keyword
        url_args['keyword'] = keyword
        for srch in keyword.split(" "):
            domain += [('name', 'ilike', srch)]
        url = '/search/dictionary/%s/keyword/%s' % (slug(dictionary_id), keyword)

        if sorting:
            try:
                words._generate_order_by(sorting, None)
            except ValueError:
                sorting = False
        else:
            sorting = 'name'
        url_args = {'sorting': sorting}

        total = words.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._word_per_page,
            url_args=url_args,
        )
        results = words.search(domain, offset=(page - 1) * self._word_per_page, limit=self._word_per_page, order=sorting)

        values.update({
            'user_id': request.env.user,
            'results': results,
            'pager': pager,
            'total': total,
            'page': page,
            'keyword': keyword,
            'dictionary_id': dictionary_id
        })
        return request.render("openbiblica.view_dictionary_search", values)

    @http.route(['/remove/meaning/<model("openbiblica.meaning"):meaning_id>'], type='http', auth='user', website=True)
    def remove_meaning(self, meaning_id=0):
        meaning_id.unlink()
        return request.redirect(request.httprequest.referrer)

    @http.route(['/add/meaning/'], type='http', auth='user', website=True)
    def add_meaning(self, **kwargs):
        if not kwargs.get('meaning'):
            return request.redirect(request.httprequest.referrer)
        word_id = request.env['openbiblica.word'].sudo().search([('id', '=', int(kwargs.get('word_id')))])
        dictionary_id = request.env['openbiblica.dictionary'].sudo().search([('id', '=', int(kwargs.get('dictionary_id')))])
        meaning = kwargs.get('meaning').lower()
        meaning_id = request.env['openbiblica.meaning'].sudo().search([
            ('name', '=', meaning), ("dictionary_id", "=", dictionary_id.id), ("word_id", "=", word_id.id)])
        if not meaning_id:
            meaning_id = request.env['openbiblica.meaning'].create({
                'name': meaning,
                'dictionary_id': dictionary_id.id,
                'word_id': word_id.id,
            })
        return request.redirect(request.httprequest.referrer)

    @http.route(['/word/<model("openbiblica.word"):word_id>',
                 '/word/<model("openbiblica.word"):word_id>/page/<int:page>'],
                type='http', auth="public", website=True, csrf=False)
    def view_word(self, word_id=0, page=1):
        if not word_id:
            return request.redirect('/my/home')
        values = {}
        verse_ids = request.env['openbiblica.verse']
        domain = [('content', 'ilike', word_id.name)]
        url_args = {}
        url = '/word/%s' % (slug(word_id))
        total = words.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._items_per_page,
            url_args=url_args,
        )
        results = words.search(domain, offset=(page - 1) * self._items_per_page, limit=self._items_per_page)

        values.update({
            'user_id': request.env.user,
            'word_id': word_id,
            'results': results,
            'pager': pager,
            'total': total,
            'page': page,
        })
        return request.render("openbiblica.view_word", values)

    @http.route(['/meaning/<model("openbiblica.meaning"):meaning_id>',
                 '/meaning/<model("openbiblica.meaning"):meaning_id>/page/<int:page>'],
                type='http', auth="public", website=True, csrf=False)
    def view_meaning(self, meaning_id=0, page=1):
        if not meaning_id:
            return request.redirect('/my/home')
        values = {}
        meaning_ids = request.env['openbiblica.meaning']
        domain = [('dictionary_id.id', '=', meaning_id.dictionary_id.id),('name', 'ilike', meaning_id.name)]
        url_args = {}
        url = '/meaning/%s' % (slug(meaning_id))
        total = meaning_ids.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._items_per_page,
            url_args=url_args,
        )
        results = meaning_ids.search(domain, offset=(page - 1) * self._items_per_page, limit=self._items_per_page)

        values.update({
            'user_id': request.env.user,
            'meaning_id': meaning_id,
            'results': results,
            'pager': pager,
            'total': total,
            'page': page,
        })
        return request.render("openbiblica.view_meaning", values)

