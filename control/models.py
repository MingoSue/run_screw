import datetime
import time as time_
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


class ScrewConfig(models.Model):
    speed = models.FloatField()
    direction = models.IntegerField()
    n = models.IntegerField()
    power = models.IntegerField()


class Screw(models.Model):
    speed = models.FloatField()
    direction = models.IntegerField()
    current = models.IntegerField()


class Weight(models.Model):
    weight = models.FloatField(default=0)

