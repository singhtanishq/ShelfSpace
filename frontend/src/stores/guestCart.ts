/** Guest cart (anonymous visitors) persisted in localStorage.

 * Once signed in, the server-backed cart takes over; the guest cart is
 * merged into it via POST /cart/merge and cleared.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface GuestCartItem {
  book_id: number;
  quantity: number;
}

interface GuestCartState {
  items: GuestCartItem[];
  addItem: (bookId: number, quantity?: number) => void;
  removeItem: (bookId: number) => void;
  clear: () => void;
}

export const useGuestCart = create<GuestCartState>()(
  persist(
    (set) => ({
      items: [],
      addItem: (bookId, quantity = 1) =>
        set((state) => {
          const existing = state.items.find((i) => i.book_id === bookId);
          if (existing) {
            return {
              items: state.items.map((i) =>
                i.book_id === bookId ? { ...i, quantity: Math.min(i.quantity + quantity, 99) } : i
              ),
            };
          }
          return { items: [...state.items, { book_id: bookId, quantity }] };
        }),
      removeItem: (bookId) =>
        set((state) => ({ items: state.items.filter((i) => i.book_id !== bookId) })),
      clear: () => set({ items: [] }),
    }),
    { name: "shelfspace.guest-cart" }
  )
);
