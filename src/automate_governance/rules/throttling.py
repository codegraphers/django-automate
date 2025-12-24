from __future__ import annotations

from django.db import models, transaction
from django.utils import timezone


class ThrottleBucket(models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    tokens = models.FloatField(default=0.0)
    last_refill = models.DateTimeField(auto_now_add=True)

class ThrottleStore:
    """
    Token bucket implementation using DB atomic upserts.
    """

    def consume(self, key: str, capacity: int, refill_rate_per_sec: float, cost: int = 1) -> bool:
        now = timezone.now()

        # Postgres UPSERT or Atomic Transaction
        with transaction.atomic():
            # Select for update to lock the bucket
            bucket, created = ThrottleBucket.objects.select_for_update().get_or_create(
                key=key,
                defaults={"tokens": capacity, "last_refill": now}
            )

            if created:
                # new bucket starts full
                if capacity >= cost:
                    bucket.tokens = capacity - cost
                    bucket.save()
                    return True
                return False

            # Refill
            elapsed = (now - bucket.last_refill).total_seconds()
            added = elapsed * refill_rate_per_sec
            new_tokens = min(capacity, bucket.tokens + added)

            if new_tokens >= cost:
                bucket.tokens = new_tokens - cost
                bucket.last_refill = now
                bucket.save()
                return True
            else:
                # Update refill time/tokens even on failure?
                # Ideally yes to capture passive refill, but strictly not needed for logic correctness
                # if we always recalc from last_refill. But we should save to avoid drift logic issues.
                bucket.tokens = new_tokens
                bucket.last_refill = now
                bucket.save()
                return False
