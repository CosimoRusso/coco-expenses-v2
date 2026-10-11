from django.apps import apps
from django.test import SimpleTestCase
from expenses.models.timestamp import TimestampModel


class TestTimestamps(SimpleTestCase):
    def test_every_model_of_the_app_is_timestamped(self):
        models = apps.get_app_config("expenses").get_models()

        untimestamped = [
            m.__name__ for m in models if not issubclass(m, TimestampModel)
        ]

        self.assertEqual(untimestamped, [])
