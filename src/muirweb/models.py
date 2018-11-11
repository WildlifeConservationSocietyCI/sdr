from django.db import models


class DefinitionType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class FrequencyType(models.Model):
    name = models.CharField(max_length=255)
    maxprob = models.DecimalField(max_digits=4, decimal_places=1)

    def __str__(self):
        return u'%s [maxprob: %s]' % (self.name, self.maxprob)


class GroupLabel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'relationship type label'

    def __str__(self):
        return self.name


class Group(models.Model):
    label = models.ForeignKey(GroupLabel, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'relationship type'

    def __str__(self):
        label = ''
        if self.label is not None:
            label = '%s ' % self.label.name or ''
        return u'%s[%s]' % (label, self.pk)


class InteractionType(models.Model):
    name = models.CharField(max_length=100)
    operation = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class StateLabel(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class State(models.Model):
    label = models.ForeignKey(StateLabel, on_delete=models.PROTECT)

    def __str__(self):
        label = ''
        if self.label is not None:
            label = '%s ' % self.label.name or ''
        return u'%s[%s]' % (label, self.pk)


class StrengthType(models.Model):
    name = models.CharField(max_length=100)
    prob = models.SmallIntegerField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return u'%s [%s%%]' % (self.name, self.prob)


class Element(models.Model):
    elementid = models.DecimalField(unique=True, max_digits=7, decimal_places=2)
    name = models.CharField(max_length=255)
    species = models.OneToOneField('species.Species', null=True, blank=True, related_name='element',
                                   on_delete=models.SET_NULL)
    definitiontype = models.ForeignKey(DefinitionType, verbose_name='subject type', null=True, blank=True,
                                       on_delete=models.PROTECT)
    frequencytype = models.ForeignKey(FrequencyType, null=True, blank=True, on_delete=models.PROTECT)
    spatially_explicit = models.BooleanField(default=True)
    mapped_manually = models.BooleanField(default=False)
    native_units = models.BooleanField(default=False)
    subset_rule = models.CharField(max_length=255, blank=True,
                                   help_text='operands: [element_id]; operators: +-/*<>== logical_and() logical_or()')
    adjacency_rule = models.IntegerField(null=True, blank=True, help_text='Within x m (integer)')
    description = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True, null=True, blank=True)
    references = models.ManyToManyField('base.Reference', blank=True)

    def save(self, *args, **kwargs):
        if self.species:
            self.name = self.species.__str__()
        else:
            self.name = ''
        super(Element, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Relationship(models.Model):
    subject = models.ForeignKey(Element, related_name='subject_relationships', on_delete=models.CASCADE)
    object = models.ForeignKey(Element, related_name='object_relationships', on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    relationshiptype = models.ForeignKey(Group, on_delete=models.CASCADE)
    strengthtype = models.ForeignKey(StrengthType, on_delete=models.PROTECT)
    interactiontype = models.ForeignKey(InteractionType, on_delete=models.PROTECT)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        try:
            cf = GroupLabel.objects.get(name='condition for')
            if self.pk is None and self.relationshiptype.label == cf:
                # because rel is new, we don't need to exclude self
                other_cf_rels = self.subject.subject_relationships.filter(relationshiptype=self.relationshiptype)
                if other_cf_rels.count() > 0:
                    new_group = Group(label=cf)
                    new_group.save()
                    self.relationshiptype = new_group
        except GroupLabel.DoesNotExist:
            pass
        super(Relationship, self).save(*args, **kwargs)

    def __str__(self):
        return u'%s > %s' % (self.subject, self.object)
