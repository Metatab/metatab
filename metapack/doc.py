# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Extensions to the MetatabDoc, Resources and References, etc.
"""

EMPTY_SOURCE_HEADER = '_NONE_'  # Marker for a column that is in the destination table but not in the source


from metapack.resource import MetapackResource, MetapackReference
from metatab import MetatabDoc
from rowgenerators import Url
from .html import linkify





class MetapackDoc(MetatabDoc):

    @property
    def env(self):
        """Return the module associated with a package's python library"""
        try:
            return self.get_lib_module_dict()
        except ImportError:
            return None

    def get_lib_module_dict(self):
        """Load the 'lib' directory as a python module, so it can be used to provide functions
        for rowpipe transforms. This only works filesystem packages"""

        from os.path import dirname, abspath, join, isdir
        from importlib import import_module
        import sys

        u = Url(self.ref)
        if u.proto == 'file':

            doc_dir = dirname(abspath(u.parts.path))

            # Add the dir with the metatab file to the system path
            sys.path.append(doc_dir)

            if not isdir(join(doc_dir, 'lib')):
                return {}

            try:
                m = import_module("lib")
                return {k: v for k, v in m.__dict__.items() if not k.startswith('__')}
            except ImportError as e:

                raise ImportError("Failed to import python module form 'lib' directory: ", str(e))

        else:
            return {}

    def resources(self, name=None, term='Root.Datafile', section='Resources', env=None, clz=False,
                              code_path=None):

        """Iterate over every root level term that has a 'url' property, or terms that match a find() value or a name value"""

        if clz is False:
            clz = self.resource_class

        base_url = self.package_url if self.package_url else self._ref

        if env is None:
            try:
                env = self.get_lib_module_dict()
            except ImportError:
                pass

        for t in self[section].terms:

            if term and not t.term_is(term):
                continue

            if name and t.get_value('name') != name:
                continue

            if not 'url' in t.arg_props:
                pass

            resource_term = clz(t, base_url, env=env, code_path=code_path)

            yield resource_term


def resource(self, name=None, term='Root.Datafile', section='Resources', env=None,
             clz=False, code_path=None):
    """

    :param name:
    :param term:
    :param env: And environment doc ( like a module ) to pass into the row processor
    :return:
    """

    resources = list(self.resources(name=name, term=term, section=section, env=env, clz=clz,
                                    code_path=code_path))

    if not resources:
        return None

    else:
        r = resources[0]
    return r

    def references(self, name=None, term='Root.Reference', section='References',
                   env=None):
        """
        Like resources(), but by default looks for Root.Reference terms in the References section
        :param name: Value of name property for terms to return
        :param term: Fully qualified term name, defaults to Root.Reference
        :param section: Name of section to look in. Defaults to 'References'
        :param env: Environment dict to be passed into resource row generators.
        :return:
        """

        clz = self.reference_class

        return self.resources(name=name, term=term, section=section, env=env, clz=clz)

    def reference(self, name=None, term='Root.Reference', section='References', env=None):
        """
        Like resource(), but by default looks for Root.Reference terms in the References section

        :param name: Value of name property for terms to return
        :param term: Fully qualified term name, defaults to Root.Reference
        :param section: Name of section to look in. Defaults to 'References'
        :param env: Environment dict to be passed into resource row generators.
        :return:
        """

        clz = self.reference_class

        return self.resource(name=name, term=term, section=section, env=env, clz=clz)

    def distributions(self, type=False):
        """"Return a dict of distributions, or if type is specified, just the first of that type

        """
        from collections import namedtuple

        Dist = namedtuple('Dist', 'type url term')

        def dist_type(url):

            if url.target_file == 'metadata.csv':
                return 'fs'
            elif url.target_format == 'xlsx':
                return 'excel'
            elif url.resource_format == 'zip':
                return "zip"
            elif url.target_format == 'csv':
                return "csv"

            else:

                return "unk"

        dists = []

        for d in self.find('Root.Distribution'):

            u = Url(d.value)

            t = dist_type(u)

            if type == t:
                return Dist(t, u, d)
            elif type is False:
                dists.append(Dist(t, u, d))

        return dists

    def _repr_html_(self, **kwargs):
        """Produce HTML for Jupyter Notebook"""

        def resource_repr(r, anchor=kwargs.get('anchors', False)):
            return "<p><strong>{name}</strong> - <a target=\"_blank\" href=\"{url}\">{url}</a> {description}</p>" \
                .format(name='<a href="#resource-{name}">{name}</a>'.format(name=r.name) if anchor else r.name,
                        description=r.get_value('description', ''),
                        url=r.resolved_url)

        def documentation():

            out = ''

            try:
                self['Documentation']
            except KeyError:
                return ''

            try:
                for t in self['Documentation']:

                    if t.get_value('url'):

                        out += ("\n<p><strong>{} </strong>{}</p>"
                                .format(linkify(t.get_value('url'), t.get_value('title')),
                                        t.get_value('description')
                                        ))

                    else:  # Mostly for notes
                        out += ("\n<p><strong>{}: </strong>{}</p>"
                                .format(t.record_term.title(), t.value))


            except KeyError:
                raise
                pass

            return out

        def contacts():

            out = ''

            try:
                self['Contacts']
            except KeyError:
                return ''

            try:

                for t in self['Contacts']:
                    name = t.get_value('name', 'Name')
                    email = "mailto:" + t.get_value('email') if t.get_value('email') else None

                    web = t.get_value('url')
                    org = t.get_value('organization', web)

                    out += ("\n<p><strong>{}: </strong>{}</p>"
                            .format(t.record_term.title(),
                                    (linkify(email, name) or '') + " " + (linkify(web, org) or '')
                                    ))

            except KeyError:
                pass

            return out

        return """
<h1>{title}</h1>
<p>{name}</p>
<p>{description}</p>
<p>{ref}</p>
<h2>Documentation</h2>
{doc}
<h2>Contacts</h2>
{contact}
<h2>Resources</h2>
<ol>
{resources}
</ol>
""".format(
            title=self.find_first_value('Root.Title', section='Root'),
            name=self.find_first_value('Root.Name', section='Root'),
            ref=self.ref,
            description=self.find_first_value('Root.Description', section='Root'),
            doc=documentation(),
            contact=contacts(),
            resources='\n'.join(["<li>" + resource_repr(r) + "</li>" for r in self.resources()])
        )

    @property
    def html(self):
        from .html import html
        return html(self)

    @property
    def markdown(self):
        from .html import markdown
        return markdown(self)

