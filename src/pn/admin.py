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
        if hasattr(self.instance, 'place'):  # i.e., if saving and not adding
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


class LocationInline(SdrTabularInline):
    model = Location
    formset = AtLeastOneRequiredInlineFormSet
    min_num = 1
    extra = 0


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


class RelatedPlacesInline(SdrTabularInline):
    model = Place.related_places.through
    fk_name = 'from_place'
    _parent_obj = None
    _fk_field = 'to_place'

    def get_formset(self, request, obj=None, **kwargs):
        print(self.model.to_place)
        self._parent_obj = obj
        return super(RelatedPlacesInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == self._fk_field:
            if hasattr(self, '_parent_obj') and hasattr(self._parent_obj, 'pk'):
                kwargs['queryset'] = Place.objects.exclude(pk=self._parent_obj.pk)
        field = super(RelatedPlacesInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        return field


class RelatedToPlacesInline(RelatedPlacesInline):
    fk_name = 'from_place'
    verbose_name = 'related to place'
    verbose_name_plural = 'related to places'
    readonly_fields = ('to_place_link', 'to_place_featuretype')
    _fk_field = 'to_place'

    def to_place_link(self, obj):
        link = reverse('admin:%s_%s_change' % (Place._meta.app_label, Place._meta.model_name), args=(obj.to_place.pk,))
        formatted = format_html('<a href="{0}">{1}</a>', link, obj.to_place)
        return mark_safe(formatted)
    to_place_link.short_description = 'link'

    def to_place_featuretype(self, obj):
        return obj.to_place.featuretype
    to_place_featuretype.short_description = 'feature type'


class RelatedFromPlacesInline(RelatedPlacesInline):
    fk_name = 'to_place'
    verbose_name_plural = 'places relating to this place'
    readonly_fields = ('from_place_link', 'from_place_featuretype')
    fields = readonly_fields
    _fk_field = 'from_place'

    def from_place_link(self, obj):
        link = reverse('admin:%s_%s_change' % (Place._meta.app_label, Place._meta.model_name),
                       args=(obj.from_place.pk,))
        formatted = format_html('<a href="{0}">{1}</a>', link, obj.from_place)
        return mark_safe(formatted)
    from_place_link.short_description = 'place'

    def from_place_featuretype(self, obj):
        return obj.to_place.featuretype
    from_place_featuretype.short_description = 'feature type'

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
               PlacePolygonInline, RelatedToPlacesInline, RelatedFromPlacesInline]


admin.site.register(Language)
admin.site.register(Description)
admin.site.register(Laterdev)
admin.site.register(Location)
admin.site.register(PlacePoint, PlacePointAdmin)
admin.site.register(PlaceLine, PlaceLineAdmin)
admin.site.register(PlacePolygon, PlacePolygonAdmin)
admin.site.register(Placename, PlacenameAdmin)
admin.site.register(Place, PlaceAdmin)
