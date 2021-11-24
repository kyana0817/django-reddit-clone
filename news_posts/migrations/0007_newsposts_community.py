# Generated by Django 3.2.8 on 2021-11-24 02:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0003_communities_updated_at'),
        ('news_posts', '0006_remove_newsposts_community'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsposts',
            name='community',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='communities.communities'),
            preserve_default=False,
        ),
    ]
