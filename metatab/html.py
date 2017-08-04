# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Create Markdown and HTML of datasets.
"""

import six
from markdown import markdown as convert_markdown
from rowgenerators.fetch import download_and_cache
from rowgenerators import SourceSpec

dl_templ = "{}\n:   {}\n\n"


def ns(v):
    """Return empty str if bool false"""
    return str(v) if bool(v) else ''


def linkify(v, description=None, cwd_url=None):
    from rowgenerators import Url
    from os.path import abspath

    if not v:
        return None

    u = Url(v)

    if u.scheme in ('http', 'https', 'mailto'):

        if description is None:
            description = v
        return '[{desc}]({url})'.format(url=v, desc=description)

    elif u.scheme == 'file':

        return '[{desc}]({url})'.format(url=u.parts.path, desc=description)

    else:
        return v


def resource(r, fields=None):
    from operator import itemgetter

    fields = fields or (
        ('Header', 'header'),
        ('Datatype', 'datatype'),
        ('Description', 'description')
    )

    headers = [f[0] for f in fields]
    keys = [f[1] for f in fields]

    rows = [''.join(["<td>{}</td>".format(e.replace("\n", "<br/>\n")) for e in [c.get(k, '') for k in keys]])
            for c in r.columns()]

    return ("### {name} \n [{url}]({url})\n\n".format(name=r.name, url=r.resolved_url)) + \
           "{}\n".format(ns(r.description)) + \
           "<table class=\"table table-striped\">\n" + \
           ("<tr>{}</tr>".format(''.join("<th>{}</th>".format(e) for e in headers))) + \
           "\n".join("<tr>{}</tr>".format(row) for row in rows) + \
           '</table>\n'

def ckan_resource_markdown(r, fields=None):

    fields = fields or (
        ('Header', 'header'),
        ('Datatype', 'datatype'),
        ('Description', 'description')
    )

    headers = [f[0] for f in fields]
    keys = [f[1] for f in fields]


    def col_line(c):
        return "* **{}** ({}): {}\n".format(
            c.get('header'),
            c.get('datatype'),
            "*{}*".format(c.get('description')) if c.get('description') else '')

    return "### {}. {} Columns. \n\n{}".format(
        ns(r.description),
        len(list(r.columns())),
        ''.join([col_line(c) for c in r.columns()])
    )



def resource_block(doc, fields=None):
    import sys

    if fields is None:
        fields = [
            ('Header', 'header'),
            ('Datatype', 'datatype'),
            ('Description', 'description')
        ]

        for h in doc['Schema'].args:

            if h.lower() in ('note', 'notes', 'coding'):
                fields.append((h, h.lower()))

    return "".join(resource(r, fields) for r in doc.resources())


def resource_ref(r):
    return dl_templ.format(r.name, "_{}_<br/>{}".format(r.resolved_url, ns(r.description)))


def resource_ref_block(doc):
    return "".join(resource_ref(r) for r in doc.resources())


def contact(r):
    pass


def contacts_block(doc):
    out = ''

    def mklink(url, desc):
        return '[{desc}]({url})'.format(url=url, desc=desc)

    def ctb(url, desc):

        if url and desc:
            return mklink(url, desc)

        elif url:
            return url

        elif desc:
            return desc

        else:
            return ''

    try:

        for t in doc['Contacts']:
            p = t.properties
            name = p.get('name')
            email = "mailto:" + p.get('email') if p.get('email') else None

            web = p.get('url')
            org = p.get('organization', web)

            out += (dl_templ.format(t.record_term.title(),
                                    ', '.join(e for e in (ctb(email, name), ctb(web, org)) if e)))

    except KeyError:
        pass

    return out


def documentation_block(doc):
    doc_links = ''

    inline = ''

    notes = []

    try:
        doc['Documentation']
    except KeyError:
        return ''

    try:

        for t in doc.resources(term='Root.IncludeDocumentation', section='Documentation'):
            paths = download_and_cache(SourceSpec(t.value), cache_fs=doc._cache)

            with open(paths['sys_path']) as f:
                inline += f.read()

        for t in doc.resources(term=['Root.Documentation'], section='Documentation'):

                if t.properties.get('description'):
                    dl_templ = "{}\n:   {}\n\n"
                else:
                    dl_templ = "{} {}\n\n"

                doc_links += (dl_templ
                              .format(linkify(t.resolved_url,
                                              t.properties.get('title')),
                                      t.properties.get('description')
                                      ))
        # The doc_img alt text is so we can set a class for CSS to resize the image.
        # img[alt=doc_img] { width: 100 px; }

        for t in doc.resources(term=['Root.Image'], section='Documentation'):
            doc_links += ('[![{}]({} "{}")]({})'
                          .format('doc_img', t.resolved_url, t.properties.get('title'),
                                  t.resolved_url))


        for t in doc.resources(term='Root.Note', section='Documentation'):

            notes.append(t.value)


    except KeyError:
        raise
        pass

    return inline + \
           (("\n\n## Notes \n\n" + "\n".join('* ' + n for n in notes if n)) if notes else '') + \
           ("\n\n## Documentation Links\n" + doc_links if doc_links else '')


from pybtex.style.formatting.plain import Style
from pybtex.backends.html import Backend

from pybtex.style.formatting import toplevel, find_plugin
from pybtex.style.template import (
    join, words, together, field, optional, first_of,
    names, sentence, tag, optional_field, href
)
from pybtex.richtext import Text, Symbol
class MetatabStyle(Style):
    # Minnesota Population Center. IPUMS Higher Ed: Version 1.0 [dataset]
    # Minneapolis, MN: University of Minnesota, 2016. http://doi.org/10.18128/D100.V1.0.

    def format_url(self, e):

        return words [
            href [
                field('url', raw=True),
                field('url', raw=True)
                ]
        ]

    def format_accessed(self, e):
        from dateutil.parser import parser

        return words [
            'Accessed',
            field('accessdate', raw=True, apply_func=lambda v: str(parser().parse(v).strftime("%d %b %Y")))
        ]

    def format_dataset(self, e):
        date = words[optional_field('month'), field('year')]

        template = toplevel[
            self.format_author_or_editor(e),
            self.format_btitle(e, 'title'),
            sentence[together[ 'Version', optional_field('version')]],
            sentence[
                field('publisher'),
                date
            ],
            self.format_web_refs(e),
            self.format_accessed(e)
        ]


        return template.format_data(e)

class MetatabHtmlBackend(Backend):

    def write_prologue(self):
        pass
        #super().write_prologue()

    def write_epilogue(self):
        pass
        #super().write_epilogue()

    def write_entry(self, key, label, text):
        self.output("<div class='citation'><a name=\"{key}\"><b>[{key}]</b></a> {text} </div>"
                    .format(key=key, text=text))


def citation(t):
    from pybtex import PybtexEngine
    from nameparser import HumanName
    from yaml import safe_dump

    d = t.as_dict()
    if 'author' in d:
        authors = []
        for e in d['author'].split(';'):
            author_d = HumanName(e).as_dict(include_empty=False)
            if 'suffix' in author_d:
                author_d['lineage'] = author_d['suffix']
                del author_d['suffix']
            authors.append(author_d)
        d['author'] = authors

    return PybtexEngine().format_from_string(safe_dump({ 'entries' : {  t.value : d } }),
                                             style=MetatabStyle,
                                             output_backend=MetatabHtmlBackend,
                                             bib_format='yaml')

def bibliography(doc):

    entries = []

    for t in doc.get_section('Bibliography', []):
        entries.append(citation(t))

    return '\n'.join(entries)




def identity_block(doc):
    from collections import OrderedDict

    name = doc.find_first('Root.Name')

    d = OrderedDict(
        name=name.value,
        identifier=doc.find_first_value('Root.Identifier'),
    )

    for k, v in name.properties.items():
        d[k] = v

    del d['@value']

    return "".join(dl_templ.format(k, v) for k, v in d.items())


def modtime_str(doc):
    from dateutil.parser import parse

    modtime = doc.find_first_value('Root.Modified') or doc.find_first_value('Root.Issued')

    if modtime:
        try:
            modtime_str = "Last Modified: " + parse(modtime).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            modtime_str = ''

    else:

        modtime_str = ''

    return modtime_str

def markdown(doc):
    """Markdown, specifically for the Notes field in a CKAN dataset"""

    name = doc.find_first('Root.Name')

    text = """

`{name}` {modtime}

_{description}_

{doc_block}

## Contacts

{contacts_block}

""".format(
        title=doc.find_first_value('Root.Title'),
        modtime=modtime_str(doc),
        description=doc.find_first_value('Root.Description'),
        name=doc.find_first_value('Root.Name'),
        doc_block=documentation_block(doc),
        contacts_block=contacts_block(doc)
    )

    return text


def html(doc):
    extensions = [
        'markdown.extensions.extra',
        'markdown.extensions.admonition'
    ]

    def mdc(text):
        return convert_markdown(text, extensions)

    return """
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

    <style>
    .narrow-dl .dl-horizontal dd {{
        margin-left: 100px;
    }}

    .narrow-dl .dl-horizontal dt {{
        width: 80px;
    }}

    </style>
    <title>{title}</title>
</head>
<body>
    <div class="container">
        <div class="row">
            <div class="col-md-12">
                <h1>{title}</h1>
                <p>{modtime}</p>
                <p>{description}</p>
            </div>
        </div>
        <div class="row">
            <div class="col-md-7">
                <h2>Documentation</h2>
                {doc_block}
                <h2>Resources</h2>
                {resource_refs}
            </div>
            <div class="col-md-5 narrow-dl">
                <h2>Identity</h2>
                {identity_block}
                <h2>Contacts</h2>
                {contacts_block}
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
            {resource_block}
            </div>
        </div>
    </div>

</body>
</html>
    """.format(
        title=doc.find_first_value('Root.Title'),
        modtime=modtime_str(doc),
        description=doc.find_first_value('Root.Description'),
        identity_block=mdc(identity_block(doc)).replace('<dl>', "<dl class=\"dl-horizontal\">"),
        doc_block=mdc(documentation_block(doc)),
        contacts_block=mdc(contacts_block(doc)).replace('<dl>', "<dl class=\"dl-horizontal\">"),
        resource_refs=mdc(resource_ref_block(doc)).replace('<dl>', "<dl class=\"dl-horizontal\">"),
        resource_block=mdc(resource_block(doc))
    )
