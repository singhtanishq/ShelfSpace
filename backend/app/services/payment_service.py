"""Payment abstraction.

The mock gateway simulates authorization without touching real money so the
platform can be demoed end-to-end. Swap `MockPaymentGateway` for a Stripe/
Razorpay adapter without touching the checkout flow: implement `charge()`
and register the provider in PAYMENT_PROVIDERS.
"""

import secrets
from typing import Optional, Protocol

from app.core.logging import get_logger
from app.models import PaymentMethod
from app.utils.exceptions import ValidationError

logger = get_logger(__name__)


class PaymentGateway(Protocol):
    def charge(self, *, amount: float, method: PaymentMethod, reference_hint: Optional[str]) -> str:
        """Authorize `amount`; return the provider transaction reference."""
        ...


class MockPaymentGateway:
    """Always authorizes. Card/UPI inputs are validated for shape only."""

    def charge(self, *, amount: float, method: PaymentMethod, reference_hint: Optional[str] = None) -> str:
        if method == PaymentMethod.CARD:
            if not reference_hint or not reference_hint.replace(" ", "").isdigit() or len(reference_hint.replace(" ", "")) < 12:
                raise ValidationError("A valid card number is required for card payments.")
        elif method == PaymentMethod.UPI:
            if not reference_hint or "@" not in reference_hint:
                raise ValidationError("A valid UPI ID is required for UPI payments.")
        # Deterministic-looking fake reference; no real money moves.
        return f"mock_{method.value}_{secrets.token_hex(8)}"


PAYMENT_PROVIDERS: dict[str, PaymentGateway] = {
    "mock": MockPaymentGateway(),
}


def charge(*, amount: float, method: PaymentMethod, provider: str = "mock", reference_hint: Optional[str] = None) -> str:
    gateway = PAYMENT_PROVIDERS.get(provider)
    if gateway is None:
        raise ValidationError(f"Unknown payment provider: {provider}")
    return gateway.charge(amount=amount, method=method, reference_hint=reference_hint)
