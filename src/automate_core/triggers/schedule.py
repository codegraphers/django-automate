from __future__ import annotations

from datetime import datetime

# Note: In real impl, would use 'croniter' or similar library
# For skeleton, we stub the next_fire logic.

class ScheduleTriggerLogic:
    def get_next_fire_time(self, cron_expression: str, last_fired_at: datetime | None, now: datetime) -> datetime:
        """
        Compute next fire time based on cron expression.
        """
        # Stub implementation
        # import croniter
        # iter = croniter.croniter(cron_expression, now)
        # return iter.get_next(datetime)
        return now
