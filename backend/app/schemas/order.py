"""Cart, checkout, order and return schemas."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class CartItemPublic(BaseModel):
    book_id: int
    title: str
    slug: str
    cover_image: Optional[str] = None
    author_names: str
    unit_price: float
    original_price: float
    discount_percent: float
    quantity: int
    line_total: float
    available_quantity: int
    in_stock: bool


class CartPublic(BaseModel):
    items: List[CartItemPublic]
    subtotal: float
    discount_total: float
    shipping_fee: float
    tax_total: float
    total: float
    coupon: Optional["AppliedCoupon"] = None
    coupon_error: Optional[str] = None
    currency: str = "INR"
    total_quantity: int = 0


class AppliedCoupon(BaseModel):
    code: str
    description: Optional[str] = None


class CartItemAdd(BaseModel):
    book_id: int
    quantity: int = Field(default=1, ge=1, le=99)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=99)


class CartCouponApply(BaseModel):
    code: str = Field(min_length=1, max_length=40)


class CartMergeItem(BaseModel):
    book_id: int
    quantity: int = Field(default=1, ge=1, le=99)


class CartMergeRequest(BaseModel):
    items: List[CartMergeItem]


class WishlistItemPublic(BaseModel):
    book_id: int
    title: str
    slug: str
    cover_image: Optional[str] = None
    author_names: str
    price: float
    effective_price: float
    discount_percent: float
    available_quantity: int
    added_at: datetime


class ShippingAddressInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=20)
    line1: str = Field(min_length=4, max_length=255)
    line2: Optional[str] = Field(default=None, max_length=255)
    city: str = Field(min_length=2, max_length=80)
    state: str = Field(min_length=2, max_length=80)
    postal_code: str = Field(min_length=4, max_length=20)
    country: str = Field(default="India", max_length=80)


class CheckoutRequest(BaseModel):
    address_id: Optional[int] = None
    shipping_address: Optional[ShippingAddressInput] = None
    payment_method: Literal["cod", "card", "upi"]
    notes: Optional[str] = Field(default=None, max_length=1000)

    # Mock gateway fields (no real money moves; documented demo behavior).
    card_number: Optional[str] = None
    upi_id: Optional[str] = None


class OrderItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: Optional[int]
    title: str
    author_names: str
    cover_image: Optional[str]
    isbn: Optional[str]
    unit_price: float
    quantity: int
    line_total: float


class OrderStatusHistoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: Optional[str]
    to_status: str
    note: Optional[str]
    created_at: datetime
    changed_by_id: Optional[int] = None


class ReturnItemPublic(BaseModel):
    order_item_id: int
    quantity: int
    title: str = ""


class ReturnRequestPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    return_number: str
    order_id: int
    order_number: str = ""
    user_id: int
    type: str
    status: str
    reason: str
    description: Optional[str]
    refund_amount: Optional[float]
    refund_status: str
    admin_note: Optional[str]
    created_at: datetime
    decided_at: Optional[datetime]
    completed_at: Optional[datetime]
    items: List[ReturnItemPublic] = []


class OrderPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    user_id: int
    status: str
    payment_method: str
    payment_status: str
    subtotal: float
    discount_total: float
    shipping_fee: float
    tax_total: float
    total: float
    coupon_code: Optional[str]
    shipping_address: dict
    notes: Optional[str]
    placed_at: datetime
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    items: List[OrderItemPublic] = []
    status_history: List[OrderStatusHistoryPublic] = []
    returns: List[ReturnRequestPublic] = []


class OrderList(BaseModel):
    items: List[OrderPublic]
    total: int
    page: int
    page_size: int
    pages: int


class StatusUpdateRequest(BaseModel):
    status: Literal[
        "pending",
        "confirmed",
        "processing",
        "shipped",
        "out_for_delivery",
        "delivered",
        "cancelled",
        "returned",
    ]
    note: Optional[str] = Field(default=None, max_length=255)


class CancelOrderRequest(BaseModel):
    note: Optional[str] = Field(default=None, max_length=255)


class ReturnItemInput(BaseModel):
    order_item_id: int
    quantity: int = Field(ge=1, le=99)


class ReturnCreate(BaseModel):
    type: Literal["return", "replacement"]
    reason: Literal[
        "damaged", "defective", "wrong_item", "not_as_described", "changed_mind", "other"
    ]
    description: Optional[str] = Field(default=None, max_length=2000)
    items: List[ReturnItemInput] = Field(min_length=1)


class ReturnDecision(BaseModel):
    note: Optional[str] = Field(default=None, max_length=255)


# ---- Coupons ----


class CouponPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    description: Optional[str]
    discount_type: str
    value: float
    min_order_amount: float
    max_discount_amount: Optional[float]
    usage_limit: Optional[int]
    used_count: int
    starts_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime


class CouponCreate(BaseModel):
    code: str = Field(min_length=3, max_length=40)
    description: Optional[str] = Field(default=None, max_length=255)
    discount_type: Literal["percent", "fixed"]
    value: float = Field(gt=0)
    min_order_amount: float = Field(default=0, ge=0)
    max_discount_amount: Optional[float] = Field(default=None, gt=0)
    usage_limit: Optional[int] = Field(default=None, ge=1)
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "code": "WELCOME10",
                "discount_type": "percent",
                "value": 10,
                "min_order_amount": 500,
                "max_discount_amount": 200,
            }
        }


class CouponUpdate(BaseModel):
    description: Optional[str] = None
    discount_type: Optional[Literal["percent", "fixed"]] = None
    value: Optional[float] = Field(default=None, gt=0)
    min_order_amount: Optional[float] = Field(default=None, ge=0)
    max_discount_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


# ---- Notifications ----


class NotificationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str
    body: str
    link: Optional[str]
    is_read: bool
    created_at: datetime


class NotificationList(BaseModel):
    items: List[NotificationPublic]
    total: int
    page: int
    page_size: int
    pages: int
    unread_count: int = 0


CartPublic.model_rebuild()
