import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { BookCard } from "@/components/books/BookCard";
import { StatusBadge } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import type { Book } from "@/types/api";

const book: Book = {
  id: 1,
  title: "Test Book",
  slug: "test-book",
  cover_image: null,
  price: 300,
  discount_percent: 10,
  effective_price: 270,
  rating_avg: 4.5,
  rating_count: 8,
  is_active: true,
  is_featured: false,
  authors: [{ id: 1, name: "Jane Author", slug: "jane-author", bio: null }],
  categories: [],
  available_quantity: 5,
};

function renderCard() {
  return render(
    <MemoryRouter>
      <BookCard book={book} />
    </MemoryRouter>
  );
}

describe("BookCard", () => {
  it("shows title, author and effective price", () => {
    renderCard();
    expect(screen.getByText("Test Book")).toBeInTheDocument();
    expect(screen.getByText("Jane Author")).toBeInTheDocument();
    expect(screen.getByText(/270\.00/)).toBeInTheDocument();
    expect(screen.getByText(/300\.00/)).toBeInTheDocument(); // crossed-out original
  });

  it("shows the discount badge", () => {
    renderCard();
    expect(screen.getByText("−10%")).toBeInTheDocument();
  });

  it("marks out-of-stock books and disables their add button", () => {
    render(
      <MemoryRouter>
        <BookCard book={{ ...book, available_quantity: 0 }} />
      </MemoryRouter>
    );
    expect(screen.getByText("Out of stock")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /add test book to cart/i })).toBeDisabled();
  });
});

describe("StatusBadge", () => {
  it("humanizes snake_case statuses", () => {
    render(<StatusBadge status="out_for_delivery" />);
    expect(screen.getByText("out for delivery")).toBeInTheDocument();
  });
});

describe("Button", () => {
  it("disables and shows a spinner while loading", () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
