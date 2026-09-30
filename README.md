# ShopEase – Django Templates, Forms, Validation & HTMX

Server-rendered storefront (Python 3.10+, Django 4.2 LTS / 5.x, HTMX 1.9, SQLite).
No React/Vue: every dynamic behaviour is a Django view returning HTML that HTMX swaps in.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations store
python manage.py migrate
python manage.py seed              # sample categories + 13 products (with generated images)
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Optional admin: `python manage.py createsuperuser` → `/admin/`.

| URL | Page |
| --- | --- |
| `/` | Product catalog (search, category filter, sort, pagination) |
| `/products/<id>/` | Product detail + add to cart |
| `/manage/products/` | Staff product management (list, add, edit, delete, inline stock/active) |
| `/cart/` → `/checkout/` → `/orders/<id>/confirmation/` | Cart and checkout |

Management pages have no login by design (the brief says no user accounts).

## Project layout

```
config/            settings, urls
store/             models, forms, views, cart.py (session cart), seed command
templates/         base.html, 404.html, page templates
templates/partials/  _product_card, _stock_badge, _product_grid, _pagination, _cart_summary,
                     _cart_container, _checkout_form, _manage_row, _manage_table, _form_field, ...
static/css|js|img/ style.css, app.js, placeholder.svg
media/             uploaded product images (MEDIA_URL / MEDIA_ROOT, dev only)
docs/              Part 1 analysis, reflection, screenshot guide
```

## Why HTMX is loaded from a CDN

`base.html` loads HTMX 1.9.12 from jsDelivr. Reason: it is a single ~14 KB script with no build step,
it is served gzip-compressed from a global edge network, and it keeps the repository free of vendored
minified code. To work offline, download `htmx.min.js` into `static/js/` and change the `<script>` tag to
`{% static 'js/htmx.min.js' %}`.

## Requirement checklist

* **Templates:** `base.html` (`extends`/`block`), 10+ `{% include %}` partials, loops, conditionals,
  `floatformat`, `date`, `truncatewords`, `pluralize`, empty-state messages on catalog, manage list and cart.
  Presentation helpers (`stock_status`, `is_out_of_stock`) live on the model, not in templates.
* **Static/media:** `{% load static %}` everywhere, responsive CSS (mobile/tablet/desktop breakpoints,
  collapsing navbar, tables become stacked cards under 640 px).
* **Forms:** `ProductForm` and `OrderForm` (ModelForms) with custom widgets, labels and help text.
  Checkout creates `Order` + `OrderItem`s from the session cart, reduces stock and clears the cart.
* **Validation (7 rules):** Philippine mobile `clean_phone`; `price > 0`; `stock >= 0`; unique product name;
  full-name check; cross-field `clean()` (delivery needs address + city, Express needs a complete address);
  stock rule on add-to-cart, quantity update and checkout (re-checked inside a transaction).
  Errors show beside fields with `role="alert"`, non-field errors at the top, input is preserved.
  Forms use `novalidate` so the server-side messages can be demonstrated.
* **HTMX (9 interactions):** live search/filter/sort · pagination · add to cart + OOB badge ·
  cart quantity `hx-put` · remove `hx-delete` + `hx-confirm` · shipping change refreshes summary ·
  product form and checkout submit with errors swapped in (`HX-Redirect` on success) ·
  inline stock/active toggle · row delete · `hx-indicator` spinners.
  Views check `HX-Request` and return partials for HTMX, full pages otherwise.
* **Errors:** unknown IDs → `404.html` (inline error partial for HTMX); stale/out-of-stock cart items are
  removed or adjusted with a notice.

## Notes

* Uploaded file inputs cannot be preserved by browsers after a failed submit; every other value is preserved.
* Payment is simulated (Cash on Delivery / Pay Later).
