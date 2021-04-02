# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import base64
import re

from odoo import http, modules, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug


class WebsiteExport(http.Controller):

    @http.route('/export/usfm/<model("openbiblica.book"):book_id>', type='http', auth="user", website=True)
    def export_usfm(self, book_id=0):
        user_id = request.env.user
        if book_id.create_id == user_id:
            if book_id.rest:
                book_id.update({
                    'rest': None,
                })
            rest = '\id ' + book_id.title_id + ' ' + book_id.bible_id.name + '\n'
            if book_id.title_ide:
                rest = rest + '\ide ' + book_id.title_ide + '\n'
            if book_id.title:
                rest = rest + r'\toc1 ' + book_id.title + '\n'
            if book_id.title_short:
                rest = rest + r'\toc2 ' + book_id.title_short + '\n'
            if book_id.title_abrv:
                rest = rest + r'\toc3 ' + book_id.title_abrv + '\n'
            if book_id.name:
                rest = rest + r'\mt ' + book_id.name + '\n'
            if book_id.description:
                rest = rest + r'\h ' + book_id.description + '\n'

            rest = rest.encode('utf-8')
            book_id.update({
                'rest': base64.b64encode(rest)
            })
        n_values = {
            'chapter_id': book_id.chapter_ids[0],
        }
        return request.render("openbiblica.export_usfm", n_values)

    @http.route('/export/continue/usfm/<model("openbiblica.chapter"):chapter_id>', type='http', auth="user", website=True)
    def cont_export_usfm(self, chapter_id=0):
        user_id = request.env.user
        if chapter_id.create_id == user_id:
            book_id = chapter_id.book_id
            status, headers, content = request.env['ir.http'].sudo().binary_content(
                model='openbiblica.book', id=book_id.id, field='rest')
            rest = base64.b64decode(content).decode('utf-8')

            rest = rest + '\c ' + chapter_id.name + '\n' + '\p' + '\n'

            for verse_id in chapter_id.verse_ids:
                rest = rest + r'\v ' + verse_id.name + ' ' + verse_id.content + '\n'

            rest = rest.encode('utf-8')
            while chapter_id.sequence < len(book_id.chapter_ids):
                book_id.update({
                    'rest': base64.b64encode(rest),
                })
                next_chapter_id = request.env['openbiblica.chapter'].search([
                    ('book_id', '=', book_id.id),
                    ('sequence', '=', chapter_id.sequence + 1)])
                n_values = {
                    'chapter_id': next_chapter_id,
                }
                return request.render("openbiblica.export_usfm", n_values)

            book_id.update({
                'files': base64.b64encode(rest),
                'rest': None,
            })
        return request.redirect('/book/%s' % slug(book_id))

    @http.route('/html/<model("openbiblica.book"):book_id>', type='http', auth="public", website=True)
    def view_html(self, book_id=0):
        values = {'book_id': book_id}
        return request.render("openbiblica.view_html", values)

