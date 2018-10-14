from django.forms import ModelForm, NumberInput, CheckboxSelectMultiple
from .models import *
from pn.models import Placename, Place
from django.conf import settings

admin.site.site_header = '%s Spatial Data Resources' % settings.PROJECT_NAME


class DefAreaAdmin(SdrBaseAdmin):
    pass


class DefFeatureTypeAdmin(SdrBaseAdmin):
    pass


class DefTypeAdmin(SdrBaseAdmin):
    pass


class QaInline(SdrTabularInline):

    def __init__(self, *args, **kwargs):
        super(QaInline, self).__init__(*args, **kwargs)
        admin_qs = User.objects.filter(groups__name=settings.QA_GROUP_NAME).distinct()
        self.qa_processors = [(a.pk, str(a)) for a in admin_qs]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super(QaInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'qa_processor' and hasattr(self, 'qa_processors'):
            field.choices = self.qa_processors
        return field


class ScanInline(QaInline):
    model = Scan

    formfield_overrides = {
        models.TextField: {'widget': AutosizedTextarea},
    }


class GeorefInline(QaInline):
    model = Georef

    formfield_overrides = {
        models.TextField: {'widget': AutosizedTextarea},
        models.IntegerField: {'widget': NumberInput(attrs={'style': 'width: 50px;'})},
        models.DecimalField: {'widget': NumberInput(attrs={'style': 'width: 50px;'})},
    }


class FeatureInline(QaInline):
    model = Feature


class PlacenameInline(SdrTabularInline):
    model = Placename

    def place_link(self, obj):
        link = reverse('admin:%s_%s_change' % (Place._meta.app_label, Place._meta.model_name), args=(obj.place.pk,))
        formatted = format_html('<a href="{0}">{1}</a>', link, obj.place)
        return mark_safe(formatted)
    place_link.short_description = 'place'

    fields = ('name', 'place_link', 'language', 'canonical', 'invented', 'pagenumbers')

    # Make everything in this table read-only
    def get_readonly_fields(self, request, obj=None):
        # Make fields appear in right order
        return ['name', 'place_link', 'language', 'canonical', 'invented', 'pagenumbers']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SdrAdminForm(ModelForm):
    class Meta:
        model = Sdr
        fields = '__all__'
        widgets = {
            'areas': CheckboxSelectMultiple,
            'notes_sdraccloc': AutosizedTextarea(attrs={'style': 'width: 400px;'}),
            'notes_sdraccsiz': AutosizedTextarea(attrs={'style': 'width: 400px;'}),
            'notes_sdraccgeo': AutosizedTextarea(attrs={'style': 'width: 400px;'}),
            'notes': AutosizedTextarea(attrs={'style': 'width: 100%;'}),
            # 'zotero': EnclosedInput(append='<input id="zotero_button" type="button" class="btn" value="link">'),
        }


class SdrAdmin(ReferenceAdmin):
    form = SdrAdminForm

    def scans(self, obj):
        count = Scan.objects.filter(sdr=obj).count()
        if count is not None:
            return count
        return 0
    scans.admin_order_field = 'scans'

    def images(self, obj):
        count = Georef.objects.filter(sdr=obj).count()
        if count is not None:
            return count
        return 0
    images.admin_order_field = 'images'

    def features(self, obj):
        count = Feature.objects.filter(sdr=obj).count()
        if count is not None:
            count = 0
        total = obj.intended_features.count()
        return '%s / %s' % (count, total)
    features.admin_order_field = 'features'

    list_display = (
        'id', 'name_short', 'zotero_link', 'sdr_year', 'type', 'scans', 'images', 'features', 'last_modified')
    list_display_links = ('id', 'name_short')
    # TODO: from-year to-year search fields
    search_fields = ['id', 'name_short', 'zotero']
    list_filter = ('areas', 'intended_features', 'type')
    # avoiding 'id' in first column because http://annalear.ca/2010/06/10/why-excel-thinks-your-csv-is-a-sylk/
    exportable_fields = ['name_short', 'id', 'zotero', 'sdr_year', 'type', 'scans', 'images', 'features',
                         'last_modified_formatted']

    readonly_fields = ('id',)
    fields = (('id', 'name_short', 'sdr_year'), ('type', 'zotero'), 'areas', 'intended_features',
              ('sdraccloc', 'notes_sdraccloc'), ('sdraccsiz', 'notes_sdraccsiz'), ('sdraccgeo', 'notes_sdraccgeo'),
              'notes')
    filter_horizontal = ('intended_features',)
    formfield_overrides = {
        # models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

    inlines = [ScanInline, GeorefInline, FeatureInline, PlacenameInline]


admin.site.register(DefAccuracyGeoref)
admin.site.register(DefAccuracyLocation)
admin.site.register(DefAccuracySize)
admin.site.register(DefRectification)
admin.site.register(DefResolution)
admin.site.register(Feature)
admin.site.register(Georef)
admin.site.register(Scan)
admin.site.register(DefArea, DefAreaAdmin)
admin.site.register(DefFeatureType, DefFeatureTypeAdmin)
admin.site.register(DefType, DefTypeAdmin)
admin.site.register(Sdr, SdrAdmin)
