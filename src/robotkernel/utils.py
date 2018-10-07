# -*- coding: utf-8 -*-
from lunr.builder import Builder
from lunr.stemmer import stemmer
from lunr.stop_word_filter import stop_word_filter
from lunr.trimmer import trimmer
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

import base64
import pygments


def javascript_uri(html):
    """Because data-uri for text/html is not supported by IE"""
    if isinstance(html, str):
        html = html.encode('utf-8')
    return (
        'javascript:(function(){{'
        'var w=window.open();'
        'w.document.open();'
        'w.document.write(window.atob(\'{}\'));'
        'w.document.close();'
        '}})();'.format(base64.b64encode(html).decode('utf-8'))
    )


def data_uri(mimetype, data):
    return 'data:{};base64,{}'.format(
        mimetype,
        base64.b64encode(data).decode('utf-8'),
    )


def highlight(language, data):
    lexer = get_lexer_by_name(language)
    formatter = HtmlFormatter(noclasses=True, nowrap=True)
    return pygments.highlight(data, lexer, formatter)


def lunr_builder(ref, fields):
    """A convenience function to configure and construct a lunr.Builder.

    Returns:
        Index: The populated Index ready to search against.
    """
    builder = Builder()
    builder.pipeline.add(trimmer, stop_word_filter, stemmer)
    builder.search_pipeline.add(stemmer)
    builder.ref(ref)
    for field in fields:
        builder.field(field)
    return builder
