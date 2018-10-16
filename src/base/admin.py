from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from app.utils import *
from .models import *
from species.models import SpeciesReference


class OrganizationAdmin(SdrBaseAdmin):
    pass


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin, NoFooterMixin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_organization')
    list_select_related = ('userprofile', )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'userprofile__organization')

    def get_organization(self, instance):
        return instance.userprofile.organization
    get_organization.admin_order_field = 'userprofile__organization'
    get_organization.short_description = 'Organization'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


class CustomGroupAdmin(GroupAdmin, NoFooterMixin):
    pass


class PeriodAdmin(SdrBaseAdmin):
    list_display = ('name', 'year_start', 'year_end')


class SpeciesReferenceInline(SdrTabularInline):
    model = SpeciesReference
    extra = 0


class ReferenceAdmin(ReferenceAdmin):
    list_display = ('name_short', 'zotero_link', 'last_modified')
    list_display_links = ('name_short',)
    search_fields = ['name_short', 'zotero']
    inlines = [SpeciesReferenceInline, ]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Period, PeriodAdmin)
admin.site.register(Reference, ReferenceAdmin)
