from django.contrib.postgres.operations import CreateExtension
from django.db import migrations

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        CreateExtension("anon"),
        migrations.RunSQL("SELECT anon.init()", reverse_sql=migrations.RunSQL.noop),
    ]
