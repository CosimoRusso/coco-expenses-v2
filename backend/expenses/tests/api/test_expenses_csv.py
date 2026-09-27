import csv
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from expenses.models import Expense, PaymentMethod
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.payment_method_factories import PaymentMethodFactory
from expenses.tests.factories.user_factories import UserFactory
from expenses.tests.factories.user_settings_factories import UserSettingsFactory
from rest_framework import status
from rest_framework.reverse import reverse

HEADER = (
    "expense_date,description,amount,amortization_start_date,"
    "amortization_end_date,category,trip,currency,is_expense"
)
ROW = "2025-01-01,coffee,2.50,2025-01-01,2025-01-01,food,,EUR,True"


class TestImportExpensesFromCsv(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        UserSettingsFactory(user=cls.user, is_encrypted=False)
        CurrencyFactory(code="EUR")
        cls.url = reverse("expenses:expenses-load-from-csv")

    def setUp(self):
        self.login(self.user.email)

    def upload(self, content: str):
        file = SimpleUploadedFile("expenses.csv", content.encode("utf-8"))
        return self.client.post(self.url, {"file": file}, format="multipart")

    def test_import_links_existing_payment_method_by_code(self):
        card = PaymentMethodFactory(user=self.user, code="card", name="My card")

        res = self.upload(f"{HEADER},payment_method\n{ROW},card\n")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.get().payment_method, card)
        self.assertEqual(PaymentMethod.objects.count(), 1)

    def test_import_creates_missing_payment_method(self):
        res = self.upload(f"{HEADER},payment_method\n{ROW},cash\n")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        payment_method = Expense.objects.get().payment_method
        self.assertEqual(payment_method.user, self.user)
        self.assertEqual(payment_method.code, "cash")
        self.assertEqual(payment_method.name, "cash")

    def test_import_does_not_use_payment_method_of_another_user(self):
        other = PaymentMethodFactory(user=UserFactory(), code="card")

        self.upload(f"{HEADER},payment_method\n{ROW},card\n")

        payment_method = Expense.objects.get().payment_method
        self.assertNotEqual(payment_method, other)
        self.assertEqual(payment_method.user, self.user)

    def test_import_with_empty_payment_method_leaves_it_unset(self):
        res = self.upload(f"{HEADER},payment_method\n{ROW},\n")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(Expense.objects.get().payment_method)

    def test_import_file_without_payment_method_column(self):
        res = self.upload(f"{HEADER}\n{ROW}\n")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(Expense.objects.get().payment_method)


class TestExportExpensesToCsv(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        UserSettingsFactory(user=cls.user, is_encrypted=False)
        cls.url = reverse("expenses:expenses-download-csv")

    def setUp(self):
        self.login(self.user.email)

    def exported_rows(self) -> list[dict]:
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        content = b"".join(res.streaming_content).decode("utf-8")
        return list(csv.DictReader(io.StringIO(content)))

    def test_export_writes_payment_method_code(self):
        card = PaymentMethodFactory(user=self.user, code="card", name="My card")
        ExpenseFactory(
            user=self.user, payment_method=card, currency=CurrencyFactory(code="EUR")
        )

        rows = self.exported_rows()

        self.assertEqual(rows[0]["payment_method"], "card")

    def test_export_leaves_payment_method_empty_when_unset(self):
        ExpenseFactory(
            user=self.user, payment_method=None, currency=CurrencyFactory(code="EUR")
        )

        rows = self.exported_rows()

        self.assertEqual(rows[0]["payment_method"], "")

    def test_export_contains_only_own_expenses(self):
        euro = CurrencyFactory(code="EUR")
        ExpenseFactory(user=self.user, description="mine", currency=euro)
        ExpenseFactory(user=UserFactory(), description="not mine", currency=euro)

        rows = self.exported_rows()

        self.assertEqual([row["description"] for row in rows], ["mine"])
