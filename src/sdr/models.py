import os
from django.contrib.gis.db import models
from django.db.models import Count
from django.contrib.auth.models import User
from django.utils.text import get_valid_filename, Truncator
from django.core.files import storage
from app.utils import *
import boto3
import botocore


class DefFeatureType(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'feature type'
        verbose_name_plural = 'feature types'
        ordering = ['name']


class DefArea(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "name__icontains",

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'area'
        verbose_name_plural = 'areas'
        ordering = ['name']


class DefAccuracyGeoref(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'georeferencing accuracy level'
        verbose_name_plural = 'georeferencing accuracy levels'


class DefAccuracyLocation(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'location accuracy level'
        verbose_name_plural = 'location accuracy levels'


class DefAccuracySize(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'size accuracy level'
        verbose_name_plural = 'size accuracy levels'


class DefRectification(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'rectification order'
        verbose_name_plural = 'rectification orders'
        ordering = ['name']


class DefResolution(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'resolution quality level'
        verbose_name_plural = 'resolution quality levels'


class DefType(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'resource type'
        verbose_name_plural = 'resource types'
        ordering = ['name']


# http://blog.endpoint.com/2013/09/getting-django-admin-to-sort-modified.html
class SdrManager(models.Manager):
    def get_queryset(self):
        qs = super(SdrManager, self).get_queryset().annotate(
            scans=Count('scan'),
            images=Count('georef'),
            features=Count('feature'),
        )
        return qs


class Sdr(models.Model):
    zotero = models.CharField(max_length=8, verbose_name='zotero ID')
    name_short = models.CharField(max_length=255, verbose_name='short name')
    sdr_year = models.SmallIntegerField(verbose_name='earliest year depicted')
    intended_features = models.ManyToManyField(DefFeatureType)
    areas = models.ManyToManyField(DefArea)
    type = models.ForeignKey(DefType, on_delete=models.PROTECT)
    sdraccloc = models.ForeignKey(DefAccuracyLocation, verbose_name='location accuracy', on_delete=models.PROTECT)
    sdraccsiz = models.ForeignKey(DefAccuracySize, verbose_name='size accuracy', on_delete=models.PROTECT)
    sdraccgeo = models.ForeignKey(DefAccuracyGeoref, verbose_name='georeferencing accuracy', on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    notes_sdraccloc = models.TextField(blank=True, verbose_name='location accuracy notes')
    notes_sdraccsiz = models.TextField(blank=True, verbose_name='size accuracy notes')
    notes_sdraccgeo = models.TextField(blank=True, verbose_name='georeferencing accuracy notes')
    last_modified = models.DateTimeField(auto_now=True, verbose_name='last modified')

    objects = SdrManager()

    def save(self, *args, **kwargs):
        super(Sdr, self).save(*args, **kwargs)
        # Save every child object to ensure filenames stay consistent with SDR name
        for s in self.scan_set.all():
            s.save()
        for g in self.georef_set.all():
            g.save()
        for f in self.feature_set.all():
            f.save()

    def __str__(self):
        name = str(self.name_short)
        if len(name) > 20:
            return '%s...' % name[:20]
        return name

    class Meta:
        verbose_name = 'spatial data resource'
        verbose_name_plural = 'spatial data resources'
        ordering = ['-last_modified']


def sdrfile_name(instance, filename):
    resourcetype = instance.__class__.__name__.lower()
    if resourcetype == Feature.__name__.lower():
        resourcetype = get_valid_filename(Truncator(instance.featuretype.name).words(4, truncate=''))
    humanname = get_valid_filename(Truncator(instance.sdr.name_short).words(4, truncate=''))
    root, ext = os.path.splitext(filename)
    instancefile = '%s-%s-%s-%s%s' % (instance.sdr_id, humanname, resourcetype, instance.pk, ext)
    return instancefile


def rename_existing_file(oldfile, newfile):
    s = storage.get_storage_class()

    classname = s.__name__.split('.')[-1]
    if classname == 'S3Boto3Storage':
        s3 = boto3.resource('s3')
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        try:
            s3.Object(bucket, oldfile.name).load()
            s3.Object(bucket, newfile.name).copy_from(CopySource='%s/%s' % (bucket, oldfile.name))
            s3.Object(bucket, oldfile.name).delete()
        except botocore.exceptions.ClientError as e:
            pass
    elif classname == 'OverwriteFileSystemStorage' or classname == 'FileSystemStorage':
        if os.path.isfile(oldfile.path):
            new_path = os.path.join(settings.MEDIA_ROOT, newfile.name)
            os.rename(oldfile.path, new_path)
    else:
        raise NotImplementedError('Rename existing file not implemented for storage system in use: %s' % classname)


# noinspection PyUnresolvedReferences
def save_sdr_files(instance, *args, **kwargs):
    resourcemodel = instance.__class__

    # adding a new obj. Need to save record first so we have pk for filename.
    if instance.pk is None:
        file_to_save = instance.file
        instance.file = None
        super(resourcemodel, instance).save(*args, **kwargs)
        instance.file = file_to_save

    # editing existing object
    else:
        oldfile = resourcemodel.objects.get(pk=instance.pk).file
        instance.file.name = sdrfile_name(instance, instance.file.name)
        # rename existing file; if no new file is uploaded, existing file will be properly named
        if oldfile.name != instance.file.name:  # SDR name has changed, OR user is replacing file
            rename_existing_file(oldfile, instance.file)

    super(resourcemodel, instance).save(*args, **kwargs)


class Feature(models.Model):
    sdr = models.ForeignKey(Sdr, on_delete=models.CASCADE)
    file = models.FileField(upload_to=sdrfile_name, null=True)
    featuretype = models.ForeignKey(DefFeatureType, verbose_name='feature type', on_delete=models.PROTECT)
    processor = models.ForeignKey(User, related_name='features_processed', verbose_name='processed by',
                                  on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    qa_processor = models.ForeignKey(User, null=True, blank=True, verbose_name='QA\'d by', on_delete=models.PROTECT)
    qa_date = models.DateField(null=True, blank=True, verbose_name='QA date')
    final = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        save_sdr_files(self, *args, **kwargs)

    def __str__(self):
        return '%s %s' % (self.sdr.__str__(), str(self.pk))

    class Meta:
        verbose_name = 'digitized feature'
        verbose_name_plural = 'digitized features'
        ordering = ['sdr']


class Georef(models.Model):
    sdr = models.ForeignKey(Sdr, on_delete=models.CASCADE)
    file = models.FileField(upload_to=sdrfile_name, null=True)
    rectification = models.ForeignKey(DefRectification, on_delete=models.PROTECT)
    control_points = models.SmallIntegerField()
    rms_error = models.DecimalField(max_digits=8, decimal_places=6, verbose_name='RMS error')
    processor = models.ForeignKey(User, related_name='georefs_processed', verbose_name='processed by',
                                  on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    qa_processor = models.ForeignKey(User, null=True, blank=True, verbose_name='QA\'d by', on_delete=models.PROTECT)
    qa_date = models.DateField(null=True, blank=True, verbose_name='QA date')
    final = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        save_sdr_files(self, *args, **kwargs)

    def __str__(self):
        return '%s %s' % (self.sdr.__str__(), str(self.pk))

    class Meta:
        verbose_name = 'georeferenced image'
        verbose_name_plural = 'georeferenced images'
        ordering = ['sdr']


class Scan(models.Model):
    sdr = models.ForeignKey(Sdr, on_delete=models.CASCADE)
    # Setting null=True for fields based on CharField is discouraged, but required because of the save() override
    # that saves data before renaming file. I'm not sure why form still requires form input but this is desired anyway.
    file = models.FileField(upload_to=sdrfile_name, null=True)
    resolution = models.ForeignKey(DefResolution, on_delete=models.PROTECT)
    processor = models.ForeignKey(User, related_name='scans_processed', verbose_name='processed by',
                                  on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    qa_processor = models.ForeignKey(User, null=True, blank=True, verbose_name='QA\'d by', on_delete=models.PROTECT)
    qa_date = models.DateField(null=True, blank=True, verbose_name='QA date')
    final = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        save_sdr_files(self, *args, **kwargs)

    def __str__(self):
        return '%s %s' % (self.sdr.__str__(), str(self.pk))

    class Meta:
        verbose_name = 'scanned image'
        verbose_name_plural = 'scanned images'
        ordering = ['sdr']
