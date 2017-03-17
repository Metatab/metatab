# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Create Markdown and HTML of datasets.
"""

from markdown import markdown as convert_markdown
from rowgenerators.fetch import download_and_cache
from rowgenerators import SourceSpec

dl_templ = "{}\n:   {}\n\n"

def ns(v):
    """Return empty str if boll false"""
    return str(v) if bool(v) else ''

def linkify(v, description = None, cwd_url=None):
    from rowgenerators import Url
    from os.path import abspath

    if not v:
        return None

    u = Url(v)


    if u.scheme in ('http','https','mailto'):

        if description is None:
            description = v
        return '[{desc}]({url})'.format(url=v, desc = description)

    elif u.scheme == 'file':

        return '[{desc}](file:{url})'.format(url=u.parts.path, desc=description)

    else:
        return v


def resource(r):
    return ("### {name} \n [{url}]({url})\n\n".format(name=r.name, url=r.url)) + \
           "{}\n".format(ns(r.description))+ \
           "<table class=\"table table-striped\">\n" + \
           "<tr><th>Header</th><th>Type</th><th>Description</th></tr>" + \
           '\n'.join(
               "<tr><td>{}</td><td>{}</td><td>{}</td></tr> ".format(c['header'], c['datatype'], c['description'])
               for c in r.columns()) + \
           '</table>\n'

def resource_block(doc):

    return "".join(resource(r) for r in doc.resources())

def resource_ref(r):

    return dl_templ.format(r.name,"_{}_<br/>{}".format(r.url,ns(r.description)))

def resource_ref_block(doc):

    return "".join(resource_ref(r) for r in doc.resources())


def contact(r):
    pass

def contacts_block(doc):

    out = ''

    try:

        for t in doc['Contacts']:
            p = t.properties
            name = p.get('name', 'Name')
            email = "mailto:" + p.get('email') if p.get('email') else None

            web = p.get('url')
            org = p.get('organization', web)

            out += (dl_templ
                    .format(t.record_term.title(),
                            (linkify(email, name) or '') + " " + (linkify(web, org) or '')
                            ))

    except KeyError:
        pass

    return out

def documentation_block(doc):

    doc_links = ''

    inline = ''

    notes = []

    try:
        for t in doc['Documentation']:

            if t.term_is('Root.IncludeDocumentation'):
                paths = download_and_cache(SourceSpec(t.value), cache_fs=doc._cache)

                with open(paths['sys_path']) as f:
                    inline += f.read()

            elif t.properties.get('url'):

                doc_links += (dl_templ
                        .format(linkify(t.properties.get('url'), t.properties.get('title')),
                                t.properties.get('description')
                                ))

            elif t.term_is('Root.Note'):
                notes.append(t.value)
            else:
                doc_links += (dl_templ.format(t.record_term.title(), t.value))


    except KeyError:
        raise
        pass




    return inline + \
           ("\n\n## Notes \n\n" + "\n".join('* '+n for n in notes) ) if notes else '' +\
           ("\n\n## Documentation Links\n"+doc_links if doc_links else '')

def identity_block(doc):

    from collections import OrderedDict


    name = doc.find_first('Root.Name')

    d = OrderedDict(
        name = name.value,
        identifier = doc.find_first_value('Root.Identifier'),
    )

    for k, v in name.as_dict().items():
        d[k] = v

    del d['@value']

    return "".join(dl_templ.format(k, v) for k,v in d.items())


def markdown(doc):
    """Markdown, specifically for the Notes field in a CKAN dataset"""

    name = doc.find_first('Root.Name')

    text = """

`{name}`

_{description}_

{doc_block}

## Contacts

{contacts_block}

""".format(
        title=doc.find_first_value('Root.Title'),
        description=doc.find_first_value('Root.Description'),
        name=doc.find_first_value('Root.Name'),
        doc_block=documentation_block(doc),
        contacts_block = contacts_block(doc)
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
        description=doc.find_first_value('Root.Description'),
        identity_block=mdc(identity_block(doc)).replace('<dl>', "<dl class=\"dl-horizontal\">"),
        doc_block=mdc(documentation_block(doc)),
        contacts_block=mdc(contacts_block(doc)).replace('<dl>', "<dl class=\"dl-horizontal\">"),
        resource_refs=mdc(resource_ref_block(doc)).replace('<dl>', "<dl class=\"dl-horizontal\">"),
        resource_block=mdc(resource_block(doc))
    )



