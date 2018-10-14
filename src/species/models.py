from django.contrib.gis.db import models
from base.models import Reference, Period
from django.contrib.postgres.fields import JSONField


class Taxon(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'taxa'

    def __str__(self):
        return self.name


class Likelihood(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Species(models.Model):
    taxon = models.ForeignKey(Taxon, on_delete=models.PROTECT)
    name_accepted = models.CharField(max_length=255, verbose_name='accepted scientific name')
    name_common = models.CharField(max_length=255, verbose_name='common name')
    col = models.CharField(max_length=32, verbose_name='Catalog of Life ID')
    historical_likelihood = models.ForeignKey(Likelihood, on_delete=models.PROTECT, null=True, blank=True)
    introduced = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True, verbose_name='last modified')

    class Meta:
        ordering = ['taxon', 'name_accepted', ]
        verbose_name_plural = 'species'

    def __str__(self):
        return '{} ({})'.format(self.name_accepted, self.name_common)


class SpeciesReference(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    reference = models.ForeignKey(Reference, on_delete=models.CASCADE)
    documentation_text = models.TextField(blank=True)
    period = models.ForeignKey(Period, on_delete=models.PROTECT)
    pagenumbers = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ('species', 'reference',)

    def __str__(self):
        return '{}: {}'.format(self.species, self.reference.name_short)
