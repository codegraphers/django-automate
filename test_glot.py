import sqlglot
from sqlglot import exp

sql = "SELECT * FROM auth_user LIMIT 5"
expression = sqlglot.parse_one(sql)

print(f"Original: {expression.sql()}")

limit = expression.args.get("limit")
print(f"Limit Arg Type: {type(limit)}")
if limit:
    print(f"Limit This Type: {type(limit.this)}")
    print(f"Limit This: {limit.this}")
    # Try accessing value
    try:
        print(f"Value via .this.this: {limit.this.this}")
    except Exception as e:
        print(f"Error accessing .this.this: {e}")

# Test Replacing
print("--- Replacing Limit with 1000 ---")
expression2 = expression.copy()
# Method A: Builder
expression2 = expression2.limit(1000)
print(f"Method A (builder): {expression2.sql()}")

# Method B: Set
print("--- Method B (set) ---")
expression3 = expression.copy()
expression3.set("limit", exp.Limit(this=exp.Literal.number(1000)))
print(f"Method B (set): {expression3.sql()}")
