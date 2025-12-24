"""
Workflow API - Create and manage workflows from the canvas UI.
"""

import json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@staff_member_required
@require_http_methods(["POST"])
def create_workflow(request):
    """
    POST /api/automate/workflows/
    POST /api/automate/workflows/

    Create a new automation with a workflow from the canvas UI.

    Request body:
        {
            "name": "My Workflow",
            "graph": {
                "nodes": [...],
                "edges": [...]
            }
        }
    """
    try:
        from django.utils.text import slugify  # noqa: PLC0415

        from automate.models import Automation, TriggerSpec, Workflow  # noqa: PLC0415

        data = json.loads(request.body)
        name = data.get("name", "Untitled Workflow")
        graph = data.get("graph", {})

        # Create or get automation
        slug = slugify(name)
        counter = 1
        original_slug = slug
        while Automation.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

        automation = Automation.objects.create(name=name, slug=slug, enabled=True, environment="default")

        # Create trigger from first trigger node
        trigger_nodes = [n for n in graph.get("nodes", []) if n.get("type") == "trigger"]
        if trigger_nodes:
            trigger_node = trigger_nodes[0]
            trigger_config = trigger_node.get("config", {})

            trigger_type_map = {"webhook": "webhook", "schedule": "schedule", "db_change": "model_signal"}

            TriggerSpec.objects.create(
                automation=automation,
                type=trigger_type_map.get(trigger_config.get("event_type", "webhook"), "webhook"),
                config=trigger_config,
                enabled=True,
            )

            # Enforce DB Trigger if applicable
            if trigger_config.get("event_type") == "db_change" and trigger_config.get("table"):
                from django.core.management import call_command  # noqa: PLC0415

                try:
                    call_command("setup_db_trigger", trigger_config.get("table"))
                except Exception as e:
                    print(f"Warning: Failed to setup DB trigger: {e}")

        # Create workflow with all nodes (including non-trigger steps)
        step_nodes = [n for n in graph.get("nodes", []) if n.get("type") != "trigger"]

        workflow = Workflow.objects.create(
            automation=automation,
            version=1,
            graph={"nodes": step_nodes, "edges": graph.get("edges", []), "config": {"name": name}},
            is_live=True,
            created_by=request.user.username,
        )

        return JsonResponse(
            {
                "id": str(automation.id),
                "slug": automation.slug,
                "workflow_version": workflow.version,
                "message": f"Workflow '{name}' created successfully!",
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@staff_member_required
@require_http_methods(["GET", "PUT"])
def workflow_detail(request, id):
    """
    GET /api/automate/workflows/{id}/ - Retrieve a workflow.
    PUT /api/automate/workflows/{id}/ - Update a workflow.
    """
    from django.shortcuts import get_object_or_404  # noqa: PLC0415

    from automate.models import Automation, TriggerSpec, Workflow  # noqa: PLC0415

    automation = get_object_or_404(Automation, id=id)

    if request.method == "GET":
        workflow = automation.workflows.filter(is_live=True).last()
        if not workflow:
            return JsonResponse({"error": "No workflow found"}, status=404)

        return JsonResponse(
            {
                "id": str(automation.id),
                "name": automation.name,
                "slug": automation.slug,
                "graph": workflow.graph.get("graph", workflow.graph),  # Handle nested or flat graph
            }
        )

    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            graph = data.get("graph", {})
            name = data.get("name", automation.name)

            # Update Automation
            if name != automation.name:
                automation.name = name
                # Keep slug stable or explicit update only? Let's keep slug stable for now.
                automation.save()

            # Update Trigger
            trigger_nodes = [n for n in graph.get("nodes", []) if n.get("type") == "trigger"]
            if trigger_nodes:
                trigger_config = trigger_nodes[0].get("config", {})
                trigger_type_map = {"webhook": "webhook", "schedule": "schedule", "db_change": "model_signal"}
                trig_type = trigger_type_map.get(trigger_config.get("event_type", "webhook"), "webhook")

                # Update existing triggers or clear and create?
                # For simplicity, let's update the first one or create new
                trigger = automation.triggers.first()
                if trigger:
                    trigger.type = trig_type
                    trigger.config = trigger_config
                    trigger.save()
                else:
                    TriggerSpec.objects.create(
                        automation=automation, type=trig_type, config=trigger_config, enabled=True
                    )

                # Enforce DB Trigger
                if trigger_config.get("event_type") == "db_change" and trigger_config.get("table"):
                    from django.core.management import call_command  # noqa: PLC0415

                    try:
                        call_command("setup_db_trigger", trigger_config.get("table"))
                    except Exception as e:
                        print(f"Warning: Failed to setup DB trigger: {e}")

            # Create NEW Workflow Version (Immutable history)
            step_nodes = [n for n in graph.get("nodes", []) if n.get("type") != "trigger"]
            current_version = automation.workflows.order_by("-version").first().version

            Workflow.objects.create(
                automation=automation,
                version=current_version + 1,
                graph={
                    "nodes": step_nodes,
                    "edges": graph.get("edges", []),
                    "config": {"name": name},
                    # We should probably store the FULL graph including trigger node visual for UI restoration
                    # But the 'executor' only needs steps.
                    # UI needs 'graph' as sent. Let's store that too.
                    # Wait, the lines above: `graph` in GET.
                    # If I store trimmed nodes in `graph`, UI loses trigger node visual.
                    # Solution: Store FULL graph in a UI-specific field or valid graph structure.
                    # Let's simple check: `graph` param in `Workflow` model is JSONField.
                    "ui_graph": graph,  # Store the raw UI graph for reloading
                },
                is_live=True,
                created_by=request.user.username,
            )

            return JsonResponse({"id": str(automation.id), "message": "Workflow updated successfully!"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
