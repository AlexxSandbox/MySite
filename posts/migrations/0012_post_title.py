# Generated by Django 2.2.9 on 2020-07-07 17:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_auto_20200706_1818'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='title',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Заголовок'),
        ),
    ]