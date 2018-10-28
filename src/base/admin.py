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
            Prefetch('reference', queryset=Reference.objects.all().only('id')),
            Prefetch('period', queryset=Period.objects.all()),
        ).order_by('species__name_accepted')


# class SpeciesReferenceInline(SdrTabularInline):
#     model = SpeciesReference
#     fields = ('species', 'reference', 'distribution', 'period', 'pagenumbers', 'notes')
#     extra = 0
#     formset = SpeciesReferenceInlineFormset
#
#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         field = super(SpeciesReferenceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
#         if db_field.name == 'species' and hasattr(self, 'cached_species'):
#             field.choices = self.cached_species
#         return field


# noinspection PyProtectedMember
class SpeciesReferenceInline(SdrTabularInline):
    model = SpeciesReference
    formset = SpeciesReferenceInlineFormset
    readonly_fields = ('species_link', 'reference', 'distribution', 'period', 'pagenumbers', 'notes')
    exclude = ('created_by', 'species')

    def species_link(self, obj):
        link = reverse('admin:%s_%s_change' % ('species', 'species'), args=(obj.species.pk,))
        link_formatted = format_html('<a href="{0}">{1}</a>', link, obj.species)
        return mark_safe(link_formatted)
    species_link.admin_order_field = 'species__name_accepted'
    species_link.short_description = 'species'

    def has_add_permission(self, request):
        return False


class AddSpeciesReferenceInline(SdrTabularInline):
    model = SpeciesReference
    formset = SpeciesReferenceInlineFormset
    fields = ('species', 'reference', 'distribution', 'period', 'pagenumbers', 'notes')
    extra = 0
    verbose_name_plural = 'Add species references'

    def get_queryset(self, request):
        return super(AddSpeciesReferenceInline, self).get_queryset(request).none()

    def has_change_permission(self, request, obj=None):
        return False


class ReferenceAdmin(ReferenceAdmin, SpeciesReferenceMixin):
    list_display = ('name_short', 'zotero_link', 'last_modified')
    list_display_links = ('name_short',)
    search_fields = ['name_short', 'zotero']

    # def get_formsets_with_inlines(self, request, obj=None):
    #     for inline in self.get_inline_instances(request, obj):
    #         inline.cached_species = [(i.pk, str(i)) for i in Species.objects.only('name_accepted', 'name_common')]
    #         yield inline.get_formset(request, obj), inline

    def add_view(self, request, form_url='', extra_context=None):
        self.inlines = []
        if '_popup' not in request.GET:
            self.inlines = [SpeciesReferenceInline, AddSpeciesReferenceInline]
        return super(ReferenceAdmin, self).add_view(
            request, form_url, extra_context=extra_context,
        )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.inlines = []
        if '_popup' not in request.GET:
            self.inlines = [SpeciesReferenceInline, AddSpeciesReferenceInline]
        return super(ReferenceAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context,
        )


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Period, PeriodAdmin)
admin.site.register(Reference, ReferenceAdmin)
