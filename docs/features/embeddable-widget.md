# Embeddable Chat Widget

Embed the Data Chat widget on external websites with full security controls.

## Overview

The embeddable widget allows you to add AI-powered data chat to any website. Features include:

- **Domain Whitelisting**: Only allowed domains can embed
- **API Key Authentication**: Secure per-embed keys
- **Rate Limiting**: Prevent abuse
- **Theme Customization**: Match your brand

## Creating an Embed

### Via Admin UI

1. Go to Admin → Automate Datachat → Chat Embeds
2. Click "Add Chat Embed"
3. Configure:
   - **Name**: Internal identifier
   - **Allowed Domains**: JSON array of domains
   - **Rate Limiting**: Requests per minute
   - **Theme**: Colors and title
   - **Welcome Message**: Initial greeting

### Programmatically

```python
from automate_datachat.models import ChatEmbed

embed = ChatEmbed.objects.create(
    name="Marketing Site Widget",
    allowed_domains=["example.com", "*.example.com"],
    rate_limit_per_minute=10,
    theme={
        "primaryColor": "#4F46E5",
        "title": "Ask Our Data"
    },
    welcome_message="Hi! Ask me anything about our products."
)

print(embed.api_key)  # Auto-generated: dce_xxxxx...
```

## Embed Code

After creating an embed, copy the generated code:

```html
<script 
  src="https://yoursite.com/datachat/embed/v1/<embed-id>/widget.js" 
  data-key="dce_YOUR_API_KEY">
</script>
```

The widget will appear as a floating chat button in the bottom-right corner.

## Security Features

### Domain Whitelisting

Specify which domains can embed the widget:

```json
["example.com", "app.example.com", "*.staging.example.com"]
```

Wildcards are supported:
- `*.example.com` - All subdomains
- `example.com` - Exact match only

### API Key Authentication

Each embed has a unique API key (auto-generated):

```
dce_a1b2c3d4e5f6g7h8i9j0...
```

The widget passes this in the `X-Embed-Key` header.

### Rate Limiting

Prevent abuse with per-session limits:

| Setting | Description |
|---------|-------------|
| `rate_limit_per_minute` | Max requests per minute per session |
| `max_queries_per_session` | Total queries allowed per session |

### Table Restrictions

Limit which tables can be queried:

```json
["products", "categories"]
```

Empty array = all tables allowed.

## Theme Customization

Customize the widget appearance:

```json
{
    "primaryColor": "#2563EB",
    "title": "Data Assistant"
}
```

| Property | Description | Default |
|----------|-------------|---------|
| `primaryColor` | Button and header color | `#2563EB` |
| `title` | Widget header title | "Data Assistant" |

## API Endpoints

The embed widget uses these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/datachat/embed/v1/<id>/widget.js` | GET | Widget JavaScript |
| `/datachat/embed/v1/<id>/chat` | POST | Send message |
| `/datachat/embed/v1/<id>/config` | GET | Get embed config |

### Chat API

**Request:**
```bash
curl -X POST https://yoursite.com/datachat/embed/v1/<id>/chat \
  -H "Content-Type: application/json" \
  -H "X-Embed-Key: dce_xxxxx" \
  -d '{"question": "How many products are there?"}'
```

**Response:**
```json
{
    "answer": "There are 42 products in the database.",
    "sql": "SELECT COUNT(*) FROM products",
    "error": null
}
```

## Error Responses

| Status | Error | Description |
|--------|-------|-------------|
| 401 | "Invalid API key" | Wrong or missing key |
| 403 | "Domain not allowed" | Origin not whitelisted |
| 404 | "Embed not found" | Invalid embed ID |
| 429 | "Rate limit exceeded" | Too many requests |

## Integration Examples

### React

```jsx
import { useEffect } from 'react';

function ChatWidget() {
    useEffect(() => {
        const script = document.createElement('script');
        script.src = 'https://yoursite.com/datachat/embed/v1/<id>/widget.js';
        script.setAttribute('data-key', 'dce_xxxxx');
        document.body.appendChild(script);
        
        return () => script.remove();
    }, []);
    
    return null;
}
```

### Vue

```vue
<script setup>
import { onMounted, onUnmounted } from 'vue';

onMounted(() => {
    const script = document.createElement('script');
    script.src = 'https://yoursite.com/datachat/embed/v1/<id>/widget.js';
    script.setAttribute('data-key', 'dce_xxxxx');
    document.body.appendChild(script);
});
</script>
```

### Static HTML

```html
<!DOCTYPE html>
<html>
<body>
    <h1>My Website</h1>
    
    <script 
        src="https://yoursite.com/datachat/embed/v1/<id>/widget.js" 
        data-key="dce_xxxxx">
    </script>
</body>
</html>
```
