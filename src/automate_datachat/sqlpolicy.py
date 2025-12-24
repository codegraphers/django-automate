import sqlglot
from sqlglot import exp


class SQLPolicyException(Exception):
    pass


class SQLPolicy:
    def __init__(self, allowed_tables: list[str], max_rows: int = 1000):
        self.allowed_tables = set(allowed_tables)
        self.max_rows = max_rows

    def validate_and_optimize(self, sql: str) -> str:
        """
        Parses SQL, enforces readonly policy, table allowlist, and injects LIMIT.
        Returns the optimized SQL.
        """
        try:
            expression = sqlglot.parse_one(sql)
        except Exception as e:
            raise SQLPolicyException(f"Invalid SQL syntax: {str(e)}")

        # 1. Enforce SELECT only
        if not isinstance(expression, exp.Select):
            raise SQLPolicyException("Only SELECT statements are allowed.")

        # 2. Validate Tables
        for table in expression.find_all(exp.Table):
            if table.name not in self.allowed_tables:
                raise SQLPolicyException(f"Access denied to table: {table.name}")

        # 3. Enforce LIMIT
        limit_node = expression.args.get("limit")
        should_enforce_max = False

        if not limit_node:
            should_enforce_max = True
        else:
            # Check if existing limit exceeds max
            try:
                # limit_node.this is usually a Literal expression for the number
                limit_val_expr = limit_node.this

                # Check if it's a simple number literal
                if isinstance(limit_val_expr, exp.Literal) and limit_val_expr.is_int:
                    current_limit = int(limit_val_expr.this)
                    if current_limit > self.max_rows:
                        should_enforce_max = True
                else:
                    # Complex limit (e.g. ALL or expression) -> overwrite for safety
                    should_enforce_max = True
            except Exception:
                # Fallback -> overwrite
                should_enforce_max = True

        if should_enforce_max:
            # Use the builder API which handles replacement correctly
            expression = expression.limit(self.max_rows)

        return expression.sql()
