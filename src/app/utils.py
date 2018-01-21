import csv
import datetime
import copy
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.gis import admin
from django.contrib.gis.db import models
# from django.contrib.gis.admin.widgets import OpenLayersWidget
from django.contrib.admin import utils as admin_util
from django.contrib.admin.actions import delete_selected
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from django.forms.models import BaseInlineFormSet
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from suit.widgets import AutosizedTextarea


def export_model_as_csv(modeladmin, request, queryset):
    if hasattr(modeladmin, 'exportable_fields'):
        field_list = modeladmin.exportable_fields
    else:
        # Copy modeladmin.list_display to remove action_checkbox
        field_list = list(modeladmin.list_display[:])
        if 'action_checkbox' in field_list:
            field_list.remove('action_checkbox')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s-%s-export_%s.csv' % (
        __package__.lower(),
        queryset.model.__name__.lower(),
        datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
    )

    writer = csv.writer(response)
    writer.writerow(
        [admin_util.label_for_field(f, queryset.model, modeladmin) for f in field_list],
    )

    for obj in queryset:
        csv_line_values = []
        for field in field_list:
            field_obj, attr, value = admin_util.lookup_field(field, obj, modeladmin)
            csv_line_values.append(value)

        writer.writerow(csv_line_values)

    return response


export_model_as_csv.short_description = 'Export selected %(verbose_name_plural)s to CSV'


# obj is an SDR object
def zotero_link(obj):
    return format_html('<a href="https://www.zotero.org/groups/{0}/items/itemKey/{1}" target="_blank">{2}</a>',
                       settings.ZOTERO_GROUP, obj.zotero, obj.zotero)


# noinspection PyProtectedMember
def ensure_canonical(instance, parent, siblings, *args):
    othercan = 0
    # If there are no other objects for this parent, make sure this one is canonical, and then just return
    if siblings.count() == 0:
        instance.canonical = True
    # if operation is add/save and obj is canonical, make all others not
    elif instance.canonical and 'delete' not in args:
        for other in siblings:
            other.canonical = False
            other.save_simple()
    # if adding/saving as noncanonical OR deleting (canonical or not), make sure something else is canonical
    elif instance.canonical is False or 'delete' in args:
        for other in siblings:
            if other.canonical:
                othercan += 1
        if othercan < 1:
            # If there's only one other object for this parent, set its object as canonical
            if siblings.count() == 1:
                siblings[0].canonical = True
                siblings[0].save_simple()
            else:
                # Otherwise, make the user choose another object as canonical
                link = reverse('admin:%s_%s_change' % (parent._meta.app_label, parent._meta.model_name),
                               args=(instance.place.pk,))
                return ValidationError({
                    'canonical': mark_safe(
                        'You may not delete or deselect this %s as canonical until you '
                        'mark another of <a href="%s">this %s\'s</a> names as canonical.'
                        % (instance._meta.model_name, link, parent._meta.model_name))
                })

    # Return queryset of other objects for this parent for possible further processing without re-querying db
    return siblings


class SdrBaseAdmin(admin.OSMGeoAdmin):
    list_select_related = True

    default_lat = settings.DEFAULT_LAT
    default_lon = settings.DEFAULT_LON
    default_zoom = settings.DEFAULT_ZOOM

    formfield_overrides = {
        models.TextField: {'widget': AutosizedTextarea},
    }

    class Media:
        css = {
            "all": ("admin/css/sdr_admin.css",)
        }
        # js = ("admin/js/sdr_admin.js",)

    # See https://groups.google.com/forum/#!topic/django-users/l_nsr0_ea0o -- added parentobj param to inline_class()
    # def get_inline_instances(self, request, obj=None):
    #     inline_instances = []
    #     for inline_class in self.inlines:
    #         inline = inline_class(self.model, self.admin_site, parentobj=obj)
    #         if request:
    #             if not (inline.has_add_permission(request) or
    #                     inline.has_change_permission(request, obj) or
    #                     inline.has_delete_permission(request, obj)):
    #                 continue
    #             if not inline.has_add_permission(request):
    #                 inline.max_num = 0
    #         inline_instances.append(inline)
    #
    #     return inline_instances

    actions = (export_model_as_csv,)


# noinspection PyProtectedMember
class CanonicalSdrBaseAdmin(SdrBaseAdmin):

    def place_link(self, obj):
        p = obj.place.__class__._meta
        link = reverse('admin:%s_%s_change' % (p.app_label, p.model_name), args=(obj.place.pk,))
        formatted = format_html('<a href="{0}">{1}</a>', link, obj.place)
        return mark_safe(formatted)
    place_link.admin_order_field = 'place'
    place_link.short_description = 'place'

    def place__featuretype(self, obj):
        return obj.place.featuretype
    place__featuretype.admin_order_field = 'featuretype'
    place__featuretype.short_description = 'feature type'

    def sdr_display(self, obj):
        s = obj.sdr.__class__._meta
        sdr_link = reverse('admin:%s_%s_change' % (s.app_label, s.model_name), args=(obj.sdr.pk,))
        sdr_formatted = format_html('<a href="{0}">{1}</a>', sdr_link, obj.sdr)
        return mark_safe('%s [%s]' % (sdr_formatted, zotero_link(obj.sdr)))
    sdr_display.admin_order_field = 'sdr'
    sdr_display.short_description = 'SDR'

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, admin_util.unquote(object_id))
        parent, siblings = obj.get_family()
        canonical_ensured = ensure_canonical(obj, parent, siblings, 'delete')
        if isinstance(canonical_ensured, ValidationError):
            messages.error(request, canonical_ensured.error_dict['canonical'][0].message)
            link = reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=(object_id,))
            return HttpResponseRedirect(link)
        else:
            return super(CanonicalSdrBaseAdmin, self).delete_view(request, object_id, extra_context)

    # do canonical validation before calling stock delete_selected
    def delete_selected_ensure_canonical(self, request, queryset):
        val_errors = []
        objs_to_mark_canonical = []
        parents_to_delete = []
        othercan = {}

        for obj in queryset:
            parent, siblings = obj.get_family()
            others_in_queryset = []
            for other in siblings:
                if other in queryset:
                    others_in_queryset.append(other)
                if other.canonical:
                    othercan[obj] = othercan.get(obj, 0) + 1

            # If there are no other objects or they're all selected for deletion, delete the associated parent
            if siblings.count() == 0 or siblings.count() == len(others_in_queryset):
                parents_to_delete.append(parent)

            # If there are no other objects for this parent,
            # or all the other objects are marked for deletion anyway,
            # or one of the other objects is marked canonical,
            # we don't need to do anything. Otherwise:
            if siblings.count() > 0 and siblings.count() != len(others_in_queryset) and othercan.get(obj, 0) < 1:
                # If there's only one other object for this parent, or only one after selecting others for deletion,
                # we only need to set its object as canonical
                if siblings.count() == 1 or siblings.count() - len(others_in_queryset) == 1:
                    for sibling in siblings:
                        if sibling not in others_in_queryset:
                            objs_to_mark_canonical.append(sibling)
                else:
                    # Otherwise, add an error
                    link = reverse('admin:%s_%s_change' % (parent._meta.app_label, parent._meta.model_name),
                                   args=(parent.pk,))
                    val_errors.append(
                        mark_safe(
                            'You may not delete \'{0}\' until you mark another {1} for <a href="{2}">{3}</a> as '
                            'canonical.'.format(
                                obj.name, obj._meta.model_name, link, obj.name
                            )
                        )
                    )

        if val_errors:
            for e in val_errors:
                super(CanonicalSdrBaseAdmin, self).message_user(request, e, messages.ERROR)
            return None
        else:
            for obj in objs_to_mark_canonical:
                obj.canonical = True
                obj.save()
            for p in parents_to_delete:
                p.delete()

            return delete_selected(self, request, queryset)

    def get_actions(self, request):
        actions = super(CanonicalSdrBaseAdmin, self).get_actions(request)
        actions['delete_selected'] = (
            CanonicalSdrBaseAdmin.delete_selected_ensure_canonical, 'delete_selected',
            "Delete selected %(verbose_name_plural)s")
        return actions


# noinspection PyProtectedMember,PyAttributeOutsideInit
class CanonicalInlineFormset(BaseInlineFormSet):
    atleast_one = False

    def clean(self):
        super(CanonicalInlineFormset, self).clean()
        if any(self.errors):
            return
        modelname = self.queryset.model._meta.verbose_name

        if self.atleast_one:
            if not any(cleaned_data and not cleaned_data.get('DELETE', False) for cleaned_data in self.cleaned_data):
                raise ValidationError('At least one %s is required' % modelname)

        canonical_instances = []
        for form in self.forms:
            data = form.cleaned_data

            if data.get('canonical', False) and not data['DELETE']:
                canonical_instances.append(form.instance.__str__())

        # Not more than one canonical instance must be marked...
        if len(canonical_instances) > 1:
            raise ValidationError('Only one %s for this place may be marked canonical. Deselect one of: %s'
                                  % (modelname, '; '.join(canonical_instances)))

        # ...and at least one must be marked
        if len(self.forms) and self.atleast_one:
            if len(canonical_instances) < 1:
                raise ValidationError('One %s for this place must be marked canonical.' % modelname)

    # Not terribly DRY, but this just overrides the order: saves new objects before existing, so that
    # model save/delete canonical checks work
    def save(self, commit=True):
        if not commit:
            self.saved_forms = []

            def save_m2m():
                for form in self.saved_forms:
                    form.save_m2m()

            self.save_m2m = save_m2m
        return self.save_new_objects(commit) + self.save_existing_objects(commit)


# noinspection PyProtectedMember
# class SdrTabularInline(admin.TabularInline):
#     min_num = 0
#     extra = 0
class SdrTabularInline(admin.TabularInline, admin.OSMGeoAdmin):
    min_num = 0
    extra = 0

    def __init__(self, parent_model, admin_site):
        self.admin_site = admin_site
        self.parent_model = parent_model
        self.opts = self.model._meta
        self.has_registered_model = admin_site.is_registered(self.model)
        # super(SdrTabularInline, self).__init__()

        overrides = copy.deepcopy(FORMFIELD_FOR_DBFIELD_DEFAULTS)
        for k, v in self.formfield_overrides.items():
            overrides.setdefault(k, {}).update(v)
        self.formfield_overrides = overrides

        if self.verbose_name is None:
            self.verbose_name = self.model._meta.verbose_name
        if self.verbose_name_plural is None:
            self.verbose_name_plural = self.model._meta.verbose_name_plural

    # See https://groups.google.com/forum/#!topic/django-users/l_nsr0_ea0o
    # Note the __init__ override depends on having parent_object
    # All this is just to display parent label on inline heading title
    # def __init__(self, *args, **kwargs):
    #     if 'parentobj' in kwargs:
    #         parent_object = kwargs['parentobj']
    #         del kwargs['parentobj']
    #         if parent_object is not None:
    #             self.verbose_name_plural = '%s for %s %s' % (
    #                 self.model._meta.verbose_name_plural, parent_object._meta.verbose_name.title(), parent_object.pk)
    #     super(SdrTabularInline, self).__init__(*args, **kwargs)

    formfield_overrides = {
        models.TextField: {'widget': AutosizedTextarea},
        # TODO: fix inline map widgets when adding (this doesn't work)
        # models.MultiPointField: {'widget': OpenLayersWidget},
    }

    # Don't add any extra forms if we already have at least one object in this set
    # def get_extra(self, request, obj=None, **kwargs):
    #     extra = 1
    #     # I don't see a way to get the queryset for this inline directly; obj refers to parent
    #     if obj is not None:
    #         related_objects = [
    #             f for f in obj._meta.get_fields()
    #             if (f.one_to_many or f.one_to_one) and f.auto_created and not f.concrete
    #         ]
    #         links = [rel.get_accessor_name() for rel in related_objects]
    #         for link in links:
    #             if link[:-4] == self.model.__name__.lower():
    #                 qs = getattr(obj, link).all()
    #                 print(self.model.__name__.lower(), qs)
    #                 if qs.count() > 0:
    #                     return 0
    #     return extra

    # Set default for any field called 'processor' to user currently logged in
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'processor':
            kwargs['initial'] = request.user.id
        return super(SdrTabularInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class OverwriteFileSystemStorage(FileSystemStorage):

    def get_available_name(self, name, max_length=None):
        self.delete(name)
        return name
