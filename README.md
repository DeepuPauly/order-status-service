# Order Status Service

A small full-stack application that receives order-state events from two independent upstream systems (a payment processor and a trading platform), stores every event, and maintains one authoritative current status per order.

The backend is built with Django, and the frontend is built with Next.js.

---

# Running the Project

## Backend

```bash
cd backend
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Start the server:

```bash
python manage.py runserver
```

---

## Frontend

Open another terminal.

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at:

```
http://localhost:3000
```

---

## Seed Sample Data

With the backend running:

```bash
cd backend
python seed.py
```

The seed data is intentionally designed to demonstrate the required edge cases:

- **A1** receives a duplicate webhook delivery.
- **B2** receives an older event after a newer one.
- **C3** receives conflicting events from different sources.

This allows the UI to immediately show how each case is resolved.

---

# Running Tests

```bash
cd backend
python manage.py test
```

---

# API Endpoints

### POST `/api/ingest/`

Receives a single order event.

```json
{
  "order_id": "A1",
  "status": "paid",
  "event_timestamp": "2026-07-15T10:30:00Z",
  "source": "payment_processor"
}
```

Valid `source` values are `payment_processor` and `trading_platform`.

---

### GET `/api/orders/`

Returns all orders with their current authoritative status.

---

### GET `/api/orders/<order_id>/`

Returns a single order including:

- `status` — the current authoritative status
- `last_source` — which system last set the status
- `status_event_timestamp` — the event time that produced it

---

# Design Decisions

## 1. Duplicate Webhook Deliveries

Webhook senders retry whenever they receive a non-200 response, so duplicate deliveries are expected.

To make ingestion idempotent, the event table has a unique constraint on:

```
(order_id, source, event_timestamp, status)
```

If the same event arrives again, the database rejects the duplicate, it is ignored, and the endpoint still returns **HTTP 200**.

I chose to let the database enforce uniqueness instead of checking in Python first because application-level existence checks are vulnerable to race conditions.

---

## 2. Out-of-Order Events

Network delivery order cannot be trusted.

Each order stores the timestamp that produced its current status.

When a new event arrives:

- If its timestamp is newer, it becomes the current state.
- If its timestamp is older, it is still stored in the event log but does not replace the current status.

This ensures the authoritative state is always based on event time rather than arrival order.

---

## 3. Conflicting Sources

The payment processor and trading platform may temporarily disagree.

The resolution rule is explicit:

- The newest event timestamp always wins.
- If both events have exactly the same timestamp, the payment processor takes priority over the trading platform.

The reasoning is that payment represents the financial source of truth, while the trading platform may briefly lag behind.

The rule is implemented in a single `_should_replace()` function so the behavior is easy to understand and modify.

Any source not listed in `SOURCE_PRIORITY` is rejected with **400 Bad Request**. New sources must be added to `SOURCE_PRIORITY` explicitly.

Known gap: if the **same** source sends two different statuses with exactly the same timestamp, the first one to arrive is kept. Resolving that properly would need an upstream event ID or sequence number, which the payload does not include.

---

## Concurrency

Updates are wrapped inside a database transaction.

The order row is locked using `select_for_update()` before applying updates, so concurrent requests for the same order cannot overwrite each other. This is effective on PostgreSQL; on SQLite (used here) `select_for_update()` is a no-op and SQLite's own write serialization is what prevents lost updates.

---

# Testing

The project includes tests covering the scenarios most likely to fail:

- Duplicate webhook delivery does not create duplicate state.
- Older events never overwrite newer status.
- Later timestamps correctly replace earlier ones.
- Equal timestamps resolve using the defined source priority, in either arrival order.
- A payload with a missing or null field returns 400 and writes nothing.
- An unknown `source` returns 400 and writes nothing.
- Non-POST requests to the ingest endpoint return 405.

While implementing duplicate handling, I encountered an issue where an `IntegrityError` left the surrounding transaction unusable, causing a `TransactionManagementError`.

The fix was to isolate the insert inside its own savepoint so only the duplicate insert is rolled back while the rest of the transaction continues normally.

---

# Tradeoffs

### SQLite

SQLite was chosen to keep setup simple.

The application can be switched to PostgreSQL by changing the Django `DATABASES` configuration.

SQLite serializes writes, so `select_for_update()` has little practical effect here, but the code is ready for databases that support row-level locking.

---

### Plain Django Instead of DRF

I intentionally used plain Django views instead of Django REST Framework.

With only three endpoints, DRF would introduce unnecessary abstraction without solving any meaningful problem.

---

### Invalid Payloads

Malformed requests currently return **400 Bad Request**.

In a production webhook system, this could result in endless retries from the sender.

A better production approach would be to acknowledge the request with **200 OK**, record the failure, and send the event to a dead-letter queue for investigation.

I kept the implementation simple since that behavior is outside the scope of this exercise.

---

### Event History

Instead of storing only the latest order status, every incoming event is persisted.

This makes every state transition auditable and allows the current status to be reconstructed if needed, without implementing a complete event-sourcing framework.

---

### Authentication

The ingestion endpoint does not implement authentication.

A production version should verify webhook signatures or another trusted authentication mechanism before accepting events.

---

### Frontend

The Next.js pages are implemented as **Server Components**.

Data is fetched server-side, so no CORS configuration is required.

If the frontend fetched data directly from the browser, Django CORS middleware would need to be configured.

---

# Time Spent

Approximately **4 hours**.

Most of the time was spent implementing the event resolution logic, ensuring idempotent webhook processing, handling out-of-order events correctly, writing tests for the edge cases, and building a simple UI to display the current order state.