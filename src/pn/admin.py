from django.forms import ModelForm
from app.utils import *
from pn.models import *


class CanonicalAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(CanonicalAdminForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = '__all__'

    def clean(self):
        cleaned_data = super(CanonicalAdminForm, self).clean()
        if hasattr(self.instance, 'place'): # i.e., if saving and not adding
            if not cleaned_data['canonical']:
                self.instance.canonical = False
                parent, siblings = self.instance.get_family()
                canonical_ensured = ensure_canonical(self.instance, parent, siblings)
                if isinstance(canonical_ensured, ValidationError):
                    raise canonical_ensured
        return cleaned_data


class PlacenameAdmin(CanonicalSdrBaseAdmin):
    form = CanonicalAdminForm

    list_display = (
        'name', 'place_link', 'canonical', 'invented', 'language', 'place__featuretype', 'sdr_display', 'pagenumbers')
    list_display_links = ('name',)
    search_fields = ['name']
    # TODO: allow user to select multiple areas for filter: https://github.com/kevwilde/django-adminfilters
    list_filter = ('canonical', 'invented', 'language', 'place__featuretype', 'place__areas')
    exportable_fields = ['name', 'place', 'canonical', 'invented', 'language', 'place__featuretype', 'sdr',
                         'pagenumbers']


class PlacePointAdmin(CanonicalSdrBaseAdmin):
    form = CanonicalAdminForm

    def point__name(self, obj):
        return obj.__str__()
    point__name.admin_order_field = 'point__name'
    point__name.short_description = 'point'

    list_display = (
        'point__name', 'place_link', 'canonical', 'invented', 'place__featuretype', 'sdr_display', 'pagenumbers')
    search_fields = ['place__name']
    list_filter = ('canonical', 'invented', 'place__featuretype', 'place__areas')
    exportable_fields = ['point__name', 'place', 'canonical', 'invented', 'place__featuretype', 'sdr', 'pagenumbers']


class PlaceLineAdmin(CanonicalSdrBaseAdmin):
    form = CanonicalAdminForm

    def line__name(self, obj):
        return obj.__str__()
    line__name.admin_order_field = 'line__name'
    line__name.short_description = 'line'

    list_display = (
        'line__name', 'place_link', 'canonical', 'invented', 'place__featuretype', 'sdr_display', 'pagenumbers')
    search_fields = ['place__name']
    list_filter = ('canonical', 'invented', 'place__featuretype', 'place__areas')
    exportable_fields = ['line__name', 'place', 'canonical', 'invented', 'place__featuretype', 'sdr', 'pagenumbers']


class PlacePolygonAdmin(CanonicalSdrBaseAdmin):
    form = CanonicalAdminForm

    def polygon__name(self, obj):
        return obj.__str__()
    polygon__name.admin_order_field = 'polygon__name'
    polygon__name.short_description = 'polygon'

    list_display = (
        'polygon__name', 'place_link', 'canonical', 'invented', 'place__featuretype', 'sdr_display', 'pagenumbers')
    search_fields = ['place__name']
    list_filter = ('canonical', 'invented', 'place__featuretype', 'place__areas')
    exportable_fields = ['polygon__name', 'place', 'canonical', 'invented', 'place__featuretype', 'sdr', 'pagenumbers']


class PlacenameInlineFormset(CanonicalInlineFormset):
    atleast_one = True


class PlacenameInline(SdrTabularInline):
    model = Placename
    formset = PlacenameInlineFormset


class LocationInlineFormset(BaseInlineFormSet):
    def clean(self):
        super(LocationInlineFormset, self).clean()
        if any(self.errors):
            return

        if not any(cleaned_data and not cleaned_data.get('DELETE', False) for cleaned_data in self.cleaned_data):
            raise ValidationError('At least one location is required')


class LocationInline(SdrTabularInline):
    model = Location
    formset = LocationInlineFormset


class DescriptionInline(SdrTabularInline):
    model = Description


class LaterdevInline(SdrTabularInline):
    model = Laterdev


class PlacePointInline(SdrTabularInline):
    model = PlacePoint
    formset = CanonicalInlineFormset


class PlaceLineInline(SdrTabularInline):
    model = PlaceLine
    formset = CanonicalInlineFormset


class PlacePolygonInline(SdrTabularInline):
    model = PlacePolygon
    formset = CanonicalInlineFormset


class PlaceAdmin(SdrBaseAdmin):
    def place__name(self, obj):
        return obj.__str__()
    place__name.admin_order_field = 'place__name'
    place__name.short_description = 'place'

    def last_modified_formatted(self, obj):
        return obj.last_modified.strftime('%Y-%m-%d %H:%M:%S')
    last_modified_formatted.admin_order_field = 'last_modified'
    last_modified_formatted.short_description = 'last modified'

    list_display = ('id', 'place__name', 'placenames', 'area_list', 'featuretype', 'last_modified')
    list_display_links = ('id', 'place__name')
    search_fields = ('id', 'placename__name', 'areas__name')
    list_filter = ('featuretype',)
    exportable_fields = ['place__name', 'id', 'placenames_export', 'area_list_export', 'featuretype',
                         'last_modified_formatted']

    readonly_fields = ('id',)
    fields = ('id', 'featuretype', 'areas')
    filter_horizontal = ('areas',)

    inlines = [PlacenameInline, LocationInline, DescriptionInline, LaterdevInline, PlacePointInline, PlaceLineInline,
               PlacePolygonInline]


admin.site.register(Language)
admin.site.register(Description)
admin.site.register(Laterdev)
admin.site.register(Location)
admin.site.register(PlacePoint, PlacePointAdmin)
admin.site.register(PlaceLine, PlaceLineAdmin)
admin.site.register(PlacePolygon, PlacePolygonAdmin)
admin.site.register(Placename, PlacenameAdmin)
admin.site.register(Place, PlaceAdmin)