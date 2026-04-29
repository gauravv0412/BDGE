# Generated manually for Step 38A

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BillingProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan_key", models.CharField(db_index=True, default="free", max_length=32)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=models.deletion.CASCADE,
                        related_name="billing_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Billing profile",
                "verbose_name_plural": "Billing profiles",
            },
        ),
        migrations.CreateModel(
            name="MonthlyPresentationUsage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year_month", models.CharField(db_index=True, max_length=7)),
                ("presentation_count", models.PositiveIntegerField(default=0)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="monthly_presentation_usage",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-year_month"],
                "verbose_name": "Monthly presentation usage",
                "verbose_name_plural": "Monthly presentation usages",
            },
        ),
        migrations.AddConstraint(
            model_name="monthlypresentationusage",
            constraint=models.UniqueConstraint(fields=("user", "year_month"), name="billing_monthlyusage_user_period_uniq"),
        ),
    ]
