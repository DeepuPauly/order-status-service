from django.db import models


class Event(models.Model):
    """
    The raw log of every event we receive. We never delete or overwrite here.
    The unique constraint is what makes duplicate webhook deliveries harmless:
    the exact same event can only ever be stored once.
    """
    order_id = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    event_timestamp = models.DateTimeField()
    source = models.CharField(max_length=50)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order_id", "source", "event_timestamp", "status"],
                name="uniq_event_dedup",
            )
        ]


class Order(models.Model):
    """
    The current authoritative status of one order. We keep the event_timestamp
    that produced this status, so a late-arriving OLD event can't overwrite a
    NEWER one. last_source tells the detail page which system last set it.
    """
    order_id = models.CharField(max_length=255, primary_key=True)
    status = models.CharField(max_length=50)
    status_event_timestamp = models.DateTimeField()
    last_source = models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)