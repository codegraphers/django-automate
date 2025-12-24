# REST API Reference

The API is documented via OpenAPI/Swagger at `/api/schema/swagger-ui/`.

## Authentication
All API requests require:
`Authorization: Bearer <TOKEN>` or Session Cookie (if using Admin).

## Endpoints

### Workflows
*   `GET /api/automate/workflows/`
*   `POST /api/automate/workflows/`
*   `GET /api/automate/workflows/{id}/`

### Executions
*   `GET /api/automate/executions/`
*   `POST /api/automate/executions/{id}/replay/`

### Events
*   `POST /api/automate/webhooks/{source}/`
