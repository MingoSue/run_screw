# Generated by Django 2.2 on 2019-06-12 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='records',
            name='status',
            field=models.IntegerField(choices=[(0, '待机'), (1, '开始'), (-1, '结束')], default=0),
        ),
    ]
