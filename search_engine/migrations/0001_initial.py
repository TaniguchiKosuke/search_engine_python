# Generated by Django 3.2.7 on 2021-10-17 07:58

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='作成日時')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('deleted_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='削除日時')),
                ('title', models.CharField(max_length=1024)),
                ('url', models.URLField()),
                ('content', models.TextField(blank=True, max_length=1024, null=True)),
                ('index_keyword', models.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Index',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='作成日時')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('deleted_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='削除日時')),
                ('keyword', models.TextField()),
                ('index_json', models.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ToAnalyzePage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='作成日時')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('deleted_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='削除日時')),
                ('url', models.URLField()),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
