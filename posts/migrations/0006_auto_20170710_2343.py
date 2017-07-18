# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-10 23:43
from __future__ import unicode_literals

import FMTC.storage
from django.db import migrations, models
import posts.models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20170710_2311'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='thumbnail',
            field=models.ImageField(storage=FMTC.storage.GoogleCloudStorage(), upload_to=posts.models.format_storage_path),
        ),
    ]