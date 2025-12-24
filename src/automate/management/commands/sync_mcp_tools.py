"""
Management command to sync tools from MCP servers.

Usage:
    python manage.py sync_mcp_tools              # Sync all enabled servers
    python manage.py sync_mcp_tools --server=my-mcp  # Sync specific server
    python manage.py sync_mcp_tools --all        # Sync all servers (including disabled)
"""
from django.core.management.base import BaseCommand, CommandError
from automate.models import MCPServer
from automate_llm.mcp_client import sync_mcp_tools, MCPClientError


class Command(BaseCommand):
    help = "Sync tools from registered MCP servers"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--server",
            type=str,
            help="Slug of specific server to sync"
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Include disabled servers"
        )
    
    def handle(self, *args, **options):
        server_slug = options.get("server")
        include_all = options.get("all")
        
        if server_slug:
            try:
                servers = [MCPServer.objects.get(slug=server_slug)]
            except MCPServer.DoesNotExist:
                raise CommandError(f"MCP Server '{server_slug}' not found")
        else:
            servers = MCPServer.objects.all()
            if not include_all:
                servers = servers.filter(enabled=True)
        
        if not servers:
            self.stdout.write(self.style.WARNING("No MCP servers to sync"))
            return
        
        total_created = 0
        total_updated = 0
        errors = []
        
        for server in servers:
            self.stdout.write(f"Syncing {server.name} ({server.endpoint_url})...")
            
            try:
                created, updated, schema = sync_mcp_tools(server)
                total_created += created
                total_updated += updated
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ {created} new, {updated} updated tools (schema: {schema})")
                )
            except MCPClientError as e:
                errors.append(server.name)
                self.stdout.write(
                    self.style.ERROR(f"  ✗ {str(e)}")
                )
        
        # Summary
        self.stdout.write("")
        self.stdout.write(f"Total: {total_created} created, {total_updated} updated")
        
        if errors:
            self.stdout.write(
                self.style.ERROR(f"Failed: {', '.join(errors)}")
            )
