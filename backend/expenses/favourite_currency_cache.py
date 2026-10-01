"""The amount of each expense in the favourite currency of its user, stored on the expense.

An expense without it is converted the next time the statistics are read.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Iterator

from django.db.models import QuerySet
from expenses import date_utils
from expenses.managers import exchange_rate_manager
from expenses.models import Currency, Expense, User, UserSettings
from expenses.utils.encryption.encryption import (
    decrypt_text_with_key,
    encrypt_text_with_key,
)

BATCH_SIZE = 200
CENTS = Decimal("0.01")


class MissingCryptoKey(Exception):
    pass


class _PlainAmounts:
    field = "amount_favourite_currency"

    def __init__(self, user: User):
        self.user = user

    def missing(self) -> QuerySet[Expense]:
        return Expense.objects.filter(
            user=self.user,
            amount__isnull=False,
            amount_favourite_currency__isnull=True,
        )

    def original(self, expense: Expense) -> Decimal:
        return expense.amount

    def store(self, expense: Expense, amount: Decimal) -> None:
        expense.amount_favourite_currency = amount


class _EncryptedAmounts:
    field = "encrypted_amount_favourite_currency"

    def __init__(self, user: User, crypto_key: str):
        self.user = user
        self.crypto_key = crypto_key

    def missing(self) -> QuerySet[Expense]:
        return Expense.objects.filter(
            user=self.user, encrypted_amount_favourite_currency=""
        ).exclude(encrypted_amount="")

    def original(self, expense: Expense) -> Decimal:
        return Decimal(
            decrypt_text_with_key(self.user, self.crypto_key, expense.encrypted_amount)
        )

    def store(self, expense: Expense, amount: Decimal) -> None:
        expense.encrypted_amount_favourite_currency = encrypt_text_with_key(
            self.user, self.crypto_key, str(amount)
        )


def is_encrypted(user: User) -> bool:
    return UserSettings.objects.get_or_create(user=user)[0].is_encrypted


def favourite_currency(user: User) -> Currency:
    """The currency the statistics of `user` are expressed in."""
    user_settings = UserSettings.objects.get_or_create(user=user)[0]
    return user_settings.preferred_currency or Currency.objects.get(code="USD")


def populate_in_batches(user: User, crypto_key: str | None = None) -> Iterator[int]:
    """Convert the expenses of `user` not converted yet, yielding the size of each batch.

    Each batch is saved as soon as it is converted, so an interrupted run resumes
    from where it stopped.
    """
    amounts = _amounts_of(user, crypto_key)
    currency = favourite_currency(user)
    # Expenses are walked by id, so one that cannot be converted is not fetched twice
    last_id = 0
    while batch := _next_batch(amounts, last_id):
        _convert(amounts, batch, currency)
        last_id = batch[-1].id
        yield len(batch)


def populate_favourite_currency_amounts(
    user: User, crypto_key: str | None = None
) -> int:
    """Convert the expenses of `user` not converted yet and return how many they were."""
    return sum(populate_in_batches(user, crypto_key))


def reset_favourite_currency_amounts(user: User) -> None:
    """Forget the converted amount of every expense of `user`."""
    Expense.objects.filter(user=user).update(
        amount_favourite_currency=None, encrypted_amount_favourite_currency=""
    )


def _amounts_of(
    user: User, crypto_key: str | None
) -> _PlainAmounts | _EncryptedAmounts:
    if not is_encrypted(user):
        return _PlainAmounts(user)
    if not crypto_key:
        raise MissingCryptoKey()
    return _EncryptedAmounts(user, crypto_key)


def _next_batch(
    amounts: _PlainAmounts | _EncryptedAmounts, last_id: int
) -> list[Expense]:
    convertible = amounts.missing().filter(currency__isnull=False, id__gt=last_id)
    return list(convertible.select_related("currency").order_by("id")[:BATCH_SIZE])


def _convert(
    amounts: _PlainAmounts | _EncryptedAmounts, batch: list[Expense], currency: Currency
) -> None:
    today = date_utils.today()
    money = [
        exchange_rate_manager.Money(
            amount=amounts.original(expense),
            currency=expense.currency,
            # An expense not paid yet is converted at the latest rate
            day=expense.expense_date or today,
        )
        for expense in batch
    ]
    converted = exchange_rate_manager.bulk_convert_to_currency(money, currency)
    for expense, entry in zip(batch, converted):
        amounts.store(expense, entry.amount.quantize(CENTS, ROUND_HALF_UP))
    Expense.objects.bulk_update(batch, [amounts.field])
