import { Library, Heart, Users, Award } from "lucide-react";
import { Card, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-14 sm:px-6">
      <div className="text-center">
        <Library className="mx-auto h-12 w-12 text-brand-700" aria-hidden />
        <h1 className="mt-4 font-serif text-3xl font-bold text-brand-950 sm:text-4xl">About ShelfSpace</h1>
        <p className="mx-auto mt-4 max-w-2xl leading-relaxed text-brand-500">
          ShelfSpace began with a simple belief: buying books online should feel as warm and personal as
          wandering through your favourite neighbourhood bookshop. We curate every title on our virtual
          shelves, price them fairly, and deliver them with care.
        </p>
      </div>

      <div className="mt-12 grid gap-5 sm:grid-cols-3">
        {[
          { icon: Heart, title: "Reader-first", text: "Every recommendation and collection is chosen by humans, not algorithms alone." },
          { icon: Award, title: "Quality copies", text: "We source directly from authorised distributors so every book is genuine and well-made." },
          { icon: Users, title: "Real support", text: "Questions, returns or gift advice — a real person always answers." },
        ].map((v) => (
          <Card key={v.title}>
            <CardBody className="text-center">
              <v.icon className="mx-auto h-7 w-7 text-brand-600" aria-hidden />
              <h2 className="mt-3 font-semibold text-brand-900">{v.title}</h2>
              <p className="mt-1.5 text-sm text-brand-500">{v.text}</p>
            </CardBody>
          </Card>
        ))}
      </div>

      <div className="mt-12 rounded-2xl bg-brand-950 px-6 py-10 text-center text-white sm:px-12">
        <h2 className="font-serif text-2xl font-bold">Ready to find your next great read?</h2>
        <p className="mx-auto mt-2 max-w-md text-sm text-brand-200">
          Thousands of titles, curated collections and fair prices — all in one place.
        </p>
        <Button variant="secondary" size="lg" className="mt-6" onClick={() => (window.location.href = "/books")}>
          Browse the shelves
        </Button>
      </div>
    </div>
  );
}

export function ContactPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <div className="text-center">
        <h1 className="font-serif text-3xl font-bold text-brand-950">Contact us</h1>
        <p className="mt-3 text-brand-500">
          We love hearing from readers. Reach us any time at{" "}
          <a href="mailto:support@shelfspace.local" className="font-medium text-brand-700 hover:underline">
            support@shelfspace.local
          </a>{" "}
          and we'll reply within one business day.
        </p>
      </div>

      <div className="mt-10 grid gap-5 sm:grid-cols-2">
        <Card>
          <CardBody>
            <h2 className="font-semibold text-brand-900">Store hours</h2>
            <p className="mt-2 text-sm text-brand-500">Online orders: 24×7</p>
            <p className="text-sm text-brand-500">Support: Mon–Sat, 9am–7pm IST</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <h2 className="font-semibold text-brand-900">Head office</h2>
            <p className="mt-2 text-sm text-brand-500">
              42 Marina Boulevard
              <br />
              Mumbai, Maharashtra 400020
              <br />
              India
            </p>
          </CardBody>
        </Card>
      </div>

      <div className="mt-10 rounded-xl border border-brand-100 bg-white p-6 shadow-card">
        <h2 className="font-semibold text-brand-900">Common questions</h2>
        <dl className="mt-4 space-y-4 text-sm">
          <div>
            <dt className="font-medium text-brand-800">When will my order arrive?</dt>
            <dd className="mt-1 text-brand-500">Most orders are delivered within 3–7 business days depending on your location.</dd>
          </div>
          <div>
            <dt className="font-medium text-brand-800">What is your return policy?</dt>
            <dd className="mt-1 text-brand-500">
              Delivered orders can be returned or replaced within 14 days of delivery — request it right from your orders page.
            </dd>
          </div>
          <div>
            <dt className="font-medium text-brand-800">Do you offer cash on delivery?</dt>
            <dd className="mt-1 text-brand-500">Yes, COD is available on eligible orders and pin codes.</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
