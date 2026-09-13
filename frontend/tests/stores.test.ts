import { describe, it, expect, beforeEach } from "vitest";
import { useGuestCart } from "@/stores/guestCart";
import { useAuthStore } from "@/stores/auth";
import { formatCurrency, formatDate, mediaUrl, truncate } from "@/utils";

describe("guestCart store", () => {
  beforeEach(() => {
    useGuestCart.getState().clear();
  });

  it("adds a new item", () => {
    useGuestCart.getState().addItem(1, 2);
    expect(useGuestCart.getState().items).toEqual([{ book_id: 1, quantity: 2 }]);
  });

  it("merges quantities for the same book", () => {
    useGuestCart.getState().addItem(1, 1);
    useGuestCart.getState().addItem(1, 2);
    expect(useGuestCart.getState().items).toEqual([{ book_id: 1, quantity: 3 }]);
  });

  it("caps quantity at 99", () => {
    useGuestCart.getState().addItem(1, 99);
    useGuestCart.getState().addItem(1, 5);
    expect(useGuestCart.getState().items[0].quantity).toBe(99);
  });

  it("removes and clears items", () => {
    useGuestCart.getState().addItem(1, 1);
    useGuestCart.getState().addItem(2, 1);
    useGuestCart.getState().removeItem(1);
    expect(useGuestCart.getState().items).toEqual([{ book_id: 2, quantity: 1 }]);
    useGuestCart.getState().clear();
    expect(useGuestCart.getState().items).toEqual([]);
  });
});

describe("auth store", () => {
  it("stores and clears the session", () => {
    const user = {
      id: 1, email: "jane@example.com", username: "jane", full_name: "Jane",
      phone: null, role: "customer" as const, is_active: true, is_verified: true, created_at: "2026-01-01T00:00:00Z",
    };
    useAuthStore.getState().setSession(user, "access-1", "refresh-1");
    expect(useAuthStore.getState().accessToken).toBe("access-1");
    expect(useAuthStore.getState().getRefreshToken()).toBe("refresh-1");

    useAuthStore.getState().clearSession();
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().getRefreshToken()).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });
});

describe("utils", () => {
  it("formats INR currency", () => {
    expect(formatCurrency(1234.5)).toMatch(/₹1,234\.50/);
  });

  it("formats dates readably", () => {
    expect(formatDate("2026-09-14T10:00:00Z")).toMatch(/14 Sep 2026|13 Sep 2026/); // timezone-dependent
    expect(formatDate(null)).toBe("—");
  });

  it("prefixes media paths and passes through URLs", () => {
    expect(mediaUrl("media/covers/x.svg")).toBe("/media/covers/x.svg");
    expect(mediaUrl("https://cdn.example.com/x.png")).toBe("https://cdn.example.com/x.png");
    expect(mediaUrl(null)).toBeUndefined();
  });

  it("truncates long text", () => {
    expect(truncate("short", 10)).toBe("short");
    expect(truncate("a very long title indeed", 12)).toMatch(/…$/);
  });
});
