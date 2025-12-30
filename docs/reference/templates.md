# Templates Reference

Complete reference for Django Automate templates.

## Table of Contents

1. [Template Structure](#template-structure)
2. [Base Templates](#base-templates)
3. [Admin Templates](#admin-templates)
4. [Studio Templates](#studio-templates)
5. [Override Guide](#override-guide)

---

## Template Structure

```
src/
├── automate/templates/admin/
│   ├── automate/automation/change_list.html
│   ├── automate/prompt_eval.html
│   └── index.html
├── automate_datachat/templates/admin/
│   └── base_site.html
├── automate_modal/templates/admin/
│   └── automate_modal/endpoint/test_console.html
├── automate_studio/templates/
│   ├── admin/automate/studio/{explorer,tester,wizard}.html
│   ├── admin/index.html
│   └── studio/{base,dashboard,correlation,provider_test}.html
└── rag/templates/admin/
    └── rag/ragendpoint/test_query.html
```

---

## Base Templates

### base_site.html

**Location:** `automate_datachat/templates/admin/base_site.html`

Site-wide admin customization.

**Blocks:**

| Block | Purpose |
|-------|---------|
| `{% block title %}` | Page title |
| `{% block branding %}` | Logo/site name |
| `{% block nav-global %}` | Navigation menu |
| `{% block userlinks %}` | User menu |
| `{% block extrastyle %}` | Additional CSS |

**Override:**
```html
<!-- your_app/templates/admin/base_site.html -->
{% extends "admin/base_site.html" %}

{% block branding %}
<h1 id="site-name">My Custom Admin</h1>
{% endblock %}

{% block extrastyle %}
{{ block.super }}
<style>
    #header { background: #2c3e50; }
</style>
{% endblock %}
```

---

### studio/base.html

**Location:** `automate_studio/templates/studio/base.html`

Base layout for Studio views.

**Blocks:**

| Block | Purpose |
|-------|---------|
| `{% block title %}` | Page title |
| `{% block extra_head %}` | Additional head content |
| `{% block content %}` | Main content |
| `{% block sidebar %}` | Sidebar content |
| `{% block footer %}` | Footer content |
| `{% block extra_js %}` | Additional JavaScript |
| `{% block extra_css %}` | Additional CSS |

**Override:**
```html
{% extends "studio/base.html" %}

{% block extra_css %}
{{ block.super }}
<link rel="stylesheet" href="{% static 'css/custom.css' %}">
{% endblock %}

{% block content %}
<div class="my-custom-layout">
    {{ block.super }}
</div>
{% endblock %}
```

---

## Admin Templates

### automation/change_list.html

**Location:** `automate/templates/admin/automate/automation/change_list.html`

Custom automation list view.

**Blocks:**

| Block | Purpose |
|-------|---------|
| `{% block result_list %}` | The table of records |
| `{% block search %}` | Search form |
| `{% block pagination %}` | Pagination controls |

---

### prompt_eval.html

**Location:** `automate/templates/admin/automate/prompt_eval.html`

Prompt evaluation interface.

**Blocks:**

| Block | Purpose |
|-------|---------|
| `{% block content %}` | Main evaluation form |
| `{% block scripts %}` | JavaScript for evaluation |

---

### endpoint/test_console.html

**Location:** `automate_modal/templates/admin/automate_modal/endpoint/test_console.html`

Modal endpoint test console.

**Blocks:**

| Block | Purpose |
|-------|---------|
| `{% block content %}` | Console interface |
| `{% block scripts %}` | Console JavaScript |

---

### ragendpoint/test_query.html

**Location:** `rag/templates/admin/rag/ragendpoint/test_query.html`

RAG endpoint query tester.

**Blocks:**

| Block | Purpose |
|-------|---------|
| `{% block content %}` | Query form |
| `{% block results %}` | Results display |

---

## Studio Templates

### dashboard.html

**Location:** `automate_studio/templates/studio/dashboard.html`

Main studio dashboard.

**Variables:**

| Variable | Type | Description |
|----------|------|-------------|
| `automations` | QuerySet | Active automations |
| `executions_today` | int | Execution count |
| `error_rate` | float | Error percentage |
| `charts` | dict | Chart configurations |

---

### correlation.html

**Location:** `automate_studio/templates/studio/correlation.html`

Event correlation explorer.

**Variables:**

| Variable | Type | Description |
|----------|------|-------------|
| `correlations` | list | Correlation data |
| `time_range` | tuple | (start, end) dates |

---

### explorer.html

**Location:** `automate_studio/templates/admin/automate/studio/explorer.html`

Execution explorer interface.

---

### tester.html

**Location:** `automate_studio/templates/admin/automate/studio/tester.html`

Rule tester interface.

---

### wizard.html

**Location:** `automate_studio/templates/admin/automate/studio/wizard.html`

Automation creation wizard.

---

## Override Guide

### Method 1: Copy to Project Templates

1. Create `templates/admin/` in your project
2. Copy the template you want to override
3. Modify as needed

```python
# settings.py
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Your project templates first
        ...
    }
]
```

```
your_project/
├── templates/
│   └── admin/
│       └── base_site.html  # Your override
└── settings.py
```

---

### Method 2: Template Setting on Admin

```python
@admin.register(MyModel)
class MyModelAdmin(BaseModelAdmin):
    change_form_template = 'admin/myapp/mymodel/change_form.html'
    change_list_template = 'admin/myapp/mymodel/change_list.html'
```

---

### Method 3: Template Setting on View

```python
class MyDashboardView(TemplateView):
    template_name = 'myapp/dashboard.html'
```

```python
# urls.py
from automate_studio.views import DashboardView

class CustomDashboardView(DashboardView):
    template_name = 'custom/dashboard.html'

urlpatterns = [
    path('dashboard/', CustomDashboardView.as_view()),
]
```

---

### Custom Admin Index

```html
<!-- templates/admin/index.html -->
{% extends "admin/index.html" %}

{% block content %}
<div class="custom-welcome">
    <h2>Welcome to {{ site_header }}</h2>
</div>
{{ block.super }}
{% endblock %}

{% block sidebar %}
{{ block.super }}
<div class="custom-sidebar">
    <h3>Quick Links</h3>
    <ul>
        <li><a href="/admin/automate/automation/">Automations</a></li>
        <li><a href="/studio/dashboard/">Studio Dashboard</a></li>
    </ul>
</div>
{% endblock %}
```

---

### Custom Change Form

```html
<!-- templates/admin/automate/automation/change_form.html -->
{% extends "admin/change_form.html" %}

{% block after_field_sets %}
<div class="module">
    <h2>Workflow Preview</h2>
    <div id="workflow-canvas"></div>
</div>
{% endblock %}

{% block admin_change_form_document_ready %}
{{ block.super }}
<script>
    // Initialize workflow preview
    initWorkflowPreview('{{ original.id }}');
</script>
{% endblock %}
```

---

### Template Tags

```python
# templatetags/automate_tags.py
from django import template

register = template.Library()

@register.simple_tag
def automation_count():
    from automate_core.workflows.models import Automation
    return Automation.objects.filter(enabled=True).count()

@register.inclusion_tag('components/status_badge.html')
def status_badge(status):
    return {'status': status}
```

```html
{% load automate_tags %}

<p>Active automations: {% automation_count %}</p>
{% status_badge execution.status %}
```

---

## Component Templates

### includes/header.html

Reusable header component.

```html
{% include "studio/includes/header.html" with title="My Page" %}
```

### components/test_result.html

Test result display component.

```html
{% include "studio/components/test_result.html" with result=test_result %}
```

---

## Settings

```python
# settings.py

# Template directories (project templates override package templates)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Project templates
        ],
        'APP_DIRS': True,  # Allows app templates
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processor
                'automate.context_processors.automate_context',
            ],
        },
    },
]
```
