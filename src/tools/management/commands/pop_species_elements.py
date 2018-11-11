from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max
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
        species = Species.objects.filter(taxon=taxon).order_by('name_accepted')

        clear = options.get('clear')
        if clear:
            Element.objects.filter(species__taxon=taxon).delete()

        # welikia element ids:
        # birds 3000 - 4000
        # marine fish 6000 - 8000 (some anadromous?)
        # freshwater fish 7000 - 8000 mostly
        # mammals 1000 - 2000
        # plants = 8000 - (3000+ in welikia)
        # amphibians 5000 - 5500
        # reptiles = 5500 - 6000
        # jerusalem taxa: amphibians, birds, fish, freshwater inverts, green algae, mammals, plants, reptiles
        # Question: can we define a universal set? And in such a way to guarantee no clashing?
        taxon_ranges = {
            "amphibians": 5000,
            "birds": 3000,
            "fish": 6000,
            "freshwater inverts": 7000,
            "green algae": 2000,
            "mammals": 1000,
            "plants": 8000,
            "reptiles": 5500
        }

        if species.count() > 0:
            mwid = taxon_ranges[taxon_name]
            max_mwid = Element.objects.filter(species__taxon=taxon).aggregate(Max('elementid'))['elementid__max']
            if max_mwid is not None:
                mwid = int(max_mwid)
            for s in species:
                if s.name_accepted and s.name_accepted != '':
                    existing_elements = Element.objects.filter(species=s)
                    if existing_elements.count() < 1:
                        e = Element(
                            elementid=Decimal('{}.00'.format(mwid)),
                            name=s.__str__().strip(),
                            species=s,
                            description=s.composite_habitat
                        )
                        refs = [r.reference for r in s.speciesreference_set.all()]
                        e.save()
                        e.references.add(*refs)
                        print(e.__str__().encode('utf-8'))

                        mwid += 1
