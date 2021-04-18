# -*- coding: utf-8 -*-
from copy import deepcopy
from difflib import SequenceMatcher
from IPython.core.display import Image
from IPython.core.display import JSON
from json import JSONDecodeError
from lunr.builder import Builder
from lunr.stemmer import stemmer
from lunr.stop_word_filter import stop_word_filter
from lunr.trimmer import trimmer
from operator import itemgetter
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from robotkernel.constants import HAS_RF32_PARSER
import base64
import json
import os
import pygments
import re


try:
    from robot.libdocpkg.htmlutils import DocToHtml
except ImportError:  # < RF40
    from robot.libdocpkg.htmlwriter import DocToHtml


if HAS_RF32_PARSER:

    class Documentation:
        pass  # No longer with RF32


else:
    from robot.parsing.settings import Documentation


def javascript_uri(html, filename=""):
    """Because data-uri for text/html is not supported by IE."""
    if isinstance(html, str):
        html = html.encode("utf-8")
    return (
        "javascript:(function(el){{"
        "var w=window.open();var d='{}';"
        "w.document.open();"
        "w.document.write(window.atob(d));"
        "w.document.close();"
        "var a=w.document.createElement('a');"
        "a.appendChild(w.document.createTextNode('Download'));"
        "a.href='data:text/html;base64,' + d;"
        "a.download='{}';"
        "a.style='position:fixed;top:0;right:0;"
        "color:white;background:black;text-decoration:none;"
        "font-weight:bold;padding:7px 14px;border-radius:0 0 0 5px;';"
        "w.document.body.append(a);"
        "}})(this);".format(base64.b64encode(html).decode("utf-8"), filename)
    )


def data_uri(mimetype, data):
    return "data:{};base64,{}".format(mimetype, base64.b64encode(data).decode("utf-8"))


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


def readable_keyword(s):
    """Return keyword with only the first letter in title case."""
    if s and not s.startswith("*") and not s.startswith("["):
        if s.count("."):
            library, name = s.rsplit(".", 1)
            return library + "." + name[0].title() + name[1:].lower()
        else:
            return s[0].title() + s[1:].lower()
    else:
        return s


def detect_robot_context(code, cursor_pos):
    """Return robot code context in cursor position."""
    code = code[:cursor_pos]
    line = code.rsplit("\n")[-1]
    context_parts = code.rsplit("***", 2)
    if len(context_parts) != 3:
        return "__root__"
    else:
        context_name = context_parts[1].strip().lower()
        if context_name == "settings":
            return "__settings__"
        elif line.lstrip() == line:
            return "__root__"
        elif context_name in ["tasks", "test cases"]:
            return "__tasks__"
        elif context_name == "keywords":
            return "__keywords__"
        else:
            return "__root__"


NAME_REGEXP = re.compile("`(.+?)`")


def get_keyword_doc(keyword):
    title = keyword.name.strip("*").strip()
    title_html = f"<strong>{title}</strong>"
    if keyword.args:
        try:
            title += " " + ", ".join(keyword.args)
            title_html += " " + ", ".join(keyword.args)
        except TypeError:  # RF >= 4.0
            # TODO: Include default values and typing
            args = (
                keyword.args.positional_only
                + keyword.args.named_only
                + keyword.args.positional_or_named
            )
            title += " " + ", ".join(args)
            title_html += " " + ", ".join(args)
    body = ""
    if keyword.doc:
        if isinstance(keyword.doc, Documentation):
            body = "\n\n" + keyword.doc.value.replace("\\n", "\n")
        else:
            body = "\n\n" + keyword.doc
    return {
        "text/plain": title + "\n\n" + body,
        "text/html": f"<p>{title_html}</p>"
        + NAME_REGEXP.sub(
            lambda m: f"<code>{m.group(1)}</code>", DocToHtml(keyword.doc_format)(body)
        ),
    }


def scored_results(needle, results):
    results = deepcopy(results)
    for result in results:
        match = SequenceMatcher(
            None, needle.lower(), result["ref"].lower(), autojunk=False
        ).find_longest_match(0, len(needle), 0, len(result["ref"]))
        result["score"] = (match.size, match.size / float(len(result["ref"])))
    return list(reversed(sorted(results, key=itemgetter("score"))))


def lunr_query(query):
    query = re.sub(r"([:*])", r"\\\1", query, re.U)
    query = re.sub(r"[\[\]]", r"", query, re.U)
    return f"*{query.strip().lower()}*"


def get_lunr_completions(needle, index, keywords, context):
    matches = []
    results = []
    if needle.rstrip():
        query = lunr_query(needle)
        results = index.search(query)
        results += index.search(query.strip("*"))
    for result in scored_results(needle, results):
        ref = result["ref"]
        if ref.startswith("__") and not ref.startswith(context):
            continue
        if not ref.startswith(context) and context not in [
            "__tasks__",
            "__keywords__",
            "__settings__",
        ]:
            continue
        if not needle.count("."):
            keyword = keywords[ref].name
            if keyword not in matches:
                matches.append(readable_keyword(keyword))
        else:
            matches.append(readable_keyword(ref))
    return matches


def to_html(obj):
    """Return object as highlighted JSON."""
    return highlight("json", json.dumps(obj, sort_keys=False, indent=4))


# noinspection PyProtectedMember
def to_mime_and_metadata(obj) -> (dict, dict):  # noqa: C901
    if isinstance(obj, bytes):
        obj = base64.b64encode(obj).decode("utf-8")
        return {"text/html": to_html(obj)}, {}
    elif isinstance(obj, str) and obj.startswith("http"):
        if re.match(r".*\.(gif|jpg|svg|jpeg||png)$", obj, re.I):
            try:
                return Image(obj, embed=True)._repr_mimebundle_()
            except TypeError:
                pass
        return {"text/html": to_html(obj)}, {}
    elif isinstance(obj, str) and len(obj) < 1024 and os.path.exists(obj):
        if re.match(r".*\.(gif|jpg|svg|jpeg||png)$", obj, re.I):
            try:
                return Image(obj, embed=True)._repr_mimebundle_()
            except TypeError:
                pass
        return {"text/html": to_html(obj)}, {}
    elif hasattr(obj, "_repr_mimebundle_"):
        obj.embed = True
        return obj._repr_mimebundle_()
    elif hasattr(obj, "_repr_json_"):
        obj.embed = True
        return {"application/json": obj._repr_json_()}, {}
    elif hasattr(obj, "_repr_html_"):
        obj.embed = True
        return {"text/html": obj._repr_html_()}, {}
    elif hasattr(obj, "_repr_png_"):
        return {"image/png": obj._repr_png_()}, {}
    elif hasattr(obj, "_repr_jpeg_"):
        return {"image/jpeg": obj._repr_jpeg_()}, {}
    elif hasattr(obj, "_repr_svg_"):
        return {"image/svg": obj._repr_svg_()}, {}
    try:
        if isinstance(obj, str):
            return {"text/html": f"<pre>{to_html(obj)}</pre>".replace("\\n", "\n")}, {}
        else:
            data, metadata = JSON(data=obj, expanded=True)._repr_json_()
            return (
                {"application/json": data, "text/html": f"<pre>{to_html(obj)}</pre>"},
                metadata,
            )
    except (TypeError, JSONDecodeError):
        pass
    try:
        return {"text/html": to_html(obj)}, {}
    except TypeError:
        return {}, {}


def yield_current_connection(connections, types_):
    for instance in [
        connection["instance"]
        for connection in connections
        if connection["type"] in types_ and connection["current"]
    ]:
        yield instance
        break


def close_current_connection(connections, connection_to_close):
    match = None
    for connection in connections:
        if connection["instance"] is connection_to_close:
            match = connection
            break
    if match is not None:
        if hasattr(match["instance"], "quit"):
            match["instance"].quit()
        connections.remove(match)
