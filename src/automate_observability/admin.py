from django.contrib import admin
from .models import AuditLogEntry

@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "actor", "action", "object_type", "trace_id"]
    list_filter = ["action", "object_type"]
    search_fields = ["actor", "details", "trace_id"]
    readonly_fields = ["timestamp", "actor", "action", "object_type", "object_id", "trace_id", "details"]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
