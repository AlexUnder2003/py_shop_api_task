# Generated by Django 5.1.5 on 2025-01-17 14:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_refreshtokenmodel'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RefreshToken',
        ),
    ]
