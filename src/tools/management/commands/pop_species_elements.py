from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max
from django.conf import settings
from base.models import Reference
from species.models import Species, Taxon
from muirweb.models import Element
from app.utils import update_species_element


class Command(BaseCommand):
    help = 'Kill local processes running runserver command'

    def __init__(self):
        super(Command, self).__init__()

    def add_arguments(self, parser):
        parser.add_argument('taxon', nargs='?', type=str)
        parser.add_argument('-c', action='store_true', dest='clear',
                            default=False, help='Clear existing elements before populating'),

    def handle(self, *args, **options):
        tname = options.get('taxon')
        if tname.endswith('s'):
            tname = tname[:-1]
        try:
            taxon = Taxon.objects.get(name=tname).pk
        except Taxon.DoesNotExist:
            raise CommandError('Taxon does not exist: {}'.format(tname))
        species = Species.objects.filter(taxon=taxon, historical_likelihood_id__lte=2).order_by('name_accepted')

        clear = options.get('clear')
        if clear:
            Element.objects.filter(species__taxon=taxon).delete()

        if species.count() > 0:
            mwid = settings.TAXON_ELEMENTID_RANGES[tname]
            max_mwid = Element.objects.filter(species__taxon=taxon).aggregate(Max('elementid'))['elementid__max']
            if max_mwid is not None:
                mwid = int(max_mwid)
            for s in species:
                update_species_element(s, mwid)
                mwid += 1
