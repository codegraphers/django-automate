"""
PostgreSQL Trigger Function Migration

Creates a reusable trigger function that sends NOTIFY events when table rows change.
This is a data migration that creates PostgreSQL functions and triggers.
"""
from django.db import migrations


# PostgreSQL function that sends NOTIFY on row changes
CREATE_NOTIFY_FUNCTION = """
CREATE OR REPLACE FUNCTION automate_notify_changes()
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
    channel TEXT := 'automate_table_changes';
BEGIN
    -- Build payload based on operation type
    IF TG_OP = 'DELETE' THEN
        payload := json_build_object(
            'table', TG_TABLE_NAME,
            'schema', TG_TABLE_SCHEMA,
            'action', TG_OP,
            'timestamp', CURRENT_TIMESTAMP,
            'data', row_to_json(OLD)
        );
    ELSE
        payload := json_build_object(
            'table', TG_TABLE_NAME,
            'schema', TG_TABLE_SCHEMA,
            'action', TG_OP,
            'timestamp', CURRENT_TIMESTAMP,
            'data', row_to_json(NEW),
            'old_data', CASE WHEN TG_OP = 'UPDATE' THEN row_to_json(OLD) ELSE NULL END
        );
    END IF;

    -- Send notification
    PERFORM pg_notify(channel, payload::text);
    
    -- Return appropriate row
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

DROP_NOTIFY_FUNCTION = """
DROP FUNCTION IF EXISTS automate_notify_changes() CASCADE;
"""

# Helper to create trigger for a specific table
CREATE_TRIGGER_TEMPLATE = """
DROP TRIGGER IF EXISTS automate_changes_trigger ON {table};
CREATE TRIGGER automate_changes_trigger
    AFTER INSERT OR UPDATE OR DELETE ON {table}
    FOR EACH ROW
    EXECUTE FUNCTION automate_notify_changes();
"""


class Migration(migrations.Migration):
    """
    Creates the PostgreSQL notify function for automation triggers.
    
    Note: This does NOT create triggers on any tables automatically.
    Use management command `setup_db_trigger` to add triggers to specific tables.
    """
    
    dependencies = [
        ('automate', '0014_add_mcp_models'),
    ]
    

def create_notify_function(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(CREATE_NOTIFY_FUNCTION)

def drop_notify_function(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(DROP_NOTIFY_FUNCTION)

class Migration(migrations.Migration):
    """
    Creates the PostgreSQL notify function for automation triggers.
    
    Note: This does NOT create triggers on any tables automatically.
    Use management command `setup_db_trigger` to add triggers to specific tables.
    """
    
    dependencies = [
        ('automate', '0014_add_mcp_models'),
    ]
    
    operations = [
        migrations.RunPython(
            code=create_notify_function,
            reverse_code=drop_notify_function,
        ),
    ]
