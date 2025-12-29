"""
Workflow Service Layer.

Business logic for workflow operations, extracted from views for reusability.

All service methods are designed to be:
- Testable in isolation
- Overridable via inheritance
- Configurable via class attributes
"""

from django.utils.text import slugify


class WorkflowService:
    """
    Service for workflow CRUD operations.
    
    Encapsulates business logic for creating and updating workflows,
    separated from HTTP concerns.
    
    Class Attributes:
        trigger_type_map: Mapping from UI trigger types to model types
        
    Example:
        service = WorkflowService()
        automation, workflow = service.create_workflow(
            name="My Workflow",
            graph={"nodes": [...], "edges": [...]},
            created_by="admin"
        )
    """
    
    trigger_type_map = {
        'webhook': 'webhook',
        'schedule': 'schedule',
        'db_change': 'model_signal',
    }
    
    def generate_unique_slug(self, name: str) -> str:
        """
        Generate a unique slug for the automation.
        
        Args:
            name: Human-readable name
            
        Returns:
            Unique slug string
        """
        from automate.models import Automation
        
        slug = slugify(name)
        original_slug = slug
        counter = 1
        
        while Automation.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        return slug
    
    def create_automation(self, name: str, slug: str) -> 'Automation':
        """
        Create a new automation.
        
        Args:
            name: Human-readable name
            slug: URL-safe identifier
            
        Returns:
            Created Automation instance
        """
        from automate.models import Automation
        
        return Automation.objects.create(
            name=name,
            slug=slug,
            enabled=True,
            environment='default'
        )
    
    def create_trigger(self, automation, trigger_config: dict):
        """
        Create a trigger for the automation.
        
        Args:
            automation: Automation instance
            trigger_config: Trigger configuration dict
        """
        from automate.models import TriggerSpec
        
        trigger_type = self.trigger_type_map.get(
            trigger_config.get('event_type', 'webhook'),
            'webhook'
        )
        
        TriggerSpec.objects.create(
            automation=automation,
            type=trigger_type,
            config=trigger_config,
            enabled=True
        )
        
        # Setup DB trigger if applicable
        if trigger_config.get('event_type') == 'db_change' and trigger_config.get('table'):
            self._setup_db_trigger(trigger_config.get('table'))
    
    def _setup_db_trigger(self, table: str):
        """Setup database trigger. Override for custom behavior."""
        from django.core.management import call_command
        
        try:
            call_command('setup_db_trigger', table)
        except Exception as e:
            # Log but don't fail
            import logging
            logging.getLogger(__name__).warning(f"Failed to setup DB trigger: {e}")
    
    def create_workflow_version(
        self, 
        automation, 
        graph: dict, 
        name: str, 
        created_by: str,
        version: int = 1
    ) -> 'Workflow':
        """
        Create a new workflow version.
        
        Args:
            automation: Parent automation
            graph: Complete workflow graph
            name: Workflow name
            created_by: Username of creator
            version: Version number
            
        Returns:
            Created Workflow instance
        """
        from automate.models import Workflow
        
        # Extract step nodes (non-trigger)
        step_nodes = [n for n in graph.get('nodes', []) if n.get('type') != 'trigger']
        
        return Workflow.objects.create(
            automation=automation,
            version=version,
            graph={
                'nodes': step_nodes,
                'edges': graph.get('edges', []),
                'config': {'name': name},
                'ui_graph': graph,  # Store full graph for UI
            },
            is_live=True,
            created_by=created_by
        )
    
    def create_workflow(self, name: str, graph: dict, created_by: str) -> tuple:
        """
        Create a complete workflow with automation and trigger.
        
        Args:
            name: Workflow name
            graph: Complete workflow graph
            created_by: Username of creator
            
        Returns:
            Tuple of (Automation, Workflow) instances
        """
        # Create automation
        slug = self.generate_unique_slug(name)
        automation = self.create_automation(name, slug)
        
        # Create trigger from first trigger node
        trigger_nodes = [n for n in graph.get('nodes', []) if n.get('type') == 'trigger']
        if trigger_nodes:
            trigger_config = trigger_nodes[0].get('config', {})
            self.create_trigger(automation, trigger_config)
        
        # Create workflow
        workflow = self.create_workflow_version(
            automation=automation,
            graph=graph,
            name=name,
            created_by=created_by,
            version=1
        )
        
        return automation, workflow
    
    def update_workflow(self, automation, graph: dict, name: str, created_by: str) -> 'Workflow':
        """
        Update workflow by creating a new version.
        
        Args:
            automation: Automation to update
            graph: Updated workflow graph
            name: Updated name (or existing)
            created_by: Username of updater
            
        Returns:
            New Workflow version
        """
        from automate.models import TriggerSpec
        
        # Update automation name if changed
        if name != automation.name:
            automation.name = name
            automation.save()
        
        # Update trigger
        trigger_nodes = [n for n in graph.get('nodes', []) if n.get('type') == 'trigger']
        if trigger_nodes:
            trigger_config = trigger_nodes[0].get('config', {})
            trigger_type = self.trigger_type_map.get(
                trigger_config.get('event_type', 'webhook'),
                'webhook'
            )
            
            trigger = automation.triggers.first()
            if trigger:
                trigger.type = trigger_type
                trigger.config = trigger_config
                trigger.save()
            else:
                TriggerSpec.objects.create(
                    automation=automation,
                    type=trigger_type,
                    config=trigger_config,
                    enabled=True
                )
            
            # Setup DB trigger if applicable
            if trigger_config.get('event_type') == 'db_change' and trigger_config.get('table'):
                self._setup_db_trigger(trigger_config.get('table'))
        
        # Create new workflow version
        current_version = automation.workflows.order_by('-version').first().version
        
        return self.create_workflow_version(
            automation=automation,
            graph=graph,
            name=name,
            created_by=created_by,
            version=current_version + 1
        )


# Default service instance
default_workflow_service = WorkflowService()
