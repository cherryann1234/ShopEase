# Screenshot & Recording Guide

Setup: run the server (`python manage.py runserver`), open http://127.0.0.1:8000/. Use a window ~1200 px wide for desktop shots.
Paste each screenshot in your Word file (`LastName_LastName.docx`) under a heading + one-line caption, and add your public GitHub link on the first page.

| # | Do this | Capture |
| --- | --- | --- |
| 1 | Open `/` | Catalog with grid, result count, In/Low/Out of Stock badges, cart badge |
| 2 | Type `mouse` in search (wait 0.3 s, no reload) | Filtered grid + updated count |
| 3 | Clear it, pick a category, sort "Price: low to high" | Filtered/sorted grid |
| 4 | Search `zzzz` | Empty-list message |
| 5 | Clear search, click page 2 | Pagination (URL changes, no full reload) |
| 6 | Click "Add to Cart" on a card | Inline confirmation + badge number going up |
| 7 | Open a product → quantity `999` → Add to Cart | Stock validation error |
| 8 | Same page, quantity `1` → Add to Cart | Success message |
| 9 | Go to `/products/9999/` | Custom 404 page |
| 10 | Open `/manage/products/` | Management table, search box, Add/Edit/Delete buttons |
| 11 | Change a row's stock to `-5` and tab out | Inline stock error |
| 12 | Click a status pill | Row flips Active/Inactive without reload |
| 13 | Add Product → leave name empty, price `0`, stock `-1` → Save | **Failed validation #1**: field errors, preserved input |
| 14 | Fix values, choose a category, Save | Success message on the list |
| 15 | Edit a product | Edit form pre-filled |
| 16 | Click Delete | Browser confirm dialog, then screenshot the list with the success message |
| 17 | Go to `/cart/` with 2-3 items | Cart table, summary (subtotal/shipping/total) |
| 18 | Change a quantity; then enter more than the stock | Summary recalculates; stock error |
| 19 | Remove an item (confirm), then remove all | Empty-cart message, no Checkout button |
| 20 | Add items again → Proceed to Checkout | Checkout page |
| 21 | Name `Juan`, email `abc`, phone `12345`, Express, empty address → Place Order | **Failed validation #2**: errors beside fields + non-field error on top, input kept |
| 22 | Change shipping method Standard → Express → Pickup | Order summary total changing (shoot two states) |
| 23 | Fill valid data (phone `09171234567`) → Place Order | Order confirmation with order number |
| 24 | DevTools (F12) → device toolbar (Ctrl+Shift+M) → 360 px | Catalog, open hamburger menu, cart as stacked cards |
| 25 | DevTools → Network → throttle "Slow 3G", search in catalog | Loading spinner; optionally the request showing header `HX-Request: true` |

**Screen recording (3-4 min):** catalog (search/filter/add to cart) → manage products (failed form, then success, delete) → cart (quantity change, remove) → checkout (failed form, shipping change, success).
