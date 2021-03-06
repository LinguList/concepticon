"""
This module will be available in templates as ``u``.

This module is also used to lookup custom template context providers, i.e. functions
following a special naming convention which are called to update the template context
before rendering resource's detail or index views.
"""
import re
from itertools import groupby

from markdown import markdown

from clld.web.util.helpers import get_referents, external_link
from clld.web.util.htmllib import HTML
from clld.db.models.common import Contribution, Source


REF_PATTERN = re.compile(':ref:(?P<id>[^\)]+)')


def link_conceptlists(req, s):
    if not s:
        return ''  # pragma: no cover

    def repl(m):
        ref = Contribution.get(m.group('id'), default=None)
        return req.resource_url(ref) if ref else m.group('id')

    return markdown(REF_PATTERN.sub(repl, s))


def render_kv(meta):
    value = meta.value
    if meta.valueUrl:
        value = external_link(meta.valueUrl, label=meta.value)
    return meta.key.replace('_', ' '), value


def render_metadata(ctx):
    rows = []
    for provider, md in groupby(ctx.meta, lambda m: m.metaprovider):
        rows.append(HTML.tr(
            HTML.th(external_link(provider.url, label=provider.name), colspan='2')))
        for meta in md:
            key, value = render_kv(meta)
            rows.append(HTML.tr(HTML.td(key), HTML.td(value)))
    return HTML.table(HTML.tbody(*rows), class_='table table-condensed')


def dataset_detail_html(request=None, context=None, **kw):
    return {
        'Kraft1981': Source.get('kraft1981'),
    }


def source_detail_html(context=None, request=None, **kw):
    return dict(referents=get_referents(context, exclude=['valueset', 'language']))
