import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from expenses.models.expense import Expense
from expenses.models.user import User


def derive_key_from_password(password: str, user_id: int) -> str:
    """Derives a unique 32-byte base64 key using the password and user ID as a salt."""
    # We use a global system pepper combined with user ID as the salt
    salt = f"{settings.SECRET_KEY[:16]}-{user_id}".encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,  # Standard computational difficulty
    )

    derived_bytes = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(derived_bytes).decode()


def get_fernet_for_user(user_crypto_key: str) -> Fernet:
    return Fernet(user_crypto_key.encode())


def encrypt_user_data(user: User, password: str) -> None:
    """Encrypts user data using a derived key from the password."""
    user_crypto_key = derive_key_from_password(password, user.id)
    fernet = get_fernet_for_user(user_crypto_key)

    expenses = Expense.objects.filter(user=user).order_by("id").iterator()
    for expense in expenses:
        expense.encrypted_description = fernet.encrypt(
            expense.description.encode()
        ).decode()
        expense.encrypted_amount = fernet.encrypt(str(expense.amount).encode()).decode()
        expense.description = ""
        expense.amount = None
        expense.save(
            update_fields=[
                "description",
                "amount",
                "encrypted_description",
                "encrypted_amount",
            ]
        )


def decrypt_user_data(user: User, password: str) -> None:
    """Decrypts user data using a derived key from the password."""
    user_crypto_key = derive_key_from_password(password, user.id)
    fernet = get_fernet_for_user(user_crypto_key)

    expenses = Expense.objects.filter(user=user).order_by("id").iterator()
    for expense in expenses:
        expense.description = fernet.decrypt(
            expense.encrypted_description.encode()
        ).decode()
        expense.amount = float(
            fernet.decrypt(expense.encrypted_amount.encode()).decode()
        )
        expense.encrypted_description = ""
        expense.encrypted_amount = ""
        expense.save(
            update_fields=[
                "description",
                "amount",
                "encrypted_description",
                "encrypted_amount",
            ]
        )


def encrypt_text_with_password(user: User, password: str, text: str) -> str:
    """Encrypts a given text using a derived key from the password."""
    user_crypto_key = derive_key_from_password(password, user.id)
    fernet = get_fernet_for_user(user_crypto_key)
    return fernet.encrypt(text.encode()).decode()


def encrypt_text_with_key(user: User, user_crypto_key: str, text: str) -> str:
    """Encrypts a given text using a provided user crypto key."""
    fernet = get_fernet_for_user(user_crypto_key)
    return fernet.encrypt(text.encode()).decode()


def decrypt_text_with_password(user: User, password: str, encrypted_text: str) -> str:
    """Decrypts a given encrypted text using a derived key from the password."""
    user_crypto_key = derive_key_from_password(password, user.id)
    fernet = get_fernet_for_user(user_crypto_key)
    return fernet.decrypt(encrypted_text.encode()).decode()


def decrypt_text_with_key(user: User, user_crypto_key: str, encrypted_text: str) -> str:
    """Decrypts a given encrypted text using a provided user crypto key."""
    fernet = get_fernet_for_user(user_crypto_key)
    return fernet.decrypt(encrypted_text.encode()).decode()
