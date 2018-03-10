from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from app.utils import *
from .models import *


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


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
admin.site.register(Organization, OrganizationAdmin)
