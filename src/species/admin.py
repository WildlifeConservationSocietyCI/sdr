from django.forms import ModelForm
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


class SpeciesForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(SpeciesForm, self).__init__(*args, **kwargs)

        self.fields['col'].required = False
        self.fields['name_accepted'].required = False


@admin.register(Species)
class SpeciesAdmin(SdrBaseAdmin):
    list_display = ('name_accepted', 'name_common', 'taxon', 'col_link', 'last_modified', )
    list_display_links = ('name_accepted', 'name_common', )
    search_fields = ['name_accepted', 'name_common', ]
    actions = (export_model_as_csv,)
    list_filter = ('historical_likelihood', 'taxon')
    form = SpeciesForm

    if settings.DEBUG:
        readonly_fields = ('col_data',)
    else:
        exclude = ('col_data',)

    def col_link(self, obj):
        return format_html(
            '<a href="http://www.catalogueoflife.org/col/details/species/id/{0}" target="_blank">{0}</a>',
            obj.col)

    col_link.admin_order_field = 'col'
    col_link.short_description = 'COL ID'

    def add_view(self, request, form_url='', extra_context=None):
        self.inlines = []
        if '_popup' not in request.GET:
            self.inlines = [SpeciesReferenceInline, ]
        return super(SpeciesAdmin, self).add_view(
            request, form_url, extra_context=extra_context,
        )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.inlines = []
        if '_popup' not in request.GET:
            self.inlines = [SpeciesReferenceInline, ]
        return super(SpeciesAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context,
        )
