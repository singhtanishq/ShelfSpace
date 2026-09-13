"""All ORM models. Importing this package registers every table on Base.metadata."""

from app.models.catalog import Author, Book, BookFormat, Category, Publisher  # noqa: F401
from app.models.cart import Cart, CartItem, Coupon, CouponDiscountType, WishlistItem  # noqa: F401
from app.models.inventory import Inventory, InventoryChangeType, InventoryTransaction  # noqa: F401
from app.models.order import (  # noqa: F401
    ALLOWED_STATUS_TRANSITIONS,
    CANCELLABLE_STATUSES,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.returns import (  # noqa: F401
    RefundStatus,
    ReturnItem,
    ReturnReason,
    ReturnRequest,
    ReturnType,
    ReturnStatus,
)
from app.models.review import Notification, NotificationType, Review  # noqa: F401
from app.models.system import AuditLog, EmailLog, EmailStatus, StoreSetting  # noqa: F401
from app.models.user import Address, User, UserRefreshToken, UserRole  # noqa: F401
