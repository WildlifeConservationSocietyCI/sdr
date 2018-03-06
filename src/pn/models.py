from django.contrib.gis.db import models
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from app.utils import ensure_canonical
from sdr.models import DefFeatureType, DefArea, Sdr


class PlaceManager(models.Manager):
    # The extra() call adds the canonical placename to the queryset at the db level, so that admin can sort by it
    def get_queryset(self):
        qs = super(PlaceManager, self).get_queryset().extra(
            select={
                'place__name': 'COALESCE((SELECT name FROM pn_placename WHERE pn_placename.place_id = pn_place.id '
                               'AND pn_placename.canonical = TRUE), pn_place.id::varchar(255))'
            },
        )
        return qs


class PlaceGeomManager(models.Manager):
    _geom = None

    def get_queryset(self):
        qs = super(PlaceGeomManager, self).get_queryset().extra(
            select={
                '{0}__name'.format(self._geom): 'COALESCE((SELECT name || \' \' || pn_place{0}.id::text '
                                                'FROM pn_placename, pn_place WHERE '
                                                'pn_placename.place_id = pn_place.id AND '
                                                'pn_place{0}.place_id = pn_place.id AND '
                                                'pn_placename.canonical = TRUE), '
                                                'pn_place{0}.id::varchar(255))'.format(self._geom)
            },
        )
        return qs


class Place(models.Model):
    featuretype = models.ForeignKey(DefFeatureType, verbose_name='feature type', on_delete=models.PROTECT)
    areas = models.ManyToManyField(DefArea)
    last_modified = models.DateTimeField(auto_now=True, verbose_name='last modified')

    # noinspection PyProtectedMember
    def setnames(self):
        if hasattr(self, '_placenames'):  # Test to see whether we've already set internal multiples (and hit db)
            return
        self._name = None
        self._placenames = None
        self._placenames_export = None

        placenames = self.placename_set.all().order_by('name')
        # TODO: Refactor: this essentially reproduces the extra() queryset customization above
        canonical_placenames = [cp for cp in placenames if cp.canonical]
        if len(canonical_placenames) > 0:
            self._name = canonical_placenames[0].name
        else:
            self._name = str(self.id)

        linked_names = []
        for pn in placenames:
            link = reverse('admin:%s_%s_change' % (Placename._meta.app_label, Placename._meta.model_name),
                           args=(pn.pk,))
            formatted = format_html('<a href="{0}">{1}</a>', link, pn.name)
            linked_names.append(mark_safe(formatted))
        self._placenames = mark_safe('<br />'.join(linked_names))
        self._placenames_export = "\n".join(pn.name for pn in placenames)

    def setareas(self):
        if hasattr(self, '_area_list'):
            return
        self._area_list = None
        self._area_list_export = None

        areas = [area.name for area in self.areas.all().order_by('name')]
        self._area_list = mark_safe('<br />'.join(areas))
        self._area_list_export = self._area_list.replace('<br />', "\n")

    def name(self):
        self.setnames()
        return self._name

    def placenames(self):
        self.setnames()
        return self._placenames
    placenames.short_description = 'place names'

    def placenames_export(self):
        self.setnames()
        return self._placenames_export
    placenames_export.short_description = 'place names'

    def area_list(self):
        self.setareas()
        return self._area_list
    area_list.short_description = 'areas'

    def area_list_export(self):
        self.setareas()
        return self._area_list_export
    area_list_export.short_description = 'areas'

    objects = PlaceManager()

    def __str__(self):
        # If __str__ is accessed via its queryset, just return the placename gotten via extra()
        # Otherwise, go through name() to get the related canonical name
        try:
            return self.place__name
        except:
            name = str(self.name())
            return name

    class Meta:
        ordering = ['-last_modified']


class Language(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['name']


class Description(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    description = models.TextField()
    sdr = models.ForeignKey(Sdr, verbose_name='SDR', on_delete=models.PROTECT)
    pagenumbers = models.CharField(max_length=255, verbose_name='page numbers')

    def __str__(self):
        return '%s...' % self.description[:20]

    class Meta:
        ordering = ['sdr']


class Laterdev(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    laterdev = models.TextField()
    sdr = models.ForeignKey(Sdr, verbose_name='SDR', on_delete=models.PROTECT)
    pagenumbers = models.CharField(max_length=255, verbose_name='page numbers')

    def __str__(self):
        return '%s...' % self.laterdev[:20]

    class Meta:
        verbose_name = 'later development'
        verbose_name_plural = 'later developments'
        ordering = ['sdr']


class Location(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    location = models.TextField()
    sdr = models.ForeignKey(Sdr, verbose_name='SDR', on_delete=models.PROTECT)
    pagenumbers = models.CharField(max_length=255, verbose_name='page numbers')

    def __str__(self):
        return '%s...' % self.location[:20]

    class Meta:
        ordering = ['sdr']


class PlacenameManager(models.Manager):
    def get_queryset(self):
        qs = super(PlacenameManager, self).get_queryset().annotate(featuretype=F('place__featuretype'))
        return qs


# noinspection PyProtectedMember
class CanonicalModel(models.Model):

    @property
    def parent(self):
        raise NotImplementedError('subclasses of CanonicalModel must provide a parent attribute')

    def get_family(self):
        parent = getattr(self, self.parent._meta.model_name)
        kwargs = {'{0}__exact'.format(parent._meta.model_name): parent.pk}
        model = type(self)
        siblings = model.objects.filter(**kwargs).exclude(pk=self.pk)
        return parent, siblings

    def save(self, *args, **kwargs):
        parent, siblings = self.get_family()
        ensured = ensure_canonical(self, parent, siblings)
        if isinstance(ensured, ValidationError):
            raise ensured
        else:
            super(CanonicalModel, self).save(*args, **kwargs)

    def save_simple(self, *args, **kwargs):
        super(CanonicalModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        parent, siblings = self.get_family()
        ensured = ensure_canonical(self, parent, siblings, 'delete')
        if isinstance(ensured, ValidationError):
            raise ensured
        else:
            super(CanonicalModel, self).delete(*args, **kwargs)

    class Meta:
        abstract = True


class Placename(CanonicalModel):
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, verbose_name='language', on_delete=models.PROTECT)
    name = models.CharField(max_length=255, verbose_name='placename')
    sdr = models.ForeignKey(Sdr, verbose_name='SDR', on_delete=models.PROTECT)
    pagenumbers = models.CharField(max_length=255, verbose_name='page numbers')
    canonical = models.BooleanField(default=False)
    invented = models.BooleanField(default=False)

    objects = PlacenameManager()
    parent = Place

    def delete(self, *args, **kwargs):
        parent, siblings = self.get_family()
        super(Placename, self).delete(*args, **kwargs)

        # If this is the only placename for its place, delete the associated place
        if siblings.count() == 0:
            parent.delete()

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'placename'
        verbose_name_plural = 'placenames'
        ordering = ['name']


class PlacePointManager(PlaceGeomManager):
    _geom = 'point'


class PlacePoint(CanonicalModel):
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    geom = models.MultiPointField(geography=True)
    sdr = models.ForeignKey(Sdr, verbose_name='SDR', on_delete=models.PROTECT)
    pagenumbers = models.CharField(max_length=255, verbose_name='page numbers')
    canonical = models.BooleanField(default=False)
    invented = models.BooleanField(default=False)

    parent = Place

    objects = PlacePointManager()

    def __str__(self):
        return str('%s %s' % (self.place.name(), self.pk))

    class Meta:
        verbose_name = 'place point'
        verbose_name_plural = 'place points'


class PlaceLineManager(PlaceGeomManager):
    _geom = 'line'


class PlaceLine(CanonicalModel):
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    geom = models.MultiLineStringField(geography=True)
    sdr = models.ForeignKey(Sdr, verbose_name='SDR', on_delete=models.PROTECT)
    pagenumbers = models.CharField(max_length=255, verbose_name='page numbers')
    canonical = models.BooleanField(default=False)
    invented = models.BooleanField(default=False)

    parent = Place

    objects = PlaceLineManager()

    def __str__(self):
        return str('%s %s' % (self.place.name(), self.pk))

    class Meta:
        verbose_name = 'place line'
        verbose_name_plural = 'place lines'


class PlacePolygonManager(PlaceGeomManager):
    _geom = 'polygon'


class PlacePolygon(CanonicalModel):
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    geom = models.MultiPolygonField(geography=True)
    sdr = models.ForeignKey(Sdr, verbose_name='SDR', on_delete=models.PROTECT)
    pagenumbers = models.CharField(max_length=255, verbose_name='page numbers')
    canonical = models.BooleanField(default=False)
    invented = models.BooleanField(default=False)

    parent = Place

    objects = PlacePolygonManager()

    def __str__(self):
        return str('%s %s' % (self.place.name(), self.pk))

    class Meta:
        verbose_name = 'place polygon'
        verbose_name_plural = 'place polygons'
