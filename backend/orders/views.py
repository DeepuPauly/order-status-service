import json

from django.db import IntegrityError, transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Event, Order

# Conflict rule: when two sources report DIFFERENT statuses at the SAME
# timestamp, the payment processor wins over the trading platform, because
# payment state is the money-truth. Higher number = higher priority.
SOURCE_PRIORITY = {"payment_processor": 2, "trading_platform": 1}


@csrf_exempt
@require_POST
def ingest(request):
    try:
        payload = json.loads(request.body)
        order_id = payload["order_id"]
        status = payload["status"]
        source = payload["source"]
        # Reject bad fields up front with a 400. Otherwise a null status fails
        # the NOT NULL constraint, gets mistaken for a duplicate, and ends in a 500.
        if not (_valid_str(order_id, 255) and _valid_str(status, 50)):
            raise ValueError("order_id and status must be non-empty strings")
        if source not in SOURCE_PRIORITY:
            raise ValueError("unknown source")
        ts = parse_datetime(payload["event_timestamp"])
        if ts is None:
            raise ValueError("bad event_timestamp")
        if timezone.is_naive(ts):
            ts = timezone.make_aware(ts)
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return HttpResponseBadRequest("invalid payload")

    # Step 1: record the raw event. If it's an exact duplicate, the unique
    # constraint rejects it and we simply note that it was a duplicate.
    duplicate = _record_raw_event(order_id, status, ts, source)

    # Step 2: update the authoritative status. We ALWAYS run this, even for a
    # duplicate, because re-applying the same event is a no-op and this makes
    # retries self-healing (if a crash happened between step 1 and 2 last time).
    _apply_authoritative(order_id, status, ts, source)

    return JsonResponse({"ok": True, "duplicate": duplicate})


def _record_raw_event(order_id, status, ts, source):
    try:
        # Wrapped in its own atomic block so that a duplicate (IntegrityError)
        # only rolls back THIS insert. When there is an outer transaction
        # (TestCase, or ATOMIC_REQUESTS) this becomes a savepoint and keeps
        # that transaction usable instead of raising TransactionManagementError.
        with transaction.atomic():
            Event.objects.create(
                order_id=order_id, status=status, event_timestamp=ts, source=source
            )
        return False
    except IntegrityError:
        return True  # exact same event already stored -> duplicate delivery


def _apply_authoritative(order_id, status, ts, source):
    with transaction.atomic():
        # Lock this order's row so two events for the same order can't clobber
        # each other (prevents lost updates under concurrency).
        order = Order.objects.select_for_update().filter(pk=order_id).first()

        if order is None:
            try:
                # Savepoint again: if a concurrent request created this order
                # first, only this insert rolls back and we recover below.
                with transaction.atomic():
                    Order.objects.create(
                        order_id=order_id,
                        status=status,
                        status_event_timestamp=ts,
                        last_source=source,
                    )
                return
            except IntegrityError:
                order = Order.objects.select_for_update().get(pk=order_id)

        if _should_replace(order, ts, source):
            order.status = status
            order.status_event_timestamp = ts
            order.last_source = source
            order.save()


def _valid_str(value, max_length):
    return isinstance(value, str) and 0 < len(value) <= max_length


def _should_replace(order, ts, source):
    """Decide whether an incoming event should become the new truth."""
    if ts > order.status_event_timestamp:
        return True   # newer event always wins
    if ts < order.status_event_timestamp:
        return False  # older event never overwrites (out-of-order safety)
    # Same timestamp -> higher-priority source wins. Same source with a
    # different status at the same timestamp: first arrival is kept (would
    # need an upstream event ID / sequence number to do better).
    return SOURCE_PRIORITY[source] > SOURCE_PRIORITY.get(order.last_source, 0)


def order_list(request):
    orders = Order.objects.all().order_by("order_id")
    return JsonResponse({"orders": [_serialize(o) for o in orders]})


def order_detail(request, order_id):
    order = Order.objects.filter(pk=order_id).first()
    if order is None:
        return JsonResponse({"error": "not found"}, status=404)
    return JsonResponse(_serialize(order))


def _serialize(o):
    return {
        "order_id": o.order_id,
        "status": o.status,
        "last_source": o.last_source,
        "status_event_timestamp": o.status_event_timestamp.isoformat(),
        "updated_at": o.updated_at.isoformat(),
    }