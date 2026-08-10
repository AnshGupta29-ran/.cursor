# Category template: E-commerce / Inventory / Orders

Family shape for merchant operations: catalogs, stock, purchasing, and fulfillment.
Each run needs a concrete shop domain — not “Product A / Product B”.

## Product family intent

Staff manage products and stock levels, accept or enter customer orders, track
fulfillment states, and see operational signals (low stock, revenue snapshots).
Customer storefront is optional unless the seed requires it; admin/ops depth is mandatory.

## Identity & positioning (invent uniquely)

- Merchant type (bookstore, bike shop, cafe wholesale, electronics parts)
- Channel (admin-only ops console vs admin + simple storefront)
- Inventory philosophy (simple qty vs multi-warehouse lite)
- One twist (suppliers + POs, serial numbers, perishable lots, B2B price lists)

## Required capability areas

### Catalog
- Products with SKU, pricing, category, active flag
- Variants only if the domain needs them (state clearly)
- Media optional; prefer real fields over empty image URLs

### Inventory
- On-hand quantity adjustments with reason notes
- Low-stock threshold + alerts list/dashboard widget
- Prevent oversell policy stated (hard block vs backorder)

### Orders
- Create orders (manual admin and/or checkout)
- Line items, totals, status machine (e.g. pending → paid → packed → shipped → canceled)
- Customer identity fields appropriate to channel

### Suppliers / purchasing (include if seed suggests inventory platform)
- Supplier records
- Purchase orders that increase stock on receive

### Analytics lite
- Dashboard: counts, low stock, recent orders, simple revenue range

### Auth
- Admin authentication; role split if useful (clerk vs manager)

## UX expectations

- Dense but readable tables with pagination/filter
- Order detail page with status transitions
- Validation that prevents incomplete checkouts/orders
- Empty-state onboarding with seed catalog

## Data & persistence

Entities often include: User, Product, Category, InventoryLedger, Customer, Order,
OrderItem, Supplier, PurchaseOrder.
Use relational DB + ORM suitable to stack; migrations documented.

## Quality & reliability

- Backend tests for stock decrement, low-stock detection, unauthorized access
- Transactional integrity on order placement when stock changes
- Clear API validation errors

## Documentation & deliverables

- README with seed SKUs and a sample order path
- Status machine diagram or bullet list
- How to reset demo data

## Constraints & non-goals

- Not a full Shopify replacement
- Not payment-provider certification; mock/pay-stub OK if labeled
- Avoid fake analytics with random numbers unrelated to orders

## Acceptance criteria checklist (customize)

- [ ] Products and stock can be managed end-to-end
- [ ] Placing an order updates inventory per policy
- [ ] Low-stock alerts appear when thresholds crossed
- [ ] Order statuses transition with validation
- [ ] Auth protects admin mutations
- [ ] Critical endpoint tests pass
- [ ] Local demo is reproducible from README

## Variation axes

B2B vs B2C · storefront presence · lots/serials · multi-location · returns · tax/shipping
simplicity · supplier depth

## Anti-clone rules

Change merchant domain, status names, and ops workflows each run. Ban identical
“React Prisma inventory boilerplate” prose.
