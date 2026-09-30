# Part 1 – Interface and Data-Entry Analysis (ShopEase)

## 1. Pages and data-entry points

| Page | Data-entry points |
| --- | --- |
| Catalog `/` | Search box (`q`), category filter, sort selector, pagination links, Add to Cart (quantity 1) |
| Product detail `/products/<id>/` | Quantity field (min 1, max = stock) |
| Product management `/manage/products/` | Search box, inline stock input, inline active toggle, Delete |
| Product form | name, category, description, price, stock, image, active checkbox |
| Cart `/cart/` | Quantity input per line, Remove button |
| Checkout `/checkout/` | full name, email, phone, address, city, shipping method, payment method |

## 2. Full-page rendering vs. HTMX partial updates

| Interaction | Approach | Reason |
| --- | --- | --- |
| First load of every page, navigation between pages | Full page | Different layout/URL; SEO and bookmarking; works without JS |
| Catalog search / filter / sort / pagination | HTMX → `#product-grid` | Only the grid changes; navbar and filters stay; `hx-push-url` keeps URLs shareable |
| Add to cart | HTMX → inline message + OOB `#cart-badge` | Customer stays on the list; two areas update in one response |
| Cart quantity change, remove item | HTMX → `#cart-container` | Totals must recalculate without losing scroll position |
| Shipping method change | HTMX → `#order-summary` | Only the total changes; the half-filled form is untouched |
| Checkout / product form submit | HTMX → form (`outerHTML`) on error; `HX-Redirect` on success | Errors appear in place with input preserved; success needs a new URL |
| Inline stock/active, row delete | HTMX → `closest tr` | One row changes |
| Order confirmation, product create/edit pages, 404 | Full page | New resource/URL and printable receipt |

## 3. Validation rules

| Form / field | Rules |
| --- | --- |
| Product name | required, ≥ 3 chars, unique (case-insensitive) |
| Category | required, must exist |
| Price | required, decimal (max 10 digits, 2 decimals), **> 0** |
| Stock | required, whole number, **≥ 0** |
| Image | optional, must be a valid image |
| Add to cart / cart quantity | whole number ≥ 1; **existing cart qty + requested ≤ stock** |
| Full name | required, at least two words |
| Email | required, valid format, lower-cased |
| Phone | required; **`09XXXXXXXXX` or `+639XXXXXXXXX`** (spaces/dashes stripped) |
| Address / city | optional for pickup; **required for Standard/Express**; Express address ≥ 10 characters (cross-field `clean()`) |
| Shipping / payment | must be one of the allowed choices |
| Checkout (whole order) | every line re-checked against live stock inside a transaction; stale items reported and removed |

## 4. Partial templates and HTMX attributes

| Partial | HTMX attributes |
| --- | --- |
| `_product_grid.html`, `_product_card.html`, `_stock_badge.html`, `_pagination.html` | `hx-post`, `hx-vals`, `hx-target="#msg-<id>"` (card); `hx-get`, `hx-target="#product-grid"`, `hx-push-url` (pagination) |
| `_add_result.html`, `_cart_badge.html` | `hx-swap-oob="true"` for `#cart-badge` |
| `_cart_container.html`, `_cart_summary.html` | `hx-put`, `hx-trigger="change"`, `hx-delete`, `hx-confirm`, `hx-target="#cart-container"`, `hx-indicator` |
| `_checkout_form.html`, `_form_field.html` | `hx-post`, `hx-target="this"`, `hx-swap="outerHTML"`, `hx-indicator`; shipping select: `hx-get`, `hx-trigger="change"`, `hx-target="#order-summary"` |
| `_manage_table.html`, `_manage_row.html` | `hx-get` (live search); `hx-post` + `hx-target="closest tr"` (stock, toggle); `hx-delete` + `hx-confirm` |
| `_product_form.html` | `hx-post`, `hx-encoding="multipart/form-data"`, `hx-target="this"`, `hx-swap="outerHTML"` |
| `_messages.html`, `_error.html` | `hx-swap-oob` for the messages area; inline 404 error |
