from __future__ import unicode_literals
import sys
import re

from clld.scripts.util import initializedb, Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib.bibtex import Database
from clld.lib.dsv import reader
from clld.util import slug

import concepticon
from concepticon import models


def split(s, sep=','):
    return [ss.strip() for ss in s.split(sep) if ss.strip()]


def main(args):
    data = Data()
    data_path = lambda *cs: args.data_file('concepticon-data', 'concepticondata', *cs)

    dataset = common.Dataset(
        id=concepticon.__name__,
        name="Concepticon",
        publisher_name="Max Planck Institute for Evolutionary Anthropology",
        publisher_place="Leipzig",
        publisher_url="http://www.eva.mpg.de",
        license="http://creativecommons.org/licenses/by/4.0/",
        domain='concepticon.clld.org',
        jsondata={
            'license_icon': 'cc-by.png',
            'license_name': 'Creative Commons Attribution 4.0 International License'})
    DBSession.add(dataset)
    for i, name in enumerate(['Johann-Mattis List', 'Michael Cysouw', 'Robert Forkel']):
        c = common.Contributor(id=slug(name), name=name)
        dataset.editors.append(common.Editor(contributor=c, ord=i))

    english = data.add(
        common.Language, 'eng',
        id='eng',
        name='English')

    files = {}
    for fname in data_path('sources').files():
        files[fname.namebase] = \
            "https://github.com/clld/concepticon-data/blob/master/concepticondata/sources/%s" % fname.name

    for rec in Database.from_file(
            data_path('references', 'references.bib'), lowercase=True):
        source = data.add(common.Source, rec.id, _obj=bibtex2source(rec))
        if rec.id in files:
            DBSession.flush()
            DBSession.add(common.Source_files(
                mime_type='application/pdf',
                object_pk=source.pk,
                jsondata=dict(url=files[rec.id])))

    for concept in reader(data_path('concepticon.tsv'), namedtuples=True):
        data.add(
            models.ConceptSet,
            concept.ID,
            id=concept.ID,
            omegawiki=concept.OMEGAWIKI,
            name=concept.GLOSS,
            description=concept.DEFINITION,
            semanticfield=concept.SEMANTICFIELD,
            ontological_category=concept.ONTOLOGICAL_CATEGORY)

    unmapped = 0
    number_pattern = re.compile('(?P<number>[0-9]+)(?P<suffix>.*)')

    for cl in reader(data_path('conceptlists.tsv'), dicts=True):
        concepts = data_path('conceptlists', '%(ID)s.tsv' % cl)
        if not concepts.exists():
            continue
        langs = [l.lower() for l in split(cl['SOURCE_LANGUAGE'])]
        conceptlist = data.add(
            models.Conceptlist,
            cl['ID'],
            id=cl['ID'],
            name=' '.join(cl['ID'].split('-')),
            description=cl['NOTE'],
            target_languages=cl['TARGET_LANGUAGE'],
            source_languages=' '.join(langs),
            year=int(cl['YEAR']) if cl['YEAR'] else None,
        )
        for id_ in split(cl['REFS']):
            common.ContributionReference(
                source=data['Source'][id_], contribution=conceptlist)
        for i, name in enumerate(split(cl['AUTHOR'], sep=' and ')):
                contrib = data['Contributor'].get(name)
                if not contrib:
                    contrib = data.add(
                        common.Contributor, name, id=slug(name), name=name)
                DBSession.add(common.ContributionContributor(
                    ord=i, contribution=conceptlist, contributor=contrib))
        for k in 'ID NOTE TARGET_LANGUAGE SOURCE_LANGUAGE YEAR REFS AUTHOR'.split():
            del cl[k]
        DBSession.flush()
        for k, v in cl.items():
            DBSession.add(common.Contribution_data(
                object_pk=conceptlist.pk, key=k, value=v))

        for concept in reader(concepts, namedtuples=True):
            if not concept.ID or not concept.CONCEPTICON_ID or concept.CONCEPTICON_ID == 'NAN':
                unmapped += 1
                continue

            lgs = {}
            for lang in langs:
                v = getattr(concept, lang.upper())
                if v:
                    lgs[lang] = v

            match = number_pattern.match(concept.NUMBER)
            vs = common.ValueSet(
                id=concept.ID,
                description=getattr(concept, 'GLOSS', getattr(concept, 'ENGLISH', None)),
                language=english,
                contribution=conceptlist,
                parameter=data['ConceptSet'][concept.CONCEPTICON_ID])
            d = {}
            for key, value in concept.__dict__.items():
                if not key.startswith('CONCEPTICON_') and \
                        key not in ['NUMBER', 'ID', 'GLOSS'] + [l.upper() for l in langs]:
                    d[key.lower()] = value
            v = models.Concept(
                id=concept.ID,
                valueset=vs,
                description=getattr(concept, 'GLOSS', None),  # our own gloss, if available
                name='; '.join('%s [%s]' % (lgs[l], l) for l in sorted(lgs.keys())),
                number=int(match.group('number')),
                number_suffix=match.group('suffix'),
                jsondata=d)
            DBSession.flush()
            for key, value in lgs.items():
                DBSession.add(
                    common.Value_data(key='lang_' + key, value=value, object_pk=v.pk))

    print '%s concepts unmapped' % unmapped


def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
    for concept in DBSession.query(models.ConceptSet):
        concept.representation = len(concept.valuesets)

    for clist in DBSession.query(models.Conceptlist):
        clist.items = len(clist.valuesets)


if __name__ == '__main__':
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)
