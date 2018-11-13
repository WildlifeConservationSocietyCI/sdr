from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from base.models import Reference, Period
from app.utils import *
from operator import itemgetter


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
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Species(models.Model):
    taxon = models.ForeignKey(Taxon, on_delete=models.PROTECT)
    col = models.CharField(max_length=32, verbose_name='Catalog of Life ID', unique=True)
    name_accepted = models.CharField(max_length=255, verbose_name='accepted scientific name')
    name_common = models.CharField(max_length=255, blank=True, verbose_name='common name (first English COL)')
    name_accepted_ref = models.CharField(max_length=255, blank=True,
                                         verbose_name='accepted scientific name (reference)',
                                         help_text='Enter if different from COL accepted scientific name')
    name_common_ref = models.CharField(max_length=255, blank=True, verbose_name='common name (reference)',
                                       help_text='Enter if different from COL common name')
    historical_likelihood = models.ForeignKey(Likelihood, on_delete=models.PROTECT, null=True, blank=True)
    introduced = models.BooleanField(default=False)
    composite_habitat = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True, verbose_name='last modified')
    col_data = JSONField(verbose_name='Catalog of Life data')

    _form_cleaned = False

    class Meta:
        ordering = ['name_accepted', ]
        verbose_name_plural = 'species'

    def __str__(self):
        return '{} ({})'.format(self.name_accepted, self.name_common)

    def get_col_data(self):
        qry = {}
        qry_term = None
        if self.col is not None and self.col != '':
            qry_term = self._meta.get_field('col').verbose_name
            qry['id'] = [self.col]
        elif self.name_accepted is not None and self.name_accepted != '':
            qry_term = self._meta.get_field('name_accepted').verbose_name
            qry['name'] = [self.name_accepted]
        elif self.name_common is not None and self.name_common != '':
            qry_term = self._meta.get_field('name_common').verbose_name
            qry['name'] = [self.name_common]

        if len(qry) > 0:
            print(qry)
            try:
                col_results = query_col(qry)
                if len(col_results) > 1:
                    # if only one of the results is a Species, use it
                    species_results = [s for s in col_results if
                                       s.get('rank') is not None and s['rank'].lower() == 'species']
                    if len(species_results) == 1:
                        col_results = species_results
                    else:
                        col_results = sorted(col_results, key=itemgetter('name'))
                        col_list = '<br>'.join([
                            format_html('<a href="{0}" target="_blank">{1}</a>', r.get('url'), r.get('name'))
                            for r in col_results
                        ])
                        raise ValidationError(mark_safe(
                            'Catalog of Life returned more than one result searching by {}:<br>{}'.format(
                                qry_term,
                                col_list))
                        )

                elif len(col_results) < 1:
                    raise ValidationError('No species found in Catalog of Life. Searched with: {}'.format(
                        qry_term)
                    )

                self.col_data = col_results[0]

            except requests.exceptions.ConnectionError:
                raise ValidationError('Error connecting with Catalog of Life web service.')
            except RuntimeError as e:
                raise ValidationError('Error: {}'.format(e))

        else:
            raise ValidationError('You must specify a COL ID, accepted scientific name, or common name.')

    def update_fields_from_col(self):
        if self.col_data is not None and self.col_data != '':
            col = self.col_data.get('id')
            name_accepted = self.col_data.get('name')
            common_names = self.col_data.get('common_names')
            name_common = ''
            if common_names is not None and len(common_names) > 0:
                for cn in common_names:
                    lang = cn.get('language')
                    if lang is not None and (lang.lower() == 'english' or lang.lower() == 'en'):
                        name_common = cn['name']
                        break

            self.col = col
            self.validate_unique()
            self.name_accepted = name_accepted
            self.name_common = name_common

    def clean(self, *args, **kwargs):
        if self._form_cleaned is False:
            self.get_col_data()
            self.update_fields_from_col()
            self._form_cleaned = True
        super(Species, self).clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Species, self).save(*args, **kwargs)


@receiver(post_save, sender=Species)
def update_element_from_species(sender, instance, **kwargs):
    mwid = settings.TAXON_ELEMENTID_RANGES[instance.taxon.name]
    max_mwid = Element.objects.filter(species__taxon=instance.taxon).aggregate(Max('elementid'))['elementid__max']
    if max_mwid is not None:
        mwid = int(max_mwid)
    update_species_element(instance, mwid)


class SpeciesReference(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    reference = models.ForeignKey(Reference, on_delete=models.CASCADE)
    distribution = models.TextField(blank=True, verbose_name='Distribution/habitat')
    period = models.ForeignKey(Period, on_delete=models.PROTECT)
    pagenumbers = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True)

    class Meta:
        ordering = ('species', 'reference',)

    def __str__(self):
        return '{}: {}'.format(self.species, self.reference)


@receiver(post_save, sender=SpeciesReference)
def create_element_reference_from_species(sender, instance, created, **kwargs):
    if created:
        ref = instance.reference
        try:
            e = Element.objects.get(species=instance.species)
            if ref not in e.references.all():
                e.references.add(ref)
        except Element.DoesNotExist:
            pass


@receiver(post_delete, sender=SpeciesReference)
def delete_element_reference_from_species(sender, instance, **kwargs):
    ref = instance.reference
    try:
        e = Element.objects.get(species=instance.species)
        if ref in e.references.all():
            e.references.remove(ref)
    except Element.DoesNotExist:
        pass
