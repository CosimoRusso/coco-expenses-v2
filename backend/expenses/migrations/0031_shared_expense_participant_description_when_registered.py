from django.db import migrations, models
from django.db.models import F, OuterRef, Subquery


def keep_descriptions_of_registered_shares(apps, schema_editor):
    SharedExpense = apps.get_model("expenses", "SharedExpense")
    SharedExpenseParticipant = apps.get_model("expenses", "SharedExpenseParticipant")
    description = SharedExpense.objects.filter(id=OuterRef("shared_expense_id"))
    registered = SharedExpenseParticipant.objects.filter(expense__isnull=False)
    registered.exclude(user=F("shared_expense__created_by")).update(
        description_when_registered=Subquery(description.values("description")[:1])
    )


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0030_user_settings_default_statistics_method"),
    ]

    operations = [
        migrations.AddField(
            model_name="sharedexpenseparticipant",
            name="description_when_registered",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.RunPython(
            keep_descriptions_of_registered_shares, migrations.RunPython.noop
        ),
    ]
