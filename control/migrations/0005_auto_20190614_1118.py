# Generated by Django 2.2 on 2019-06-14 03:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0004_auto_20190614_1031'),
    ]

    operations = [
        migrations.AddField(
            model_name='records',
            name='is_settled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='screwconfig',
            name='actual_speed',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='screwconfig',
            name='auto',
            field=models.IntegerField(default=1),
        ),
    ]
