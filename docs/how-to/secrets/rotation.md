# Rotating Secrets

Regularly rotating API keys is security best practice. Automate makes this zero-downtime.

## 1. Zero-Downtime Rotation (Env Backend)

1.  **Generate new key** in the external provider (e.g. Stripe).
2.  **Add new Env Var**: `export AUTOMATE_STRIPE_KEY_V2="sk_live_new..."`.
3.  **Update Workflow**: Change the `SecretRef` in your workflow definition:
    ```json
    { "$secret": "STRIPE_KEY_V2" }
    ```
4.  **Deploy/Publish**: The next run will uses V2.
5.  **Revoke Old Key**: Once all V1 workflows have finished.

## 2. Stored Secrets (DB Backend)
If using `EncryptedDBBackend`:
1.  Go to **Admin > Governance > Stored Secrets**.
2.  Find `STRIPE_KEY`.
3.  Click **Rotate Secret**.
4.  Paste the new value.
5.  **Save**.
    *   The `SecretRef` name (`STRIPE_KEY`) stays the same.
    *   All workflows use the new value immediately.
    *   No workflow edit required.
