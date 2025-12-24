from abc import ABC, abstractmethod
from typing import Dict, Any

class MetricsCollector(ABC):
    @abstractmethod
    def increment(self, metric: str, tags: Dict[str, str] = None, value: float = 1.0):
        pass

    @abstractmethod
    def timing(self, metric: str, duration_ms: float, tags: Dict[str, str] = None):
        pass

    @abstractmethod
    def gauge(self, metric: str, value: float, tags: Dict[str, str] = None):
        pass

class NoOpCollector(MetricsCollector):
    def increment(self, metric, tags=None, value=1.0): pass
    def timing(self, metric, duration_ms, tags=None): pass
    def gauge(self, metric, value, tags=None): pass
