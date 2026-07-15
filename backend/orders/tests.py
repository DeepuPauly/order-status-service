import json

from django.test import TestCase

from .models import Event, Order


def post(client, order_id, status, ts, source):
    return client.post(
        "/api/ingest/",
        data=json.dumps(
            {
                "order_id": order_id,
                "status": status,
                "event_timestamp": ts,
                "source": source,
            }
        ),
        content_type="application/json",
    )


class IngestionTests(TestCase):
    def test_duplicate_delivery_is_a_noop(self):
        post(self.client, "A1", "paid", "2025-01-01T10:00:00Z", "payment_processor")
        post(self.client, "A1", "paid", "2025-01-01T10:00:00Z", "payment_processor")
        self.assertEqual(Event.objects.filter(order_id="A1").count(), 1)
        self.assertEqual(Order.objects.get(pk="A1").status, "paid")

    def test_out_of_order_old_event_does_not_overwrite(self):
        post(self.client, "B2", "shipped", "2025-01-01T12:00:00Z", "trading_platform")
        post(self.client, "B2", "processing", "2025-01-01T11:00:00Z", "payment_processor")
        order = Order.objects.get(pk="B2")
        self.assertEqual(order.status, "shipped")            # newer status kept
        self.assertEqual(Event.objects.filter(order_id="B2").count(), 2)  # both logged

    def test_conflict_resolved_by_latest_timestamp(self):
        post(self.client, "C3", "paid", "2025-01-01T09:00:00Z", "payment_processor")
        post(self.client, "C3", "pending", "2025-01-01T09:30:00Z", "trading_platform")
        order = Order.objects.get(pk="C3")
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.last_source, "trading_platform")

    def test_tie_on_timestamp_resolved_by_source_priority(self):
        # Same timestamp, insertion order shouldn't matter: payment wins.
        post(self.client, "D4", "pending", "2025-01-01T09:00:00Z", "trading_platform")
        post(self.client, "D4", "paid", "2025-01-01T09:00:00Z", "payment_processor")
        self.assertEqual(Order.objects.get(pk="D4").status, "paid")