import datetime
import time as time_
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


class ScrewConfig(models.Model):
    cycle = models.IntegerField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    speed = models.FloatField()
    direction = models.IntegerField()
    n = models.IntegerField()
    power = models.IntegerField()
    actual_speed = models.FloatField(null=True, blank=True)
    auto = models.IntegerField(default=1)


class Records(models.Model):
    cycle = models.IntegerField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    speed = models.FloatField(null=True, blank=True)
    direction = models.IntegerField()
    current = models.IntegerField()
    weight = models.FloatField(default=0)
    config_weight = models.FloatField(default=0)
    d_weight = models.FloatField(default=0)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    total_time = models.IntegerField(default=0)
    actual_speed = models.FloatField(null=True, blank=True)
    is_settled = models.BooleanField(default=False)
    screw_type = models.CharField(max_length=128, blank=True, null=True)


class Weight(models.Model):
    cycle = models.IntegerField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    weight = models.FloatField(default=0)

