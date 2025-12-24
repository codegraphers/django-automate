# Plugin System

We use Python `entry_points` to discover plugins.

## Configuration
In your `pyproject.toml` (if packaging your own plugins):

```toml
[project.entry-points."django_automate.connectors"]
my_erp = "my_app.adapters:MyERPAdapter"

[project.entry-points."django_automate.secrets.backends"]
vault = "my_app.secrets:HashiCorpVaultBackend"
```

## Registry Loading
On startup (`AppConfig.ready`), the registry scans these entry points and loads the classes.

## Available Extension Points
*   `django_automate.connectors`
*   `django_automate.secrets.backends`
*   `django_automate.llm.providers`
*   `django_automate.llm.renderers`
