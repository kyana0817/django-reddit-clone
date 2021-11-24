# Generated by Django 3.2.8 on 2021-11-17 03:28

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0001_initial'),
        ('news_posts', '0002_newsposts_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsposts',
            name='community',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='communities.communities'),
            preserve_default=False,
        ),
    ]
