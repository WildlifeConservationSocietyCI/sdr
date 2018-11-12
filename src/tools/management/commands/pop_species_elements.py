from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max
from base.models import Reference
from species.models import Species, Taxon
from muirweb.models import Element


class Command(BaseCommand):
    help = 'Kill local processes running runserver command'

    def __init__(self):
        super(Command, self).__init__()

    def add_arguments(self, parser):
        parser.add_argument('taxon', nargs='?', type=str)
        parser.add_argument('-c', action='store_true', dest='clear',
                            default=False, help='Clear existing elements before populating'),

    def handle(self, *args, **options):
        taxon_name = options.get('taxon')
        try:
            taxon = Taxon.objects.get(name=taxon_name).pk
        except Taxon.DoesNotExist:
            raise CommandError('Taxon does not exist: {}'.format(taxon_name))
        species = Species.objects.filter(taxon=taxon, historical_likelihood_id__lte=2).order_by('name_accepted')

        clear = options.get('clear')
        if clear:
            Element.objects.filter(species__taxon=taxon).delete()

        taxon_ranges = {
            "mammals": 1000,
            "birds": 2000,
            "reptiles": 4000,
            "amphibians": 5000,
            "fish": 6000,
            "plants": 10000,
            "freshwater inverts": 20000,
            "green algae": 30000,
        }

        if species.count() > 0:
            mwid = taxon_ranges[taxon_name]
            max_mwid = Element.objects.filter(species__taxon=taxon).aggregate(Max('elementid'))['elementid__max']
            if max_mwid is not None:
                mwid = int(max_mwid)
            for s in species:
                if s.name_accepted and s.name_accepted != '':
                    try:
                        e = Element.objects.get(species=s)
                    except Element.DoesNotExist:
                        e = Element(species=s)
                        e.elementid = Decimal('{}.00'.format(mwid))
                    e.name = s.__str__().strip()
                    e.description = s.composite_habitat
                    e.save()
                    refs = [r.reference for r in s.speciesreference_set.all()]
                    for r in refs:
                        ref = {k: v for (k, v) in r.__dict__.items() if not k.startswith('_')}
                        reference, _ = Reference.objects.get_or_create(**ref)
                        e.references.add(reference)
                    print(e.__str__().encode('utf-8'))

                    mwid += 1
