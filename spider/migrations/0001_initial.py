# Generated by Django 2.1.7 on 2019-03-27 02:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Spider',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, null=True)),
                ('phone', models.CharField(max_length=100)),
                ('corporate_name', models.CharField(max_length=50)),
                ('city', models.CharField(max_length=50)),
                ('region', models.CharField(max_length=50)),
                ('address', models.CharField(max_length=100)),
                ('url', models.CharField(max_length=250, unique=True)),
                ('year', models.IntegerField(max_length=4)),
                ('personnel_scale', models.CharField(max_length=50)),
                ('industry', models.CharField(max_length=50)),
                ('keyword', models.CharField(max_length=50)),
                ('datetime', models.DateField()),
                ('source', models.CharField(max_length=25)),
                ('insertdate', models.DateField(auto_now_add=True)),
            ],
            options={
                'db_table': 'spider',
            },
        ),
    ]