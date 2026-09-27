from django.urls import reverse
from expenses.models import PaymentMethod
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.payment_method_factories import PaymentMethodFactory
from expenses.tests.factories.user_factories import UserFactory
from rest_framework import status


class TestPaymentMethods(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.list_url = reverse("expenses:payment-methods-list")

    def details_url(self, id: int) -> str:
        return reverse("expenses:payment-methods-detail", args=[id])

    def setUp(self):
        self.login(self.user.email)

    def test_create_payment_method_belongs_to_current_user(self):
        res = self.client.post(
            self.list_url, {"code": "revolut", "name": "Revolut"}, format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        payment_method = PaymentMethod.objects.get(id=res.data["id"])
        self.assertEqual(payment_method.user, self.user)
        self.assertEqual(payment_method.code, "revolut")
        self.assertEqual(payment_method.name, "Revolut")
        self.assertTrue(payment_method.is_active)

    def test_create_payment_method_without_code_is_rejected(self):
        res = self.client.post(self.list_url, {"name": "Revolut"}, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", res.data)

    def test_create_payment_method_with_duplicate_code_is_rejected(self):
        PaymentMethodFactory(user=self.user, code="cash")

        res = self.client.post(
            self.list_url, {"code": "cash", "name": "Cash"}, format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", res.data)

    def test_same_code_is_allowed_for_different_users(self):
        PaymentMethodFactory(user=UserFactory(), code="cash")

        res = self.client.post(
            self.list_url, {"code": "cash", "name": "Cash"}, format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_update_payment_method_keeping_its_code(self):
        payment_method = PaymentMethodFactory(user=self.user, code="cash")

        res = self.client.put(
            self.details_url(payment_method.id),
            {"code": "cash", "name": "Cash", "is_active": False},
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        payment_method.refresh_from_db()
        self.assertFalse(payment_method.is_active)

    def test_list_shows_only_own_payment_methods(self):
        own = PaymentMethodFactory(user=self.user, name="Visa")
        PaymentMethodFactory(user=UserFactory(), name="Amex")

        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual([pm["id"] for pm in res.data], [own.id])

    def test_filter_by_is_active(self):
        PaymentMethodFactory(user=self.user, name="Old card", is_active=False)
        active = PaymentMethodFactory(user=self.user, name="New card")

        res = self.client.get(self.list_url, {"is_active": "true"})

        self.assertEqual([pm["id"] for pm in res.data], [active.id])

    def test_cannot_update_payment_method_of_another_user(self):
        other = PaymentMethodFactory(user=UserFactory(), name="Amex")

        res = self.client.put(
            self.details_url(other.id), {"code": "mine", "name": "Mine"}, format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_unused_payment_method(self):
        payment_method = PaymentMethodFactory(user=self.user)

        res = self.client.delete(self.details_url(payment_method.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PaymentMethod.objects.filter(id=payment_method.id).exists())

    def test_delete_payment_method_used_by_an_expense_is_rejected(self):
        payment_method = PaymentMethodFactory(user=self.user)
        ExpenseFactory(user=self.user, payment_method=payment_method)

        res = self.client.delete(self.details_url(payment_method.id))

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("deactivate it instead", res.data["detail"])
        self.assertTrue(PaymentMethod.objects.filter(id=payment_method.id).exists())
