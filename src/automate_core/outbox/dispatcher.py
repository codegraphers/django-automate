from __future__ import annotations
import logging
import traceback
from datetime import datetime, timedelta
from typing import Callable, Optional
from django.utils import timezone

from .store import OutboxStore
from .retry import calculate_backoff
from .throughput import ThroughputController

logger = logging.getLogger(__name__)

ProcessFn = Callable[[dict], None]


class Dispatcher:
    """
    Core execution loop:
    1. Claim batch from Store
    2. Check Backpressure
    3. Delegate execution to `process_fn`
    4. Handle Success/Retry/DLQ
    """

    def __init__(
        self, 
        store: OutboxStore, 
        process_fn: ProcessFn, 
        throughput: Optional[ThroughputController] = None,
        worker_id: str = "worker-1"
    ):
        self.store = store
        self.process_fn = process_fn
        self.throughput = throughput or ThroughputController()
        self.worker_id = worker_id

    def tick(self, limit: int = 50) -> int:
        now = timezone.now()
        
        # 1. Claim Batch
        items = self.store.claim_batch(owner=self.worker_id, limit=limit, now=now)
        if not items:
            return 0
            
        processed_count = 0
        for item in items:
            # 2. Check Backpressure (TODO: Optimize to check before claim or filter claim)
            # For now, we process claimed items.
            
            try:
                # 3. Process
                self.process_fn(item.payload)
                
                # 4a. Success
                self.store.mark_done(item.id, owner=self.worker_id)
                self.throughput.record_success(item.tenant_id)
                
            except Exception as e:
                # 4b. Error Handling
                logger.exception(f"Processing failed for item {item.id}")
                self.throughput.record_error(item.tenant_id)
                
                if item.attempt_count >= item.max_attempts:
                    self.store.mark_dlq(item.id, owner=self.worker_id, error_code="MAX_ATTEMPTS_EXCEEDED")
                else:
                    delay = calculate_backoff(item.attempt_count)
                    next_at = now + delay
                    error_code = type(e).__name__
                    self.store.mark_retry(
                        item.id, 
                        owner=self.worker_id, 
                        next_attempt_at=next_at, 
                        error_code=error_code
                    )
            
            processed_count += 1
            
        return processed_count
