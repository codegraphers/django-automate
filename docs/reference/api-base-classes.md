# API Base Classes Reference

Complete reference for Django Automate's base classes and mixins.

## Base Classes

### BaseAPIView

Base class for all API views.

```python
from automate_api.v1.base import BaseAPIView

class MyView(BaseAPIView):
    def get(self, request):
        return Response({'status': 'ok'})
```

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `authentication_classes` | list | `[BearerTokenAuthentication]` | Auth backends |
| `permission_classes` | list | `[IsAuthenticatedAndTenantScoped]` | Permission checks |
| `throttle_classes` | list | `[TenantRateThrottle, TokenRateThrottle]` | Rate limiting |

---

### BaseViewSet

Base class for ViewSet operations.

```python
from automate_api.v1.base import BaseViewSet

class MyViewSet(BaseViewSet):
    def list(self, request):
        return Response([])
```

**Inherits:** `ConfigurableMixin`, `TenantFilterMixin`

**Additional Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `pagination_class` | class | `CursorPagination` | Pagination handler |

---

### BaseModelViewSet

Base class for model CRUD operations.

```python
from automate_api.v1.base import BaseModelViewSet

class MyModelViewSet(BaseModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MySerializer
```

---

### BaseReadOnlyViewSet

Base class for read-only resources.

```python
from automate_api.v1.base import BaseReadOnlyViewSet

class AuditLogViewSet(BaseReadOnlyViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
```

---

## Mixins

### ConfigurableMixin

Provides Django settings integration.

```python
from automate_api.v1.base import ConfigurableMixin

class MyView(ConfigurableMixin, APIView):
    @classmethod
    def get_setting(cls, key, default=None):
        # Returns from AUTOMATE_API settings
        return super().get_setting(key, default)
```

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `get_setting` | `(key, default=None)` | Get setting from Django config |

---

### CORSMixin

Adds CORS header support.

```python
from automate_api.v1.base import CORSMixin

class MyView(CORSMixin, APIView):
    cors_allowed_origins = ['https://example.com']
```

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `cors_allowed_origins` | list | `['*']` | Allowed origins |
| `cors_allowed_methods` | list | `['GET', 'POST', ...]` | Allowed methods |
| `cors_allowed_headers` | list | `[...]` | Allowed headers |
| `cors_max_age` | int | `86400` | Preflight cache time |

**Methods:**

| Method | Description |
|--------|-------------|
| `add_cors_headers(response)` | Add CORS headers to response |
| `get_cors_allowed_origins()` | Get origins (checks settings) |
| `options(request)` | Handle preflight requests |

---

### TenantFilterMixin

Automatic tenant filtering for querysets.

```python
from automate_api.v1.base import TenantFilterMixin

class MyViewSet(TenantFilterMixin, ModelViewSet):
    tenant_field = 'organization_id'
```

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `tenant_field` | str | `'tenant_id'` | Field for filtering |

---

### RateLimitMixin

Custom rate limiting per request.

```python
from automate_api.v1.base import RateLimitMixin

class MyView(RateLimitMixin, APIView):
    rate_limit_per_minute = 30
    
    def post(self, request):
        if not self.check_rate_limit(request.user.id):
            return Response({'error': 'Rate limited'}, status=429)
```

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `rate_limit_key_prefix` | str | `'api_rate'` | Cache key prefix |
| `rate_limit_per_minute` | int | `60` | Requests/minute |

---

### StaffOnlyMixin

Restrict to staff users.

```python
from automate_api.v1.base import StaffOnlyMixin

class AdminViewSet(StaffOnlyMixin, BaseViewSet):
    pass
```

---

### PublicAPIMixin

Remove authentication for public endpoints.

```python
from automate_api.v1.base import PublicAPIMixin

class HealthView(PublicAPIMixin, BaseAPIView):
    def get(self, request):
        return Response({'healthy': True})
```

---

## Configuration

All mixins read from Django settings:

```python
# settings.py
AUTOMATE_API = {
    'CORS_ALLOWED_ORIGINS': ['https://example.com'],
    'RATE_LIMIT_PER_MINUTE': 120,
}
```

Mixins check settings first, fall back to class attributes:

```python
def get_cors_allowed_origins(self):
    return get_api_setting('CORS_ALLOWED_ORIGINS', self.cors_allowed_origins)
```
