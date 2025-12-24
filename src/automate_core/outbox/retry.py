import random
from datetime import timedelta

def calculate_backoff(attempt: int, max_delay: int = 300, jitter_pct: float = 0.2) -> timedelta:
    """
    Exponential backoff with jitter.
    delay = min(2^attempt, max_delay)
    """
    delay = min(2**attempt, max_delay)
    
    # Apply jitter: +/- jitter_pct
    # e.g. if delay=10, jitter=0.2 -> 8..12
    if jitter_pct > 0:
        spread = delay * jitter_pct
        delay += random.uniform(-spread, spread)
        
    # Ensure non-negative
    delay = max(1, delay)
    return timedelta(seconds=delay)
