from automate_datachat.sqlpolicy import SQLPolicy

try:
    policy = SQLPolicy(allowed_tables=["auth_user"], max_rows=1000)
    sql = "SELECT * FROM auth_user LIMIT 5"
    print(f"Testing SQL: {sql}")
    res = policy.validate_and_optimize(sql)
    print(f"Result: {res}")
except Exception as e:
    print(f"ERROR: {e}")
