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


class Records(models.Model):
    STAND = 0
    START = 1
    END = -1
    STATUS_CHOICES = (
        (STAND, '待机'),
        (START, '开始'),
        (END, '结束'),
    )

    cycle = models.IntegerField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    speed = models.FloatField()
    direction = models.IntegerField()
    current = models.IntegerField()
    weight = models.FloatField(default=0)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STAND)


class Weight(models.Model):
    cycle = models.IntegerField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    weight = models.FloatField(default=0)

