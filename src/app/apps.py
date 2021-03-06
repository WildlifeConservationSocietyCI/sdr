from django.apps import AppConfig
from suit.apps import DjangoSuitConfig
from suit.menu import ParentItem, ChildItem


class BaseConfig(AppConfig):
    name = 'base'


class SuitConfig(DjangoSuitConfig):
    verbose_name = 'The Shanghai Project Spatial Data Resources'
    layout = 'horizontal'
    list_per_page = 100

    menu = (
        ParentItem('Spatial Data Resources', children=[
            ChildItem(model='sdr.sdr'),
            ChildItem(model='sdr.deftype'),
            ChildItem(model='sdr.defarea'),
            ChildItem(model='sdr.deffeaturetype'),
            ChildItem(model='sdr.defaccuracygeoref'),
            ChildItem(model='sdr.defaccuracylocation'),
            ChildItem(model='sdr.defaccuracysize'),
            ChildItem(model='sdr.defrectification'),
        ], icon='fa fa-map'),
        ParentItem('Places', children=[
            ChildItem(model='pn.place'),
            # ChildItem(model='pn.placename'),
            ChildItem(model='pn.language'),
            ChildItem(model='pn.placepoint'),
            ChildItem(model='pn.placeline'),
            ChildItem(model='pn.placepolygon'),
        ], icon='fa fa-map-marker'),
        ParentItem('Species', children=[
            ChildItem(model='species.species'),
            ChildItem(model='species.taxon'),
            ChildItem(model='species.likelihood'),
        ]),
        ParentItem('Muir Web', children=[
            ChildItem(model='muirweb.element'),
            ChildItem(model='muirweb.relationship'),
        ]),
        ParentItem('References', children=[
            ChildItem(model='base.reference'),
            ChildItem(model='base.period'),
        ]),
        ParentItem('Users', children=[
            ChildItem(model='auth.user'),
            ChildItem('User groups', 'auth.group'),
            ChildItem(model='base.organization'),
        ], align_right=True, icon='fa fa-users'),
    )

    def ready(self):
        super(SuitConfig, self).ready()


class SdrAppConfig(AppConfig):
    name = 'sdr'
    verbose_name = 'Spatial Data Resources'


class PnAppConfig(AppConfig):
    name = 'pn'
    verbose_name = 'Placenames'


class SpeciesAppConfig(AppConfig):
    name = 'species'
    verbose_name = 'Species'


class MuirwebConfig(AppConfig):
    name = 'muirweb'
    verbose_name = 'Muir Web'
