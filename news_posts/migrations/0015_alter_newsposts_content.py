# Generated by Django 3.2.8 on 2021-12-10 02:13

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('news_posts', '0014_alter_newsposts_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsposts',
            name='content',
            field=models.TextField(default=django.utils.timezone.now, max_length=512),
            preserve_default=False,
        ),
    ]