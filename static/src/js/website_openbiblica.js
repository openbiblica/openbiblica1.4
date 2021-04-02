odoo.define('openbiblica.website_openbiblica', function (require) {
'use strict';

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var core = require('web.core');

    var _t = core._t;

    var lastsearch;

//    SEARCH MENU

    if ($('.o_bible_search').length) {
        var lang_options = $("select[name='langu_id']:enabled");
        var bible_options = $("select[name='bible_id']:enabled");
        var book_options = $("select[name='book_id']:enabled");
        var chapter_options = $("select[name='chapter_id']:enabled");
        var verse_options = $("select[name='verse_id']:enabled");

        $('.o_bible_search').ready(function(){
            bible_options.parent().hide();
            book_options.parent().hide();
            chapter_options.parent().hide();
            verse_options.parent().hide();
            ajax.jsonRpc('/get/langs', 'call', {
                }).then(function (langs) {
                if (langs.length > 0){
                    var i;
                    for (i = 0; i < langs.length; i++) {
                        lang_options.append('<option value="' + langs[i].id + '">' + langs[i].name + '</option>');
                    };
                };
            });
        });
        lang_options.on('change', lang_options, function () {
            bible_options.children('option:not(:first)').remove();
            book_options.children('option:not(:first)').remove();
            chapter_options.children('option:not(:first)').remove();
            verse_options.children('option:not(:first)').remove();
            bible_options.parent().hide();
            book_options.parent().hide();
            chapter_options.parent().hide();
            verse_options.parent().hide();
            var lang = lang_options.val();
            ajax.jsonRpc('/get/bibles/', 'call', {
                  lang_id: lang,
                }).then(function (bibles) {
                if (bibles){
                    var i;
                    for (i = 0; i < bibles.length; i++) {
                        bible_options.append('<option value="' + bibles[i].id + '">' + bibles[i].name + '</option>');
                    };
                    if (i>0){bible_options.parent().show();};
                };
            });
        });
        if (bible_options.length >= 1) {
            bible_options.on('change', bible_options, function () {
                book_options.children('option:not(:first)').remove();
                chapter_options.children('option:not(:first)').remove();
                verse_options.children('option:not(:first)').remove();
                book_options.parent().hide();
                chapter_options.parent().hide();
                verse_options.parent().hide();
                var bible = bible_options.val();
                ajax.jsonRpc('/get/book/', 'call', {
                      bible_id: bible,
                    }).then(function (book) {
                    if (book){
                        console.log(book);
                        var i;
                        for (i = 0; i < book.length; i++) {
                            book_options.append('<option value="' + book[i].id + '">' + book[i].name + '</option>');
                        };
                    if (i>0){book_options.parent().show();};
                    };
                });
            });
        }
        if (book_options.length >= 1) {
            book_options.on('change', book_options, function () {
                chapter_options.children('option:not(:first)').remove();
                verse_options.children('option:not(:first)').remove();
                chapter_options.parent().hide();
                verse_options.parent().hide();
                var book = book_options.val();
                ajax.jsonRpc('/get/chapter/', 'call', {
                      book_id: book,
                    }).then(function (chapter) {
                    if (chapter){
                        console.log(chapter);
                        var i;
                        for (i = 0; i < chapter.length; i++) {
                            chapter_options.append('<option value="' + chapter[i].id + '">' + chapter[i].name + '</option>');
                        };
                    if (i>0){chapter_options.parent().show();};
                    };
                });
            });
        }
        if (chapter_options.length >= 1) {
            chapter_options.on('change', chapter_options, function () {
                verse_options.children('option:not(:first)').remove();
                verse_options.parent().hide();
                var chapter = chapter_options.val();
                ajax.jsonRpc('/get/verse/', 'call', {
                      chapter_id: chapter,
                    }).then(function (verse) {
                    if (verse){
//                        console.log(verse);
                        var i;
                        for (i = 0; i < verse.length; i++) {
                            verse_options.append('<option value="' + verse[i].id + '">' + verse[i].name + '</option>');
                        };
                    if (i>0){verse_options.parent().show();};
                    };
                });
            });
        }
    }

    if ($('.o_dictionary_search').length) {
        var dict_s_lang_options = $("select[name='dict_s_lang_id']:enabled");
        var dict_t_lang_options = $("select[name='dict_t_lang_id']:enabled");
        var dicti_options = $("select[name='dicti_id']:enabled");
        var dict_form = $("form[id='search_dict_form']:enabled");

        $('.o_dictionary_search').ready(function(){
            dicti_options.parent().hide();
            dict_t_lang_options.parent().hide();
            ajax.jsonRpc('/get/source_langs/', 'call', {
                }).then(function (source_langs) {
                if (source_langs.length > 0){
                    var i;
                    for (i = 0; i < source_langs.length; i++) {
                        dict_s_lang_options.append('<option value="' + source_langs[i].id + '">' + source_langs[i].name + '</option>');
                    };
                };
            });
        });
        dict_s_lang_options.on('change', dict_s_lang_options, function () {
            dict_t_lang_options.children('option:not(:first)').remove();
            dict_t_lang_options.parent().hide();
            var source_lang = dict_s_lang_options.val();
            ajax.jsonRpc('/get/target_langs/', 'call', {
                  source_lang_id: source_lang,
                }).then(function (target_langs) {
                if (target_langs){
                    var i;
                    for (i = 0; i < target_langs.length; i++) {
                        dict_t_lang_options.append('<option value="' + target_langs[i].id + '">' + target_langs[i].name + '</option>');
                    };
                    if (i>0){dict_t_lang_options.parent().show();};
                };
            });
        });
        if (dict_t_lang_options.length >= 1) {
            dict_t_lang_options.on('change', dict_t_lang_options, function () {
                dicti_options.children('option:not(:first)').remove();
                dicti_options.parent().hide();
                var source_lang = dict_s_lang_options.val();
                var target_lang = dict_t_lang_options.val();
                ajax.jsonRpc('/get/dictionaries/', 'call', {
                      source_lang_id: source_lang,
                      target_lang_id: target_lang,
                    }).then(function (dictionaries) {
                    if (dictionaries){
                        console.log(dictionaries);
                        var i;
                        for (i = 0; i < dictionaries.length; i++) {
                            dicti_options.append('<option value="' + dictionaries[i].id + '">' + dictionaries[i].name + '</option>');
                        };
                    if (i>0){dicti_options.parent().show();};
                    };
                });
            });
        }
//        if (dicti_options.length >= 1) {
//            dicti_options.on('change', dicti_options, function ()
//           {
//                dict_form.attrs['t-attf-action'] += "/dictionary";
//                dict_form.setAttribute("t-attf-action", '/search/');
//                node.attrs['t-att-class'] += " + '" + action_classes + "'";
//            });
//        }
    }

//    USFM JSON

    if ($('.o_install_next').length) {
        $('.o_install_next').ready(function(){
            $("#install_next_button").click();
        });
    }

//    SELECT SOURCE

    if ($('.o_select_source').length) {
        $('.o_select_source').on('change', $("select[name='select_source']"), function () {
            $("#select_source_button").click();
        });
        $('.o_select_source').on('change', $("select[name='select_lang']"), function () {
            $("#select_source_button").click();
        });
    }

//    TRANSLATE THIS

    if ($('.o_translate_book').length) {
        $('.o_translate_book').ready(function(){
            var t_book_id = $("input[name='t_book_id']").val();
            var t_book_name = $("input[name='t_book_name']").val();
            $("div[id='translate_this']").append(
                '<a href="/translate/c/' + t_book_id + '" class="btn btn-sm btn-primary">Translate ' + t_book_name + '</a>'
            ).show()
        });
    }

//    ADD BOOK SOURCE

    if ($('.o_add_book_source').length) {
        var lang_source = $("select[name='source_lang_id']:enabled");
        var bible_source = $("select[name='source_bible_id']:enabled");
        var book_source = $("select[name='source_book_id']:enabled");
        var lang_target = $("select[name='target_lang_id']:enabled");
        var dictionary_source = $("select[name='dictionary_id']:enabled");
        var submit = $("div[name='submit']");

        $('.o_add_book_source').ready(function(){
            bible_source.parent().hide();
            book_source.parent().hide();
            lang_target.parent().hide();
            dictionary_source.parent().hide();
            submit.hide()
            ajax.jsonRpc('/get/langs', 'call', {
                }).then(function (langs) {
                if (langs.length > 0){
                    var i;
                    for (i = 0; i < langs.length; i++) {
                        lang_source.append('<option value="' + langs[i].id + '">' + langs[i].name + '</option>');
                    };
                };
            });
        });
        lang_source.on('change', lang_source, function () {
            bible_source.children('option:not(:first)').remove();
            book_source.children('option:not(:first)').remove();
            lang_target.children('option:not(:first)').remove();
            dictionary_source.children('option:not(:first)').remove();
            bible_source.parent().hide();
            book_source.parent().hide();
            lang_target.parent().hide();
            dictionary_source.parent().hide();
            submit.hide()
            var lang = lang_source.val();
            ajax.jsonRpc('/get/bibles/', 'call', {
                  lang_id: lang,
                }).then(function (bibles) {
                if (bibles){
                    var i;
                    for (i = 0; i < bibles.length; i++) {
                        bible_source.append('<option value="' + bibles[i].id + '">' + bibles[i].name + '</option>');
                    };
                    if (i>0){bible_source.parent().show();};
                };
            });
        });
        if (bible_source.length >= 1) {
            bible_source.on('change', bible_source, function () {
                book_source.children('option:not(:first)').remove();
                lang_target.children('option:not(:first)').remove();
                dictionary_source.children('option:not(:first)').remove();
                book_source.parent().hide();
                lang_target.parent().hide();
                dictionary_source.parent().hide();
                submit.hide()
                var bible = bible_source.val();
                ajax.jsonRpc('/get/book/', 'call', {
                      bible_id: bible,
                    }).then(function (book) {
                    if (book){
                        console.log(book);
                        var i;
                        for (i = 0; i < book.length; i++) {
                            book_source.append('<option value="' + book[i].id + '">' + book[i].name + '</option>');
                        };
                    if (i>0){book_source.parent().show();};
                    };
                });
            });
        }
        if (book_source.length >= 1) {
            book_source.on('change', bible_source, function () {
                lang_target.children('option:not(:first)').remove();
                dictionary_source.children('option:not(:first)').remove();
                lang_target.parent().hide();
                dictionary_source.parent().hide();
                var lang = lang_source.val();
                ajax.jsonRpc('/get/target_langs/', 'call', {
                      source_lang_id: lang,
                    }).then(function (target_lang) {
                    if (target_lang){
                        console.log(target_lang);
                        var i;
                        for (i = 0; i < target_lang.length; i++) {
                            lang_target.append('<option value="' + target_lang[i].id + '">' + target_lang[i].name + '</option>');
                        };
                    if (i>0){lang_target.parent().show();};
                    };
                });
                if ($(this).val() || 0){
                    submit.show();
                } else {
                    submit.hide();
                }
            });
        }
        if (lang_target.length >= 1) {
            lang_target.on('change', lang_target, function () {
                dictionary_source.children('option:not(:first)').remove();
                dictionary_source.parent().hide();
                var langtarget = lang_target.val();
                var lang = lang_source.val();
                ajax.jsonRpc('/get/dictionaries/', 'call', {
                      target_lang_id: langtarget,
                      source_lang_id: lang,
                    }).then(function (dicts) {
                    if (dicts){
                        console.log(dicts);
                        var i;
                        for (i = 0; i < dicts.length; i++) {
                            dictionary_source.append('<option value="' + dicts[i].id + '">' + dicts[i].name + '</option>');
                        };
                    if (i>0){dictionary_source.parent().show();};
                    };
                });
            });
        }
    }

//    ADD BIBLE SOURCE

    if ($('.o_add_bible_source').length) {
        var lang_source = $("select[name='lang']:enabled");
        var bible_source = $("select[name='bible']:enabled");
        var submit = $("div[name='submit']");

        $('.o_add_bible_source').ready(function(){
            bible_source.parent().hide();
            submit.hide()
            ajax.jsonRpc('/get/langs', 'call', {
                }).then(function (langs) {
                if (langs.length > 0){
                    var i;
                    for (i = 0; i < langs.length; i++) {
                        lang_source.append('<option value="' + langs[i].id + '">' + langs[i].name + '</option>');
                    };
                };
            });
        });
        lang_source.on('change', lang_source, function () {
            bible_source.children('option:not(:first)').remove();
            bible_source.parent().hide();
            submit.hide()
            var lang = lang_source.val();
            ajax.jsonRpc('/get/bibles/', 'call', {
                  lang_id: lang,
                }).then(function (bibles) {
                if (bibles){
                    var i;
                    for (i = 0; i < bibles.length; i++) {
                        bible_source.append('<option value="' + bibles[i].id + '">' + bibles[i].name + '</option>');
                    };
                    if (i>0){bible_source.parent().show();};
                };
            });
        });
        if (bible_source.length >= 1) {
            bible_source.on('change', bible_source, function () {
                if ($(this).val() || 0){
                    submit.show();
                } else {
                    submit.hide();
                }
            });
        }
    }

//SOURCE MENU

    if ($('.o_source_menu').length) {
        $('.o_source_menu').ready(function(){
            $("div[id='show_source_button'] a").text("Show Source");
            $("div[id='hide_source_button'] a").text("Hide Source");
            $("div[id='source_menu']").show()
        });
    }

//EDITOR MENU

    if ($('.o_edit_mode').length) {
        $('.o_edit_mode').ready(function(){
            $("div[id='show_button'] a").text("Edit Mode");
            $("div[id='hide_button'] a").text("View Mode");
            $("div[id='editor_menu']").show()
        });
    }

    if ($('.o_editor').length) {
        $('.o_editor').on('click', "a[name='switch_show']", function () {
            $("a[name='switch_show']").parent().hide();
            $("a[name='switch_hide']").parent().show();
            $("div[name='show_items']").show();
            $("tr[name='show_items']").show();
            $("td[name='show_items']").show();
            $("th[name='show_items']").show();
            $("span[name='show_items']").show();
            $("a[name='show_items']").show();
            $("table[name='show_items']").show();
            $("a[name='hide_items']").hide();
            $("span[name='hide_items']").hide();
            $("td[name='hide_items']").hide();
            });
        $('.o_editor').on('click', "a[name='switch_hide']", function () {
            $("a[name='switch_show']").parent().show();
            $("a[name='switch_hide']").parent().hide();
            $("div[name='show_items']").hide();
            $("tr[name='show_items']").hide();
            $("td[name='show_items']").hide();
            $("th[name='show_items']").hide();
            $("span[name='show_items']").hide();
            $("a[name='show_items']").hide();
            $("table[name='show_items']").hide();
            $("a[name='hide_items']").show();
            $("span[name='hide_items']").show();
            $("td[name='hide_items']").show();
            });
        $('.o_editor').on('click', "a[name='show_source']", function () {
            $("a[name='show_source']").parent().hide();
            $("a[name='hide_source']").parent().show();
            $("div[name='source_item']").show();
            $("tr[name='source_item']").show();
            $("td[name='source_item']").show();
            });
        $('.o_editor').on('click', "a[name='hide_source']", function () {
            $("a[name='show_source']").parent().show();
            $("a[name='hide_source']").parent().hide();
            $("div[name='source_item']").hide();
            $("tr[name='source_item']").hide();
            $("td[name='source_item']").hide();
            });
    }


//    TEXT AREA

    $('textarea.load_editor').each(function () {
        var $textarea = $(this);
        var editor_karma = $textarea.data('karma') || 30;  // default value for backward compatibility
        if (!$textarea.val().match(/\S/)) {
            $textarea.val("<p><br/></p>");
        }
        var $form = $textarea.closest('form');
        var toolbar = [
                ['style', ['style']],
                ['font', ['bold', 'italic', 'underline', 'clear']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['table', ['table']],
                ['history', ['undo', 'redo']],
            ];
        if (parseInt($("#karma").val()) >= editor_karma) {
            toolbar.push(['insert', ['link', 'picture']]);
        }
        $textarea.summernote({
                height: 150,
                toolbar: toolbar,
                styleWithSpan: false
            });

        // float-left class messes up the post layout OPW 769721
        $form.find('.note-editable').find('img.float-left').removeClass('float-left');
        $form.on('click', 'button, .a-submit', function () {
            $textarea.html($form.find('.note-editable').code());
        });
    });

//    TRANSLATE BOOK

    if ($('.o_trans_book').length) {
        var book_options = $("select[name='book_id']:enabled option:not(:first)");
        $('.o_trans_book').on('change', "select[name='bible_id']", function () {
            var select = $("select[name='book_id']");
            book_options.detach();
            var displayed_book = book_options.filter("[data-bible_id="+($(this).val() || 0)+"]");
            var nb = displayed_book.appendTo(select).show().size();
            select.parent().toggle(nb>=1);
            if (nb>=1) {
                $("div[id='new_book']").show();
                $("div[id='new_bible']").hide();
            } else {
                $("div[id='new_book']").show();
                $("div[id='new_bible']").show();
            }
        });
        $('.o_trans_book').on('click', "select[name='book_id']", function () {
            if ($(this).val() || 0){
                    $("div[id='new_book']").hide();
                    $("div[id='new_bible']").hide();
            } else {
                    $("div[id='new_book']").show();
                    $("div[id='new_bible']").hide();
            }
        });
        $('.o_trans_book').find("select[name='bible_id']").change();
        $('.o_trans_book').find("select[name='book_id']").change();
    }

//SOURCING MENU

    if ($('.o_sourcing_b').length) {
        var submit_sourcing_b = function () {
            var bible = $("input[name='bible_id']").val();
            var book = $("input[name='book_id']").val();
            var s_chapter = $("input[name='s_chapter_id']").val();
            ajax.jsonRpc('/submit/sourcing/', 'call', {
                bible_id: bible,
                book_id: book,
                s_chapter_id: s_chapter,
                }).then(function (data) {
                    if (data.s_chapter_id != null){
                        $("h2[id='report']").empty().text(data.s_chapter_id);
                        $("input[name='bible_id']").val(data.bible_id);
                        $("input[name='book_id']").val(data.book_id);
                        $("input[name='s_chapter_id']").val(data.s_chapter_id);
                        submit_sourcing_b();
                    } else if (data.bible_id != null) {
                    self.location = "/bible/" + data.bible_id;
                    } else if (data.book_id != null) {
                    self.location = "/book/" + data.book_id;
                    } else {
                    self.location = "/";
                    }
                });
            };

        $('.o_sourcing_b').ready(function(){
            submit_sourcing_b();
        });
    }

    if ($('.o_copying_b').length) {
        var submit_copying_b = function () {
            var bible = $("input[name='bible_id']").val();
            var book = $("input[name='book_id']").val();
            var s_chapter = $("input[name='s_chapter_id']").val();
            ajax.jsonRpc('/copying/source/', 'call', {
                bible_id: bible,
                book_id: book,
                s_chapter_id: s_chapter,
                }).then(function (data) {
                    if (data.s_chapter_id != null){
                        $("h2[id='report']").empty().text(data.s_chapter_id);
                        $("input[name='bible_id']").val(data.bible_id);
                        $("input[name='book_id']").val(data.book_id);
                        $("input[name='s_chapter_id']").val(data.s_chapter_id);
                        submit_copying_b();
                    } else if (data.bible_id != null) {
                    self.location = "/bible/" + data.bible_id;
                    } else if (data.book_id != null) {
                    self.location = "/book/" + data.book_id;
                    } else {
                    self.location = "/";
                    }
                });
            };

        $('.o_copying_b').ready(function(){
            submit_copying_b();
        });
    }

    if ($('.o_remove_source').length) {
        var submit_copying_b = function () {
            var bible = $("input[name='bible_id']").val();
            var book = $("input[name='book_id']").val();
            var s_chapter = $("input[name='s_chapter_id']").val();
            ajax.jsonRpc('/remove/source/', 'call', {
                bible_id: bible,
                book_id: book,
                s_chapter_id: s_chapter,
                }).then(function (data) {
                    if (data.s_chapter_id != null){
                        $("h2[id='report']").empty().text(data.s_chapter_id);
                        $("input[name='bible_id']").val(data.bible_id);
                        $("input[name='book_id']").val(data.book_id);
                        $("input[name='s_chapter_id']").val(data.s_chapter_id);
                        submit_copying_b();
                    } else if (data.bible_id != null) {
                    self.location = "/bible/" + data.bible_id;
                    } else if (data.book_id != null) {
                    self.location = "/book/" + data.book_id;
                    } else {
                    self.location = "/";
                    }
                });
            };

        $('.o_remove_source').ready(function(){
            submit_copying_b();
        });
    }

    if ($('.o_remove').length) {
        var submit_copying_b = function () {
            var bible = $("input[name='bible_id']").val();
            var chapter = $("input[name='chapter_id']").val();
            ajax.jsonRpc('/remove/p/', 'call', {
                bible_id: bible,
                chapter_id: chapter,
                }).then(function (data) {
                    if (data.chapter_id != null){
                        $("h2[id='report']").empty().text(data.chapter_id);
                        $("input[name='bible_id']").val(data.bible_id);
                        $("input[name='chapter_id']").val(data.chapter_id);
                        submit_copying_b();
                    } else if (data.bible_id != null) {
                    self.location = "/bible/" + data.bible_id;
                    } else {
                    self.location = "/my/home";
                    }
                });
            };

        $('.o_remove').ready(function(){
            submit_copying_b();
        });
    }

    if ($('.o_cleaning').length) {
        var submit_copying_b = function () {
            var chapter = $("input[name='chapter_id']").val();
            ajax.jsonRpc('/cleaning/p/', 'call', {
                chapter_id: chapter,
                }).then(function (data) {
                    if (data.chapter_id != null){
                        $("h2[id='report']").empty().text(data.chapter_id);
                        $("input[name='chapter_id']").val(data.chapter_id);
                        submit_copying_b();
                    } else {
                        $("#install_next_button").click();
                    }
                });
            };

        $('.o_cleaning').ready(function(){
            submit_copying_b();
        });
    }

// SELECT DICTIONARY
    if ($('.o_select_dictionary').length) {
        var source_lang = $("input[name='source_lang_id']:enabled").val();
        var target_lang_options = $("select[name='target_lang_id']:enabled");
        var dictionary_options = $("select[name='dictionary_id']:enabled");

        $('.o_select_dictionary').ready(function(){
            dictionary_options.parent().hide();
            ajax.jsonRpc('/get/target_langs/', 'call', {
                  source_lang_id: source_lang,
                }).then(function (target_langs) {
                if (target_langs){
                    var i;
                    for (i = 0; i < target_langs.length; i++) {
                        target_lang_options.append('<option value="' + target_langs[i].id + '">' + target_langs[i].name + '</option>');
                    };
                    if (i>0){target_lang_options.parent().show();};
                };
            });
        });
        if (target_lang_options.length >= 1) {
            target_lang_options.on('change', target_lang_options, function () {
                dictionary_options.children('option:not(:first)').remove();
                dictionary_options.parent().hide();
                var target_lang = target_lang_options.val();
                ajax.jsonRpc('/get/dictionaries/', 'call', {
                      source_lang_id: source_lang,
                      target_lang_id: target_lang,
                    }).then(function (dictionaries) {
                    if (dictionaries){
                        console.log(dictionaries);
                        var i;
                        for (i = 0; i < dictionaries.length; i++) {
                            dictionary_options.append('<option value="' + dictionaries[i].id + '">' + dictionaries[i].name + '</option>');
                        };
                    if (i>0){dictionary_options.parent().show();};
                    };
                });
            });
        }
    }

// SELECT BOOK DICTIONARY
    if ($('.o_select_book_dictionary').length) {
        var source_lang = $("input[name='source_lang_id']:enabled").val();
        var target_lang_options = $("select[name='target_lang_id']:enabled");
        var dictionary_options = $("select[name='dictio_id']:enabled");

        $('.o_select_dictionary').ready(function(){
            dictionary_options.parent().hide();
            ajax.jsonRpc('/get/target_langs/', 'call', {
                  source_lang_id: source_lang,
                }).then(function (target_langs) {
                if (target_langs){
                    var i;
                    for (i = 0; i < target_langs.length; i++) {
                        target_lang_options.append('<option value="' + target_langs[i].id + '">' + target_langs[i].name + '</option>');
                    };
                    if (i>0){target_lang_options.parent().show();};
                };
            });
        });
        if (target_lang_options.length >= 1) {
            target_lang_options.on('change', target_lang_options, function () {
                dictionary_options.children('option:not(:first)').remove();
                dictionary_options.parent().hide();
                var target_lang = target_lang_options.val();
                ajax.jsonRpc('/get/dictionaries/', 'call', {
                      source_lang_id: source_lang,
                      target_lang_id: target_lang,
                    }).then(function (dictionaries) {
                    if (dictionaries){
                        console.log(dictionaries);
                        var i;
                        for (i = 0; i < dictionaries.length; i++) {
                            dictionary_options.append('<option value="' + dictionaries[i].id + '">' + dictionaries[i].name + '</option>');
                        };
                    if (i>0){dictionary_options.parent().show();};
                    };
                });
            });
        }
    }

// SELECT DICTIONARY BIBLE
    if ($('.o_default_bible').length) {
        var dict_lang = $("input[name='source_lang_id']:enabled").val();
        var bib_options = $("select[name='biblica_id']:enabled");

        $('.o_default_bible').ready(function(){
            ajax.jsonRpc('/get/bibles/', 'call', {
                  lang_id: dict_lang,
                }).then(function (bibles) {
                if (bibles){
                    var i;
                    for (i = 0; i < bibles.length; i++) {
                        bib_options.append('<option value="' + bibles[i].id + '">' + bibles[i].name + '</option>');
                    };
                    if (i>0){bib_options.parent().show();};
                };
            });
        });
    }

// SELECT DICTIONARY BIBLE
    if ($('.o_dict_reference').length) {
        var dict_lang = $("input[name='dict_lang_id']:enabled").val();
        var dict_options = $("select[name='dict_reference_id']:enabled");

        $('.o_dict_reference').ready(function(){
            ajax.jsonRpc('/get/dict_ref/', 'call', {
                  dict_lang_id: dict_lang,
                }).then(function (dicts) {
                if (dicts){
                    var i;
                    for (i = 0; i < dicts.length; i++) {
                        dict_options.append('<option value="' + dicts[i].id + '">' + dicts[i].name + '</option>');
                    };
                    if (i>0){dict_options.parent().show();};
                };
            });
        });
    }

});