from django.contrib import admin
from app.utils import *
from .models import *


@admin.register(Taxon)
class TaxonAdmin(SdrBaseAdmin):
    pass


@admin.register(Likelihood)
class LikelihoodAdmin(SdrBaseAdmin):
    pass


class SpeciesReferenceInline(SdrTabularInline):
    model = SpeciesReference
    formset = AtLeastOneRequiredInlineFormSet
    min_num = 1
    extra = 0


@admin.register(Species)
class SpeciesAdmin(SdrBaseAdmin):
    list_display = ('name_accepted', 'name_common', 'taxon', 'col_link', 'last_modified', )
    list_display_links = ('name_accepted', 'name_common', )
    search_fields = ['name_accepted', 'name_common', ]
    actions = (export_model_as_csv,)
    list_filter = ('historical_likelihood', 'taxon')
    inlines = [SpeciesReferenceInline, ]

    def col_link(self, obj):
        return format_html(
            '<a href="http://www.catalogueoflife.org/col/details/species/id/{0}" target="_blank">{0}</a>',
            obj.col)

    col_link.admin_order_field = 'col'
    col_link.short_description = 'COL ID'
