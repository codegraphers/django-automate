from pydantic import BaseModel


# Secret Reference Type
# In config, this is stored as "ref://..." or "env://..."
# At runtime, it's resolved before reaching the provider, OR the provider resolves it.
# The user request says: "secrets are always SecretRef type, never raw string."
class SecretRef(BaseModel):
    ref: str  # The reference string, e.g. "env:OPENAI_API_KEY"

# Base for all artifacts references
class ArtifactRef(BaseModel):
    artifact_id: str
    urls: dict[str, str] | None = None # presigned urls if needed
