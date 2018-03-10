from django.apps import AppConfig
from suit.apps import DjangoSuitConfig
from suit.menu import ParentItem, ChildItem


class BaseConfig(AppConfig):
    name = 'base'


class SuitConfig(DjangoSuitConfig):
    verbose_name = 'The Shanghai Project Spatial Data Resources'
    layout = 'horizontal'

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
        ParentItem('Users', children=[
            ChildItem(model='auth.user'),
            ChildItem('User groups', 'auth.group'),
            ChildItem(model='base.organization'),
        ], icon='fa fa-users'),
    )

    def ready(self):
        super(SuitConfig, self).ready()


class SdrAppConfig(AppConfig):
    name = 'sdr'
    verbose_name = 'Spatial Data Resources'


class PnAppConfig(AppConfig):
    name = 'pn'
    verbose_name = 'Placenames'
