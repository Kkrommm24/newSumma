# Generated by Django 5.1.6 on 2025-06-04 01:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recommender', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='summaryviewlog',
            name='duration_seconds',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
