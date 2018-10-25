from django.contrib.auth.models import Group
from django.db.models import Count, Prefetch
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from app.utils import *
from .models import *
from species.models import *


class OrganizationAdmin(SdrBaseAdmin):
    pass


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin, NoFooterMixin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_organization',
                    'get_speciesref_count')
    list_select_related = ('userprofile', )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'userprofile__organization')

    def get_queryset(self, request):
        qs = super(CustomUserAdmin, self).get_queryset(request)
        return qs.annotate(speciesref_count=Count('speciesreference'))

    def get_organization(self, instance):
        return instance.userprofile.organization
    get_organization.admin_order_field = 'userprofile__organization'
    get_organization.short_description = 'Organization'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

    def get_speciesref_count(self, instance):
        return instance.speciesref_count
    get_speciesref_count.admin_order_field = 'speciesref_count'
    get_speciesref_count.short_description = 'Species references'


class CustomGroupAdmin(GroupAdmin, NoFooterMixin):
    pass


class PeriodAdmin(SdrBaseAdmin):
    list_display = ('name', 'year_start', 'year_end')


class SpeciesReferenceInlineFormset(BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        super(SpeciesReferenceInlineFormset, self).__init__(*args, **kwargs)
        self.queryset = self.queryset.prefetch_related(
            Prefetch('species', queryset=Species.objects.all().only('name_accepted', 'name_common')),
            Prefetch('reference', queryset=Reference.objects.all().only('name'))
        )


class SpeciesReferenceInline(SdrTabularInline):
    model = SpeciesReference
    fields = ('species', 'reference', 'distribution', 'period', 'pagenumbers', 'notes')
    extra = 0
    formset = SpeciesReferenceInlineFormset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super(SpeciesReferenceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'species' and hasattr(self, 'cached_species'):
            field.choices = self.cached_species
        return field


class ReferenceAdmin(ReferenceAdmin, SpeciesReferenceMixin):
    list_display = ('name_short', 'zotero_link', 'last_modified')
    list_display_links = ('name_short',)
    search_fields = ['name_short', 'zotero']
    inlines = [SpeciesReferenceInline, ]

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            inline.cached_species = [(i.pk, str(i)) for i in Species.objects.only('name_accepted', 'name_common')]
            yield inline.get_formset(request, obj), inline


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Period, PeriodAdmin)
admin.site.register(Reference, ReferenceAdmin)
