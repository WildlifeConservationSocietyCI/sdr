from django.core import urlresolvers
from app.utils import *
from .models import *


@admin.register(DefinitionType)
class DefinitionTypeAdmin(SdrBaseAdmin):
    pass


@admin.register(FrequencyType)
class FrequencyTypeAdmin(SdrBaseAdmin):
    pass


@admin.register(Group)
class GroupAdmin(SdrBaseAdmin):
    pass


@admin.register(GroupLabel)
class GroupLabelAdmin(SdrBaseAdmin):
    pass


@admin.register(InteractionType)
class InteractionTypeAdmin(SdrBaseAdmin):
    pass


@admin.register(State)
class StateAdmin(SdrBaseAdmin):
    pass


@admin.register(StateLabel)
class StateLabelTypeAdmin(SdrBaseAdmin):
    pass


@admin.register(StrengthType)
class StrengthTypeAdmin(SdrBaseAdmin):
    pass


class SubjectRelationshipInline(admin.TabularInline):
    model = Relationship
    fk_name = 'subject'
    extra = 0
    verbose_name_plural = 'What does this element depend upon?'

    def get_queryset(self, request):
        return super(SubjectRelationshipInline, self).get_queryset(request) \
            .select_related('subject', 'object', 'state', 'relationshiptype', 'strengthtype', 'interactiontype') \
            .order_by('state__label', '-interactiontype__name', 'object__name')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super(SubjectRelationshipInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "object":
            field._queryset = field._queryset.order_by('name')
            field.choices = [(e.pk, '%s [%s]' % (e.name, e.elementid)) for e in field._queryset]
        elif db_field.name == "state" and hasattr(self, "cached_states"):
            field.choices = self.cached_states
        elif db_field.name == "relationshiptype" and hasattr(self, "cached_groups"):
            field.choices = self.cached_groups
        elif db_field.name == "strengthtype" and hasattr(self, "cached_strengthtypes"):
            field.choices = self.cached_strengthtypes
        elif db_field.name == "interactiontype" and hasattr(self, "cached_interactiontypes"):
            field.choices = self.cached_interactiontypes
        return field


class ObjectRelationshipInline(admin.TabularInline):
    model = Relationship
    fk_name = 'object'
    exclude = ['subject']
    readonly_fields = ['subject_link', 'object', 'state', 'relationshiptype', 'strengthtype', 'interactiontype',
                       'notes']
    extra = 0
    verbose_name_plural = 'What depends upon this element?'

    def subject_link(self, obj):
        link = urlresolvers.reverse('admin:muirweb_element_change', args=[obj.subject.id])
        return format_html('<a href="{0}">{1}</a>', link, obj.subject) if obj.subject else None
    subject_link.admin_order_field = 'subject__name'
    subject_link.short_description = 'subject'

    def get_queryset(self, request):
        return super(ObjectRelationshipInline, self).get_queryset(request) \
            .select_related('subject', 'object', 'state', 'relationshiptype', 'strengthtype', 'interactiontype') \
            .order_by('state__label', '-interactiontype__name', 'subject__name')

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     field = super(ObjectRelationshipInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #     if db_field.name == "subject":
    #         field._queryset = field._queryset.order_by('name')
    #         field.choices = [(e.pk, '%s [%s]' % (e.name, e.elementid)) for e in field._queryset]
    #     elif db_field.name == "state" and hasattr(self, "cached_obj_states"):
    #         field.choices = self.cached_obj_states
    #     elif db_field.name == "relationshiptype" and hasattr(self, "cached_obj_groups"):
    #         field.choices = self.cached_obj_groups
    #     elif db_field.name == "strengthtype" and hasattr(self, "cached_strengthtypes"):
    #         field.choices = self.cached_strengthtypes
    #     elif db_field.name == "interactiontype" and hasattr(self, "cached_interactiontypes"):
    #         field.choices = self.cached_interactiontypes
    #     return field


@admin.register(Element)
class ElementAdmin(SdrBaseAdmin):
    list_display = ('elementid', 'name', 'definitiontype', 'spatially_explicit', 'mapped_manually', 'native_units',
                    'last_modified')
    list_display_links = ('elementid', 'name')
    list_filter = ('spatially_explicit', 'definitiontype', 'mapped_manually', 'native_units')
    ordering = ['elementid']
    search_fields = ['elementid', 'name']
    list_per_page = 200
    list_max_show_all = 5000

    fields = (('elementid', 'name'),
              'species',
              ('definitiontype', 'frequencytype'),
              ('spatially_explicit', 'native_units', 'mapped_manually'),
              ('subset_rule', 'adjacency_rule'),
              'description', 'references',)
    filter_horizontal = ('references',)

    inlines = [SubjectRelationshipInline, ObjectRelationshipInline]

    def get_formsets_with_inlines(self, request, obj=None):
        rels = Relationship.objects.none()
        # obj_rels = Relationship.objects.none()
        if obj is not None:
            rels = obj.subject_relationships.select_related('state', 'relationshiptype').all()
            # obj_rels = obj.object_relationships.select_related('state', 'relationshiptype').all()

        element_relationships = [r for r in rels]
        unique_states = list(set(r.state.id for r in element_relationships))
        unique_groups = list(set(r.relationshiptype.id for r in element_relationships))
        state_qs = State.objects.filter(id__in=unique_states).select_related('label')
        group_qs = Group.objects.filter(id__in=unique_groups).select_related('label')
        cached_strengthtypes = [(i.pk, str(i)) for i in StrengthType.objects.all()]
        cached_interactiontypes = [(i.pk, str(i)) for i in InteractionType.objects.all()]

        # obj_relationships = [r for r in obj_rels]
        # unique_obj_states = list(set(r.state.id for r in obj_relationships))
        # unique_obj_groups = list(set(r.relationshiptype.id for r in obj_relationships))
        # obj_state_qs = State.objects.filter(id__in=unique_obj_states).select_related('label')
        # obj_group_qs = Group.objects.filter(id__in=unique_obj_groups).select_related('label')

        for inline in self.get_inline_instances(request, obj):
            inline.cached_states = [(i.pk, str(i)) for i in state_qs]
            inline.cached_groups = [(i.pk, str(i)) for i in group_qs]
            # inline.cached_obj_states = [(i.pk, str(i)) for i in obj_state_qs]
            # inline.cached_obj_groups = [(i.pk, str(i)) for i in obj_group_qs]
            inline.cached_strengthtypes = cached_strengthtypes
            inline.cached_interactiontypes = cached_interactiontypes
            yield inline.get_formset(request, obj), inline

    class Media:
        css = {
            "all": ("admin/css/muirweb_admin.css",)
        }


@admin.register(Relationship)
class RelationshipAdmin(SdrBaseAdmin):
    list_display = ('id', 'subject_link', 'object_link', 'state', 'relationshiptype', 'strengthtype', 'interactiontype')
    list_filter = ('strengthtype', 'interactiontype')
    ordering = ['subject__name']
    search_fields = ('subject__name', 'object__name')

    def subject_link(self, obj):
        link = urlresolvers.reverse('admin:muirweb_element_change', args=[obj.subject.id])
        return format_html('<a href="{0}">{1}</a>', link, obj.subject) if obj.subject else None
    subject_link.admin_order_field = 'subject__name'
    subject_link.short_description = 'subject'

    def object_link(self, obj):
        link = urlresolvers.reverse('admin:muirweb_element_change', args=[obj.object.id])
        return format_html('<a href="{0}">{1}</a>', link, obj.object) if obj.object else None
    object_link.admin_order_field = 'object__name'
    object_link.short_description = 'object'

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        rels = Relationship.objects.none()
        if obj is not None:
            rels = obj.subject.subject_relationships.select_related('state', 'relationshiptype').all()
        element_relationships = [r for r in rels]
        unique_states = list(set(r.state.id for r in element_relationships))
        unique_groups = list(set(r.relationshiptype.id for r in element_relationships))
        state_qs = State.objects.filter(id__in=unique_states).select_related('label')
        group_qs = Group.objects.filter(id__in=unique_groups).select_related('label')

        context['adminform'].form.fields['state'].queryset = state_qs
        context['adminform'].form.fields['relationshiptype'].queryset = group_qs
        return super(RelationshipAdmin, self).render_change_form(request, context, add, change, form_url, obj)

