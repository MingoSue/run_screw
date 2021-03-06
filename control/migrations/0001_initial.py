# Generated by Django 2.2 on 2019-06-11 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Records',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cycle', models.IntegerField(blank=True, null=True)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('speed', models.FloatField()),
                ('direction', models.IntegerField()),
                ('current', models.IntegerField()),
                ('weight', models.FloatField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='ScrewConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cycle', models.IntegerField(blank=True, null=True)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('speed', models.FloatField()),
                ('direction', models.IntegerField()),
                ('n', models.IntegerField()),
                ('power', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Weight',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cycle', models.IntegerField(blank=True, null=True)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('weight', models.FloatField(default=0)),
            ],
        ),
    ]
