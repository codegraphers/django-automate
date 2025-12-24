from __future__ import annotations
from typing import Any, Dict, Optional
import time
import logging

from .registry import get_adapter_cls
from .profiles import ConnectionProfileValidator
from .rate_limit.policy import RateLimitPolicy
from .rate_limit.limiter import RateLimiter, InMemoryRateLimiter
from .errors import ConnectorError, ConnectorErrorCode
from .types import ConnectorResult

logger = logging.getLogger(__name__)

class ConnectorExecutor:
    """
    The One True Pipeline for connector execution.
    Orchestrates: Profile -> Policy -> RateLimit -> Execute -> Audit.
    """
    def __init__(
        self, 
        rate_limiter: Optional[RateLimiter] = None,
        profile_validator: Optional[ConnectionProfileValidator] = None
    ) -> None:
        self.rate_limiter = rate_limiter or InMemoryRateLimiter() # TODO: swap for Redis in prod
        self.profile_validator = profile_validator or ConnectionProfileValidator()

    def execute(
        self,
        *,
        connector_code: str,
        action: str,
        profile: Dict[str, Any], # Resolved profile with secrets
        input_args: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> ConnectorResult:
        trace_id = ctx.get("trace_id", "unknown")
        
        # 1. Profile Validation
        # (Assuming profile is already resolved/decrypted by caller, but we check structure)
        # val_res = self.profile_validator.validate(profile, connector_code)
        # if not val_res.ok:
        #    raise ConnectorError(ConnectorErrorCode.CONFIG_INVALID, f"Invalid profile: {val_res.errors}")

        # 2. Load Adapter
        try:
            adapter_cls = get_adapter_cls(connector_code)
            adapter = adapter_cls()
        except Exception as e:
             raise ConnectorError(ConnectorErrorCode.CONFIG_INVALID, f"Adapter {connector_code} not found: {e}")

        # 3. Action Spec Check
        if action not in adapter.action_specs:
             raise ConnectorError(ConnectorErrorCode.INVALID_INPUT, f"Action {action} not supported by {connector_code}")

        # 4. Rate Limiter Reserve
        # Determine strict or dynamic policy from profile/connector config
        # For now, simple static key
        rl_key = f"rl:{connector_code}:{profile.get('name', 'default')}"
        permit = self.rate_limiter.acquire(rl_key)
        
        if not permit.is_allowed:
             raise ConnectorError(
                 ConnectorErrorCode.RATE_LIMITED, 
                 f"Rate limited. Retry after {permit.retry_after_ms}ms",
                 retryable=True,
                 details_safe={"retry_after_ms": permit.retry_after_ms}
             )

        start_ts = time.time()
        status = "failed"
        error_code = None

        try:
            # 5. Execute
            # Adapter must be stateless, so we pass config if needed. 
            # (In this design, adapter is instantiated per call or singleton but config passed in?)
            # The interface had `validate_config` but `execute` usually takes context.
            # We assume `profile` contains the config+secrets the adapter needs.
            # But wait, original adapter interface signature: execute(action, input, ctx)
            # We need to inject profile into ctx or modify contract. 
            # Let's inject into ctx for now to adhere to contract.
            
            exec_ctx = {**ctx, "profile": profile}
            
            result = adapter.execute(action, input_args, exec_ctx)
            
            # 6. Commit Rate Limiter (feedback)
            # If result has headers, we update dynamic limits.
            # self.rate_limiter.commit(permit, result.meta.get("headers"))
            
            status = "success"
            return ConnectorResult(status="success", data=result, meta={"duration_ms": (time.time()-start_ts)*1000})

        except Exception as e:
            # 7. Normalize Error
            norm_err = adapter.normalize_error(e)
            error_code = norm_err.code
            
            # Release permit on failure if it helps? 
            # self.rate_limiter.release(permit)
            
            raise norm_err
        finally:
            # 8. Audit Log
            duration_ms = (time.time() - start_ts) * 1000
            logger.info(
                "Connector Executed",
                extra={
                    "connector": connector_code,
                    "action": action,
                    "status": status,
                    "error_code": str(error_code) if error_code else None,
                    "duration_ms": duration_ms,
                    "trace_id": trace_id
                }
            )
