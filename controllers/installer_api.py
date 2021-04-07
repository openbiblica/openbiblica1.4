# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import base64
import re
import json
from odoo.modules.module import get_module_resource

from odoo import http, modules, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug

_logger = logging.getLogger(__name__)


class WebsiteInstaller(http.Controller):

    def _install_content(self, content, book_id, user_id, chapter_id):
        # raise UserError(content)
        style = 'normal'
        align = 'default'
        insert_paragraph = False
        chapter = 0
        verse = 0
        major_chapter_id = None
        major_sequence = 1
        chapter_sequence = 1
        verse_sequence = 1

        if chapter_id:
            last_verse_id = request.env['openbiblica.verse'].search([('chapter_id', '=', chapter_id.id)])[-1]
            chapter_sequence = chapter_id.sequence + 1
            if last_verse_id:
                style = last_verse_id.style
                align = last_verse_id.align
                insert_paragraph = last_verse_id.insert_paragraph
#            if chapter_id.subbook_id:
#                major_chapter_id = chapter_id.subbook_id
#                major_sequence = major_chapter_id.sequence + 1

        for line in content:

            head, _, texts = line.partition(" ")

            # CONTENT
            if head == '\id':
                book_id['title_id'] = texts
            elif head == '\ide':
                book_id['title_ide'] = texts
            elif head == r'\toc1':
                book_id['title'] = texts
            elif head == r'\toc2':
                book_id['title_short'] = texts
            elif head == r'\toc3':
                book_id['title_abrv'] = texts
            elif head == '\mt' or head == '\mt1':
                book_id['name'] = texts
            elif head == '\h' or head == '\mt2' or head == '\mt3':
                if book_id.description:
                    book_id['description'] += texts + '\n'
                else:
                    book_id['description'] = texts + '\n'

            # PART

            elif head == '\c':
                c, _, temp = texts.partition(" ")
                if c != ' ':
                    chapter = c
                chapter_id = request.env['openbiblica.chapter'].create({
                    'name': texts,
                    'sequence': chapter_sequence,
                    'create_id': user_id.id,
                    'book_id': book_id.id,
                })
                chapter_sequence += 1
                verse_sequence = 1

            # LINE

            elif head == r'\v':
                v, _, texts = texts.partition(" ")
                if v != ' ':
                    verse = v
                request.env['openbiblica.verse'].create({
                    'chapter': chapter,
                    'name': verse,
                    'content': texts,
                    'sequence': verse_sequence,
                    'create_id': user_id.id,
                    'chapter_id': chapter_id.id,
                    'style': style,
                    'align': align,
                    'insert_paragraph': insert_paragraph,
                })
                verse_sequence += 1
                insert_paragraph = False
            elif head == '\d':
                request.env['openbiblica.verse'].create({
                    'content': texts,
                    'sequence': verse_sequence,
                    'create_id': user_id.id,
                    'chapter_id': chapter_id.id,
                    'style': style,
                    'align': align,
                    'insert_paragraph': insert_paragraph,
                })
                verse_sequence += 1
                insert_paragraph = False
            elif head == r'\f' or head == r'\ft':
                request.env['openbiblica.verse'].create({
                    'content': texts,
                    'sequence': verse_sequence,
                    'create_id': user_id.id,
                    'chapter_id': chapter_id.id,
                    'style': style,
                    'align': align,
                    'insert_paragraph': insert_paragraph,
                })
                verse_sequence += 1
                insert_paragraph = False
            elif head == '\q' or head == '\q1' or head == '\q2' or head == '\q3':
                style = 'italic'
                if texts:
                    request.env['openbiblica.verse'].create({
                        'content': texts,
                        'sequence': verse_sequence,
                        'create_id': user_id.id,
                        'chapter_id': chapter_id.id,
                        'style': style,
                        'align': align,
                        'insert_paragraph': insert_paragraph,
                    })
                    verse_sequence += 1
            elif head == '\m':
                insert_paragraph = False
                if texts:
                    request.env['openbiblica.verse'].create({
                        'content': texts,
                        'sequence': verse_sequence,
                        'create_id': user_id.id,
                        'chapter_id': chapter_id.id,
                        'style': style,
                        'align': align,
                        'insert_paragraph': insert_paragraph,
                    })
                    verse_sequence += 1
            elif head == '\qs':
                texts = texts.strip('\qs ').strip('\qs*')
                request.env['openbiblica.verse'].create({
                    'content': texts,
                    'sequence': verse_sequence,
                    'create_id': user_id.id,
                    'chapter_id': chapter_id.id,
                    'insert_paragraph': insert_paragraph,
                    'style': style,
                })
                verse_sequence += 1

            # COMMANDS

            elif head == '\s5':
                style = 'normal'
            elif head == '\p':
                insert_paragraph = True
            elif head == r'\nb':
                insert_paragraph = False

        next_values = {
            'chapter': chapter,
            'book_id': book_id,
        }
        return next_values

    @http.route(['/install/usfm/<model("openbiblica.book"):book_id>',
                 '/install/usfm/<model("openbiblica.book"):book_id>/<model("openbiblica.bible"):bible_id>'
                 ], type='http', auth="user", website=True)
    def install_usfm(self, book_id=0, bible_id=0):
        user_id = request.env.user
        if book_id.create_id == user_id or user_id in book_id.bible_id.team_ids:
            if book_id.chapter_ids:
                if bible_id:
                    return request.redirect('/cleaning/%s/%s' % (slug(book_id), slug(bible_id)))
                else:
                    return request.redirect('/cleaning/%s' % slug(book_id))
            status, headers, content = request.env['ir.http'].sudo().binary_content(
                model='openbiblica.book', id=book_id.id, field='files')
            content = base64.b64decode(content).decode('utf-8')
            content, mid, rest = content.partition("\c")
            rest = mid + rest
            content = content.splitlines()

            n_values = self._install_content(content, book_id, user_id, None)

            if rest:
                rest = rest.encode('utf-8')
                book_id.update({
                    'rest': base64.b64encode(rest)
                })
                if bible_id:
                    return request.render("openbiblica.install_next_b", n_values)
                return request.render("openbiblica.install_next", n_values)
            else:
                book_id.update({
                    'rest': None,
                    'is_installed': True
                })
        if bible_id:
            return request.redirect('/install/b/usfm/%s' % slug(bible_id))
        return request.redirect('/book/%s' % slug(book_id))

    @http.route(['/install/continue/usfm/<model("openbiblica.book"):book_id>',
                 '/install/continue/usfm/<model("openbiblica.book"):book_id>/<model("openbiblica.bible"):bible_id>'
                 ], type='http', auth="user", website=True)
    def cont_install_usfm(self, book_id=0, bible_id=0):
        user_id = request.env.user
        if book_id.create_id == user_id or user_id in book_id.bible_id.team_ids:
            status, headers, content = request.env['ir.http'].sudo().binary_content(
                model='openbiblica.book', id=book_id.id, field='rest')
            text = base64.b64decode(content).decode('utf-8')
            _, header, content = text.partition("\c")
            text, mid, rest = content.partition("\c")
            rest = mid + rest
            c, _, temp = text.partition(" ")
            chapter, _, temp = temp.partition(" ")
            content = header + text
            text = content.splitlines()

            if book_id.chapter_ids:
                last_chapter_id = request.env['openbiblica.chapter'].search([('book_id', '=', book_id.id)])[-1]
                if chapter == request.env['openbiblica.verse'].search([('chapter_id', '=', last_chapter_id.id), ('chapter', '!=', None)])[0].chapter:
                    request.env['openbiblica.verse'].search([('chapter_id', '=', last_chapter_id.id)]).unlink()
                    prev_chapter_id = request.env['openbiblica.chapter'].search([('book_id', '=', book_id.id), ('sequence', '=', last_chapter_id.sequence - 1)])
                    last_chapter_id.unlink()
                    last_chapter_id = prev_chapter_id
            else:
                last_chapter_id = None

            n_values = self._install_content(text, book_id, user_id, last_chapter_id)

            if rest:
                rest = rest.encode('utf-8')
                book_id.update({
                    'rest': base64.b64encode(rest)
                })
                if bible_id:
                    return request.render("openbiblica.install_next_b", n_values)
                return request.render("openbiblica.install_next", n_values)
            else:
                book_id.update({
                    'rest': None,
                    'is_installed': True
                })
        if bible_id:
            return request.redirect('/install/b/usfm/%s' % slug(bible_id))
        return request.redirect('/book/%s' % slug(book_id))

    @http.route(['/cleaning/<model("openbiblica.book"):book_id>',
                 '/cleaning/<model("openbiblica.book"):book_id>/<model("openbiblica.bible"):bible_id>'
                 ], type='http', auth="user", website=True)
    def cleaning(self, book_id=0, bible_id=0):
        if book_id.create_id == request.env.user or request.env.user in book_id.bible_id.team_ids:
            values = {
                'chapter_id': book_id.chapter_ids[0].id,
                'book_id': book_id,
                'bible_id': bible_id,
            }
            return request.render("openbiblica.cleaning", values)
        return request.redirect('/book/%s' % slug(book_id))

    @http.route(['/install/b/usfm/<model("openbiblica.bible"):bible_id>'], type='http', auth="user", website=True)
    def b_install_usfm(self, bible_id=0):
        if bible_id.create_id == request.env.user or request.env.user in bible_id.team_ids:
            book_ids = request.env['openbiblica.book'].search([
                ('bible_id', '=', bible_id.id),
                ('is_installed', '=', False)])
            book_ids = [j for j in book_ids if j.files]
            if not book_ids:
                bible_id['is_installed'] = True
                return request.redirect('/bible/%s' % slug(bible_id))
            book_id = book_ids[0]
            if book_id.rest:
                return request.redirect('/install/continue/usfm/%s/%s' % (slug(book_id), slug(bible_id)))
            else:
                return request.redirect('/install/usfm/%s/%s' % (slug(book_id), slug(bible_id)))

    def _sourcing(self, object_id, source_id):
        object_id.update({
            'source_id': source_id.id,
            'source_ids': [(4, source_id.id)]
        })
        return

    def _sourcing_b_c(self, bible_id, s_book_id):
        book_id = request.env['openbiblica.book'].create({
            'name': s_book_id.name,
            'sequence': s_book_id.sequence,
            'bundle': s_book_id.bundle,
            'bible_id': bible_id.id,
            'create_id': bible_id.create_id.id,
            'source_id': s_book_id.id,
            'source_ids': [(4, s_book_id.id)]
        })
        if book_id.files:
            book_id.files = None
        return book_id

    def _sourcing_c_p(self, book_id, s_chapter_id):
        chapter_id = request.env['openbiblica.chapter'].create({
            'name': s_chapter_id.name,
            'sequence': s_chapter_id.sequence,
            'book_id': book_id.id,
            'create_id': book_id.create_id.id,
            'source_id': s_chapter_id.id,
            'source_ids': [(4, s_chapter_id.id)]
        })
        return chapter_id

    def _sourcing_p_l(self, chapter_id, s_verse_id):
        request.env['openbiblica.verse'].create({
            'content': ' ',
            'chapter': s_verse_id.chapter or False,
            'name': s_verse_id.name or False,
            'sequence': s_verse_id.sequence,
            'chapter_id': chapter_id.id,
            'create_id': chapter_id.create_id.id,
            'source_id': s_verse_id.id,
            'source_ids': [(4, s_verse_id.id)]
        })
        return

    @http.route(['/submit/sourcing/'], type='json', auth="public", methods=['POST'], website=True)
    def submit_sourcing(self, **kwargs):
        book_id = request.env['openbiblica.book'].search([('id', '=', int(kwargs.get('book_id')))])
        s_chapter_id = request.env['openbiblica.chapter'].search([('id', '=', int(kwargs.get('s_chapter_id')))])
        if not request.env['openbiblica.chapter'].search([('book_id', '=', book_id.id),
                                                ('sequence', '=', s_chapter_id.sequence)]):
            chapter_id = self._sourcing_c_p(book_id, s_chapter_id)
        else:
            chapter_id = request.env['openbiblica.chapter'].search([('book_id', '=', book_id.id),
                                                       ('sequence', '=', s_chapter_id.sequence)])
            if chapter_id.source_id != s_chapter_id:
                self._sourcing(chapter_id, s_chapter_id)

        for s_verse_id in s_chapter_id.verse_ids:
            if not request.env['openbiblica.verse'].search([('chapter_id', '=', chapter_id.id),
                                                    ('sequence', '=', s_verse_id.sequence)]):
                self._sourcing_p_l(chapter_id, s_verse_id)
            elif request.env['openbiblica.verse'].search([('chapter_id', '=', chapter_id.id),
                                                  ('sequence', '=', s_verse_id.sequence)]).source_id.id != s_verse_id.id:
                self._sourcing(request.env['openbiblica.verse'].search([('chapter_id', '=', chapter_id.id),
                                                                ('sequence', '=', s_verse_id.sequence)]), s_verse_id)

        if s_chapter_id.sequence < len(s_chapter_id.book_id.chapter_ids):
            vals = {
                's_chapter_id': request.env['openbiblica.chapter'].search([('book_id', '=', s_chapter_id.book_id.id),
                                                              ('sequence', '=', s_chapter_id.sequence + 1)]).id,
                'book_id': book_id.id,
                'bible_id': kwargs.get('bible_id'),
            }
            return vals

        if not kwargs.get('bible_id'):
            vals = {
                'book_id': kwargs.get('book_id'),
            }
            return vals

        s_book_id = s_chapter_id.book_id
        while s_book_id.sequence < len(s_book_id.bible_id.book_ids):
            next_s_book_id = request.env['openbiblica.book'].search([
                ('bible_id', '=', s_book_id.bible_id.id),
                ('sequence', '=', s_book_id.sequence + 1)])
            if not request.env['openbiblica.book'].search([('bible_id', '=', book_id.bible_id.id),
                                                       ('sequence', '=', next_s_book_id.sequence)]):
                next_book_id = self._sourcing_b_c(book_id.bible_id, next_s_book_id)
            else:
                next_book_id = request.env['openbiblica.book'].search([('bible_id', '=', book_id.bible_id.id),
                                                                      ('sequence', '=', next_s_book_id.sequence)])
                if next_book_id.source_id != next_s_book_id:
                    self._sourcing(next_book_id, next_s_book_id)
            if not next_s_book_id.chapter_ids:
                s_book_id = next_s_book_id
                continue
            vals = {
                's_chapter_id': next_s_book_id.chapter_ids[0].id,
                'book_id': next_book_id.id,
                'bible_id': kwargs.get('bible_id'),
            }
            return vals
        vals = {
            'bible_id': kwargs.get('bible_id'),
        }
        return vals

    @http.route(['/sourcing/c'], type='http', auth="user", website=True)
    def sourcing_c(self, **kwargs):
        book_id = request.env['openbiblica.book'].search([('id', '=', kwargs.get('book_id'))])
        if book_id.create_id != request.env.user or request.env.user not in book_id.bible_id.team_ids:
            return request.redirect('/book/%s' % slug(book_id))
        s_book_id = request.env['openbiblica.book'].search([('id', '=', kwargs.get('source_book_id'))])
        if book_id.source_id != s_book_id:
            self._sourcing(book_id, s_book_id)
        if not s_book_id.chapter_ids:
            return request.redirect('/book/%s' % slug(book_id))
        if kwargs.get('dictionary_id'):
            book_id.dictionary_id = kwargs.get('dictionary_id')
        values = {
            's_chapter_id': s_book_id.chapter_ids[0].id,
            'book_id': book_id.id,
        }
        return request.render("openbiblica.sourcing", values)

    @http.route(['/sourcing/b'], type='http', auth="user", website=True)
    def sourcing_b(self, **kwargs):
        bible_id = request.env['openbiblica.bible'].search([('id', '=', kwargs.get('bible_id'))])
        if bible_id.create_id != request.env.user or request.env.user not in bible_id.team_ids:
            return request.redirect('/bible/%s' % slug(bible_id))
        s_bible_id = request.env['openbiblica.bible'].search([('id', '=', kwargs.get('bible'))])
        if bible_id.source_id != s_bible_id:
            self._sourcing(bible_id, s_bible_id)
        if not s_bible_id.book_ids:
            return request.redirect('/bible/%s' % slug(bible_id))
        for s_book_id in s_bible_id.book_ids:
            if not request.env['openbiblica.book'].search([('bible_id', '=', bible_id.id),
                                                       ('sequence', '=', s_book_id.sequence)]):
                self._sourcing_b_c(bible_id, s_book_id)
            else:
                if request.env['openbiblica.book'].search([('bible_id', '=', bible_id.id),
                                                       ('sequence', '=', s_book_id.sequence)]).source_id.id != s_book_id.id:
                    self._sourcing(request.env['openbiblica.book'].search([('bible_id', '=', bible_id.id),
                                                       ('sequence', '=', s_book_id.sequence)]), s_book_id)
        s_book_ids = [j for j in s_bible_id.book_ids if j.chapter_ids]
        s_book_id = s_book_ids[0]
        if not s_book_id:
            return request.redirect('/bible/%s' % slug(bible_id))
        values = {
            's_chapter_id': s_book_id.chapter_ids[0].id,
            'book_id': request.env['openbiblica.book'].search([('bible_id', '=', bible_id.id),
                                                              ('sequence', '=', s_book_id.sequence)]).id,
            'bible_id': bible_id.id,
        }
        return request.render("openbiblica.sourcing", values)

    @http.route('/source/c/<int:book>', type='http', auth="user", website=True)
    def source_book(self, book=0):
        values = {
            'book_id': request.env['openbiblica.book'].search([('id', '=', book)]),
            'user_id': request.env.user,
        }
        return request.render("openbiblica.source_book", values)

    @http.route('/source/b/<int:bible>', type='http', auth="user", website=True)
    def source_bible(self, bible=0):
        values = {
            'bible_id': request.env['openbiblica.bible'].search([('id', '=', bible)]),
            'user_id': request.env.user,
        }
        return request.render("openbiblica.source_bible", values)

    @http.route(['/transto/book'], type='http', auth='user', website=True)
    def transto_book(self, **kwargs):
        user_id = request.env.user
        if kwargs.get('book_id'):
            book_id = request.env['openbiblica.book'].search([("id", "=", kwargs.get('book_id'))])
            if book_id.create_id != user_id:
                return request.redirect(request.httprequest.referrer)

        elif kwargs.get('bible_id'):
            bible_id = request.env['openbiblica.bible'].search([("id", "=", kwargs.get('bible_id'))])
            if bible_id.create_id != user_id:
                return request.redirect(request.httprequest.referrer)
            if not kwargs.get('book_name'):
                return request.redirect(request.httprequest.referrer)
            book_id = request.env['openbiblica.book'].create({
                'name': kwargs.get('book_name'),
                'sequence': len(bible_id.book_ids) + 1,
                'bible_id': bible_id.id,
                'create_id': bible_id.create_id.id,
            })

        else:
            if kwargs.get('lang_id'):
                lang_id = request.env['openbiblica.lang'].search([("id", "=", kwargs.get('lang_id'))])
            elif kwargs.get('lang_name'):
                lang_id = request.env['openbiblica.lang'].create({
                    'name': kwargs.get('lang_name'),
                    'direction': kwargs.get('direction'),
                })
            else:
                return request.redirect(request.httprequest.referrer)

            if not kwargs.get('name'):
                return request.redirect(request.httprequest.referrer)
            if not kwargs.get('book_name'):
                return request.redirect(request.httprequest.referrer)

            bible_id = request.env['openbiblica.bible'].create({
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'create_id': user_id.id,
                'lang_id': lang_id.id,
            })
            book_id = request.env['openbiblica.book'].create({
                'name': kwargs.get('book_name'),
                'sequence': len(bible_id.book_ids) + 1,
                'bible_id': bible_id.id,
                'create_id': bible_id.create_id.id,
            })
        book_id.files = None
        source_id = request.env['openbiblica.book'].search([("id", "=", kwargs.get('s_book_id'))])
        if book_id.source_id != source_id:
            self._sourcing(book_id, source_id)
        if not source_id.chapter_ids:
            return request.redirect('/book/%s' % slug(book_id))
        s_chapter_id = source_id.chapter_ids[0]
        values = {
            's_chapter_id': s_chapter_id.id,
            'book_id': book_id.id,
        }
        return request.render("openbiblica.sourcing", values)

    def _copy_verse_source(self, verse_id, source_id):
        verse_id.update({
            'content': source_id.content,
            'chapter': source_id.chapter,
            'chapter_alt': source_id.chapter_alt,
            'verse': source_id.verse,
            'verse_alt': source_id.verse_alt,
            'verse_char': source_id.verse_char,
            'style': source_id.style,
            'align': source_id.align,
            'insert_paragraph': source_id.insert_paragraph,
        })
        return

    def _copy_chapter_source(self, chapter_id, source_id):
        chapter_id.update({
            'name': source_id.name,
            'description': source_id.description,
        })
        return

    def _copy_book_source(self, book_id, source_id):
        book_id.update({
            'name': source_id.name,
            'description': source_id.description,
            'title_id': source_id.title_id,
            'title_ide': source_id.title_ide,
            'title_short': source_id.title_short,
            'title_abrv': source_id.title_abrv,
            'bundle': source_id.bundle,
        })
        return

    def _copy_bible_source(self, bible_id, source_id):
        bible_id.update({
            'name': source_id.name,
            'description': source_id.description,
        })
        return

    def _copying_p_l(self, chapter_id, s_verse_id):
        request.env['openbiblica.verse'].create({
            'content': s_verse_id.content,
            'chapter': s_verse_id.chapter or False,
            'name': s_verse_id.name or False,
            'sequence': s_verse_id.sequence,
            'chapter_id': chapter_id.id,
            'create_id': chapter_id.create_id.id,
            'source_id': s_verse_id.id,
            'source_ids': [(4, s_verse_id.id)]
        })
        return

    def _copying_c_p(self, book_id, s_chapter_id):
        chapter_id = request.env['openbiblica.chapter'].create({
            'name': s_chapter_id.name,
            'description': s_chapter_id.description,
            'sequence': s_chapter_id.sequence,
            'book_id': book_id.id,
            'create_id': book_id.create_id.id,
            'source_id': s_chapter_id.id,
            'source_ids': [(4, s_chapter_id.id)]
        })
        return chapter_id

    def _copying_b_c(self, bible_id, s_book_id):
        book_id = request.env['openbiblica.book'].create({
            'name': s_book_id.name,
            'sequence': s_book_id.sequence,
            'description': s_book_id.description,
            'title_id': s_book_id.title_id,
            'title_ide': s_book_id.title_ide,
            'title_short': s_book_id.title_short,
            'title_abrv': s_book_id.title_abrv,
            'bundle': s_book_id.bundle,
            'bible_id': bible_id.id,
            'create_id': bible_id.create_id.id,
            'source_id': s_book_id.id,
            'source_ids': [(4, s_book_id.id)]
        })
        if book_id.files:
            book_id.files = None
        return book_id

    @http.route(['/copying/source/'], type='json', auth="public", methods=['POST'], website=True)
    def copying_source(self, **kwargs):
        book_id = request.env['openbiblica.book'].search([('id', '=', int(kwargs.get('book_id')))])
        s_chapter_id = request.env['openbiblica.chapter'].search([('id', '=', int(kwargs.get('s_chapter_id')))])
        if not request.env['openbiblica.chapter'].search([('book_id', '=', book_id.id),
                                                       ('sequence', '=', s_chapter_id.sequence)]):
            chapter_id = self._copying_c_p(book_id, s_chapter_id)
        else:
            chapter_id = request.env['openbiblica.chapter'].search([
                ('book_id', '=', book_id.id),
                ('sequence', '=', s_chapter_id.sequence)])
            self._copy_chapter_source(chapter_id, s_chapter_id)

        for s_verse_id in s_chapter_id.verse_ids:
            if not request.env['openbiblica.verse'].search([('chapter_id', '=', chapter_id.id),
                                                    ('sequence', '=', s_verse_id.sequence)]):
                self._copying_p_l(chapter_id, s_verse_id)
            else:
                self._copy_verse_source(
                    request.env['openbiblica.verse'].search([('chapter_id', '=', chapter_id.id),
                                                     ('sequence', '=', s_verse_id.sequence)]), s_verse_id)

        if s_chapter_id.sequence < len(s_chapter_id.book_id.chapter_ids):
            vals = {
                's_chapter_id': request.env['openbiblica.chapter'].search([('book_id', '=', s_chapter_id.book_id.id),
                                                              ('sequence', '=', s_chapter_id.sequence + 1)]).id,
                'book_id': book_id.id,
                'bible_id': kwargs.get('bible_id'),
            }
            return vals

        if not kwargs.get('bible_id'):
            vals = {
                'book_id': kwargs.get('book_id'),
            }
            return vals

        s_book_id = s_chapter_id.book_id
        while s_book_id.sequence < len(s_book_id.bible_id.book_ids):
            next_s_book_id = request.env['openbiblica.book'].search([
                ('bible_id', '=', s_book_id.bible_id.id),
                ('sequence', '=', s_book_id.sequence + 1)])
            if not request.env['openbiblica.book'].search([('bible_id', '=', book_id.bible_id.id),
                                                       ('sequence', '=', next_s_book_id.sequence)]):
                next_book_id = self._copying_b_c(book_id.bible_id, next_s_book_id)
            else:
                next_book_id = request.env['openbiblica.book'].search([('bible_id', '=', book_id.bible_id.id),
                                                                      ('sequence', '=', next_s_book_id.sequence)])
                self._copy_book_source(next_book_id, next_s_book_id)
            if not next_s_book_id.chapter_ids:
                s_book_id = next_s_book_id
                continue
            vals = {
                's_chapter_id': next_s_book_id.chapter_ids[0].id,
                'book_id': next_book_id.id,
                'bible_id': kwargs.get('bible_id'),
            }
            return vals
        vals = {
            'bible_id': kwargs.get('bible_id'),
        }
        return vals

    @http.route(['/copy/c/source/<model("openbiblica.book"):book_id>/<model("openbiblica.book"):source_id>'], type='http',
                auth='user', website=True)
    def copy_book_source(self, book_id=0, source_id=0):
        if book_id.create_id != request.env.user or request.env.user not in book_id.bible_id.team_ids:
            return request.redirect(request.httprequest.referrer)
        self._copy_book_source(book_id, source_id)
        if not source_id.chapter_ids:
            return request.redirect('/book/%s' % slug(book_id))
        values = {
            's_chapter_id': source_id.chapter_ids[0].id,
            'book_id': book_id.id,
        }
        return request.render("openbiblica.copying", values)

    @http.route(['/copy/b/source/<model("openbiblica.bible"):bible_id>/<model("openbiblica.bible"):source_id>'], type='http',
                auth='user', website=True)
    def copy_bible_source(self, bible_id=0, source_id=0):
        if bible_id.create_id != request.env.user or request.env.user not in bible_id.team_ids:
            return request.redirect(request.httprequest.referrer)
        self._copy_bible_source(bible_id, source_id)
        if not source_id.book_ids:
            return request.redirect('/bible/%s' % slug(bible_id))

        for s_book_id in source_id.book_ids:
            if not request.env['openbiblica.book'].search([('bible_id', '=', bible_id.id),
                                                       ('sequence', '=', s_book_id.sequence)]):
                self._copying_b_c(bible_id, s_book_id)
            else:
                self._copy_book_source(request.env['openbiblica.book'].search([('bible_id', '=', bible_id.id),
                                                                              ('sequence', '=', s_book_id.sequence)]), s_book_id)
        s_book_ids = [j for j in source_id.book_ids if j.chapter_ids]
        s_book_id = s_book_ids[0]
        if not s_book_id:
            return request.redirect('/bible/%s' % slug(bible_id))
        values = {
            's_chapter_id': s_book_id.chapter_ids[0].id,
            'book_id': request.env['openbiblica.book'].search([('bible_id', '=', bible_id.id), ('sequence', '=', s_book_id.sequence)]).id,
            'bible_id': bible_id.id,
        }
        return request.render("openbiblica.copying", values)

    @http.route(['/copy/p/source/<model("openbiblica.chapter"):chapter_id>/<model("openbiblica.chapter"):source_id>'], type='http',
                auth='user', website=True)
    def copy_chapter_source(self, chapter_id=0, source_id=0):
        if chapter_id.create_id != request.env.user or request.env.user not in chapter_id.bible_id.team_ids:
            return request.redirect(request.httprequest.referrer)
        self._copy_chapter_source(chapter_id, source_id)
        if not source_id.verse_ids:
            return request.redirect(request.httprequest.referrer)
        for s_verse_id in source_id.verse_ids:
            if not request.env['openbiblica.verse'].search([('chapter_id', '=', chapter_id.id),
                                                    ('sequence', '=', s_verse_id.sequence)]):
                self._copying_p_l(chapter_id, s_verse_id)
            else:
                self._copy_verse_source(request.env['openbiblica.verse'].search([('chapter_id', '=', chapter_id.id),
                                                                        ('sequence', '=', s_verse_id.sequence)]), s_verse_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/copy/l/source/<model("openbiblica.verse"):verse_id>/<model("openbiblica.verse"):source_id>'], type='http',
                auth='user', website=True)
    def copy_verse_source(self, verse_id=0, source_id=0):
        if verse_id.create_id == request.env.user or request.env.user in verse_id.bible_id.team_ids:
            self._copy_verse_source(verse_id, source_id)
        return request.redirect(request.httprequest.referrer)

    def _remove_verse_source(self, verse_id, source_id):
        if verse_id.source_id == source_id:
            verse_id['source_id'] = None
        verse_id.update({
            'source_ids': [(3, source_id.id)]
        })
        return

    def _remove_chapter_source(self, chapter_id, source_id):
        if chapter_id.source_id == source_id:
            chapter_id['source_id'] = None
        chapter_id.update({
            'source_ids': [(3, source_id.id)]
        })
        return

    def _remove_book_source(self, book_id, source_id):
        if book_id.source_id == source_id:
            book_id['source_id'] = None
        book_id.update({
            'source_ids': [(3, source_id.id)]
        })
        return

    def _remove_bible_source(self, bible_id, source_id):
        if bible_id.source_id == source_id:
            bible_id['source_id'] = None
        bible_id.update({
            'source_ids': [(3, source_id.id)]
        })
        return

    @http.route(['/remove/source/'], type='json', auth="public", methods=['POST'], website=True)
    def remove_source(self, **kwargs):
        book_id = request.env['openbiblica.book'].search([('id', '=', int(kwargs.get('book_id')))])
        s_chapter_id = request.env['openbiblica.chapter'].search([('id', '=', int(kwargs.get('s_chapter_id')))])

        while request.env['openbiblica.chapter'].search([('book_id', '=', book_id.id),
                                               ('source_ids', 'in', s_chapter_id.id)]):
            chapter_id = request.env['openbiblica.chapter'].search([('book_id', '=', book_id.id),
                                            ('source_ids', 'in', s_chapter_id.id)])[0]
            for s_verse_id in s_chapter_id.verse_ids:
                while request.env['openbiblica.verse'].search([('chapter_id', '=', chapter_id.id),
                                                        ('source_ids', 'in', s_verse_id.id)]):
                    verse_id = request.env['openbiblica.verse'].search([('chapter_id', '=', chapter_id.id),
                                                        ('source_ids', 'in', s_verse_id.id)])[0]
                    self._remove_verse_source(verse_id, s_verse_id)
                    continue
            self._remove_chapter_source(chapter_id, s_chapter_id)
            continue

        if s_chapter_id.sequence < len(s_chapter_id.book_id.chapter_ids):
            vals = {
                's_chapter_id': request.env['openbiblica.chapter'].search([('book_id', '=', s_chapter_id.book_id.id),
                                                              ('sequence', '=', s_chapter_id.sequence + 1)]).id,
                'book_id': book_id.id,
                'bible_id': kwargs.get('bible_id'),
            }
            return vals

        s_book_id = s_chapter_id.book_id
        self._remove_book_source(book_id, s_book_id)

        if not kwargs.get('bible_id'):
            vals = {
                'book_id': kwargs.get('book_id'),
            }
            return vals

        while request.env['openbiblica.book'].search([('bible_id', '=', book_id.bible_id.id),
                                                  ('source_ids', 'in', s_book_id.id)]):
            vals = {
                's_chapter_id': s_book_id.chapter_ids[0].id,
                'book_id': request.env['openbiblica.book'].search([('bible_id', '=', book_id.bible_id.id),
                                                                  ('source_ids', 'in', s_book_id.id)])[0].id,
                'bible_id': kwargs.get('bible_id'),
            }
            return vals

        while s_book_id.sequence < len(s_book_id.bible_id.book_ids):
            next_s_book_id = request.env['openbiblica.book'].search([
                ('bible_id', '=', s_book_id.bible_id.id),
                ('sequence', '=', s_book_id.sequence + 1)])
            if not request.env['openbiblica.book'].search([('bible_id', '=', book_id.bible_id.id),
                                                       ('source_ids', 'in', next_s_book_id.id)]):
                continue
            next_book_id = request.env['openbiblica.book'].search([('bible_id', '=', book_id.bible_id.id),
                                                                  ('source_ids', 'in', next_s_book_id.id)])[0]
            if not next_s_book_id.chapter_ids:
                self._remove_book_source(next_book_id, next_s_book_id)
                continue
            vals = {
                's_chapter_id': next_s_book_id.chapter_ids[0].id,
                'book_id': next_book_id.id,
                'bible_id': kwargs.get('bible_id'),
            }
            return vals
        self._remove_bible_source(book_id.bible_id, s_book_id.bible_id)
        vals = {
            'bible_id': kwargs.get('bible_id'),
        }
        return vals

    @http.route(['/remove/c/source/<model("openbiblica.book"):book_id>/<model("openbiblica.book"):source_id>'], type='http',
                auth='user', website=True)
    def remove_book_source(self, book_id=0, source_id=0):
        if book_id.create_id != request.env.user or request.env.user not in book_id.bible_id.team_ids:
            return request.redirect(request.httprequest.referrer)
        if not source_id.chapter_ids:
            self._remove_book_source(book_id, source_id)
            return request.redirect('/book/%s' % slug(book_id))
        values = {
            's_chapter_id': source_id.chapter_ids[0].id,
            'book_id': book_id.id,
        }
        return request.render("openbiblica.remove_source", values)

    @http.route(['/remove/b/source/<model("openbiblica.bible"):bible_id>/<model("openbiblica.bible"):source_id>'], type='http',
                auth='user', website=True)
    def remove_bible_source(self, bible_id=0, source_id=0):
        if bible_id.create_id != request.env.user or request.env.user not in bible_id.team_ids:
            return request.redirect(request.httprequest.referrer)
        if not source_id.book_ids:
            return request.redirect('/bible/%s' % slug(bible_id))

        s_book_id = source_id.book_ids[0]
        while s_book_id.sequence < len(source_id.book_ids) + 1:
            while request.env['openbiblica.book'].search([('bible_id', '=', bible_id.id),
                                                            ('source_ids', 'in', s_book_id.id)]):
                book_id = request.env['openbiblica.book'].search([('bible_id', '=', bible_id.id),
                                                                 ('source_ids', 'in', s_book_id.id)])[0]
                if s_book_id.chapter_ids:
                    values = {
                        's_chapter_id': s_book_id.chapter_ids[0].id,
                        'book_id': book_id.id,
                        'bible_id': bible_id.id,
                    }
                    return request.render("openbiblica.remove_source", values)
                self._remove_book_source(book_id, s_book_id)
                continue
            s_book_id = request.env['openbiblica.book'].search([('bible_id', '=', s_book_id.bible_id.id),
                                                               ('sequence', '=', s_book_id.sequence + 1)])
            continue
        self._remove_bible_source(bible_id, source_id)
        return request.redirect('/bible/%s' % slug(bible_id))

    @http.route(['/remove/dict/<model("openbiblica.book"):book_id>'], type='http', auth='user', website=True)
    def remove_book_dictionary(self, book_id=0):
        if book_id.create_id == request.env.user or request.env.user in bible_id.team_ids:
            book_id['dictionary_id'] = None
        return request.redirect(request.httprequest.referrer)

    @http.route(['/select/dict/<model("openbiblica.book"):book_id>'], type='http', auth='user', website=True)
    def select_book_dictionary(self, book_id=0, **kwargs):
        if book_id.create_id == request.env.user or request.env.user in book_id.bible_id.team_ids:
            if not kwargs.get('dictio_id'):
                return request.redirect(request.httprequest.referrer)
            book_id['dictionary_id'] = kwargs.get('dictio_id')
        return request.redirect(request.httprequest.referrer)

    @http.route(['/select/default/dict/<model("openbiblica.bible"):bible_id>'], type='http', auth='user', website=True)
    def select_bible_dictionary(self, bible_id=0, **kwargs):
        if bible_id.create_id == request.env.user or request.env.user in bible_id.team_ids:
            if not kwargs.get('dictionary_id'):
                bible_id['default_dictionary_id'] = None
                return request.redirect(request.httprequest.referrer)
            bible_id['default_dictionary_id'] = kwargs.get('dictionary_id')
        return request.redirect(request.httprequest.referrer)

    @http.route(['/install/dictionary/<model("openbiblica.dictionary"):dictionary_id>',
                 ], type='http', auth="user", website=True)
    def install_dictionary(self, dictionary_id=0):
        user_id = request.env.user
        if dictionary_id.create_id == user_id or user_id in dictionary_id.team_ids:
            status, headers, content = request.env['ir.http'].sudo().binary_content(
                model='openbiblica.dictionary', id=dictionary_id.id, field='files')
            contents = json.loads(base64.b64decode(content).decode('utf-8'))

            for line in contents:
                value = contents[line]
                lemma = value.get('lemma')
                strongs_def = value.get('strongs_def')
                kjv_def = value.get('kjv_def')
                word_id = request.env['openbiblica.word'].search([("name", "=", lemma),
                                                                  ("lang_id", "=", dictionary_id.source_lang_id.id)])
                if not word_id:
                    word_id = request.env['openbiblica.word'].create({
                        'name': lemma,
                        'lang_id': dictionary_id.source_lang_id.id,
                    })
#                if strongs_def:
#                    if not request.env['openbiblica.meaning'].search([("name", "=", strongs_def),
#                                                                            ("word_id", "=", word_id.id),
#                                                                            ("dictionary_id", "=", dictionary_id.id)]):
#                        request.env['openbiblica.meaning'].create({
#                            'name': strongs_def,
#                            'word_id': word_id.id,
#                            'dictionary_id': dictionary_id.id,
#                        })
                if kjv_def:
                    if not request.env['openbiblica.meaning'].search([("name", "=", kjv_def),
                                                                            ("word_id", "=", word_id.id),
                                                                            ("dictionary_id", "=", dictionary_id.id)]):
                        request.env['openbiblica.meaning'].create({
                            'name': kjv_def,
                            'word_id': word_id.id,
                            'dictionary_id': dictionary_id.id,
                        })

            dictionary_id['files'] = None
        return request.redirect('/dictionary/%s' % slug(dictionary_id))

    @http.route(['/default/bible/<model("openbiblica.dictionary"):dictionary_id>'], type='http', auth='user', website=True)
    def select_default_dictionary(self, dictionary_id=0, **kwargs):
        if dictionary_id.create_id == request.env.user or request.env.user in dictionary_id.team_ids:
            if not kwargs.get('biblica_id'):
                dictionary_id['default_bible_id'] = None
                return request.redirect(request.httprequest.referrer)
            dictionary_id['default_bible_id'] = kwargs.get('biblica_id')
        return request.redirect(request.httprequest.referrer)

    @http.route(['/reference/<model("openbiblica.dictionary"):dict_lang_id>'], type='http', auth='user', website=True)
    def reference_dict(self, dict_lang_id=0, **kwargs):
        if dict_lang_id.create_id == request.env.user or request.env.user in dict_lang_id.team_ids:
            if not kwargs.get('dict_reference_id'):
                dict_lang_id['dict_reference_id'] = None
                return request.redirect(request.httprequest.referrer)
            dict_lang_id['dict_reference_id'] = kwargs.get('dict_reference_id')
        return request.redirect(request.httprequest.referrer)

    @http.route(['/wordmapping/'], type='http', auth='user', website=True)
    def wordmapping(self, **kwargs):
        values = {
            'user_id': request.env.user,
        }
        return request.render("openbiblica.wordmapping", values)

    @http.route(['/wordmappingjs'], type='json', auth="user", website=True)
    def wordmappingjs(self, **kwargs):
        if not request.env.user.allow_word_mapping:
            return request.redirect('/my/home')
        verse_ids = request.env['openbiblica.verse'].search([('is_mapped', '=', False)])
        if not verse_ids:
            values = {
                'total': None,
            }
            return values
        verse_id = verse_ids[0]
        if verse_id.lang_id.direction == 'rtl':
            words = verse_id.content.split()
        else:
            words = re.findall(r'\w+|[\[\]⸂⸃()]|\S+', verse_id.content)
        for word in words:
            word_id = request.env['openbiblica.word'].search([('name', '=', word), ('lang_id', '=', verse_id.lang_id.id)])
            if not word_id:
                word_id = request.env['openbiblica.word'].create({
                    'name': word,
                    'lang_id': verse_id.lang_id.id,
                })
            to = word_id.total + 1
            word_id['total'] = to
        verse_id['is_mapped'] = True
        if not kwargs.get('tot'):
            total_mapped = 0
        else:
            total_mapped = int(kwargs.get('tot'))
        values = {
            'total_mapped': total_mapped + 1,
        }
        return values

