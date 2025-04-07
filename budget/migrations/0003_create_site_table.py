from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('budget', '0002_create_default_site'),
    ]

    operations = [
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('domain', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'django_site',
            },
        ),
        migrations.RunSQL(
            sql="""
            INSERT INTO django_site (id, domain, name)
            VALUES (1, 'localhost:8000', 'localhost')
            ON CONFLICT (id) DO NOTHING;
            """,
            reverse_sql="""
            DELETE FROM django_site WHERE id = 1;
            """
        ),
    ] 