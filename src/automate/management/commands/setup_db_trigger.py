"""
Management command to set up PostgreSQL triggers on specific tables.

Usage:
    python manage.py setup_db_trigger orders          # Add trigger to 'orders' table
    python manage.py setup_db_trigger auth_user       # Add trigger to 'auth_user' table
    python manage.py setup_db_trigger --list          # List all tables with triggers
    python manage.py setup_db_trigger --remove orders # Remove trigger from table
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Set up PostgreSQL NOTIFY triggers on specific tables"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "table",
            nargs="?",
            type=str,
            help="Table name to add trigger to"
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List all tables with automate triggers"
        )
        parser.add_argument(
            "--remove",
            action="store_true",
            help="Remove trigger from table instead of adding"
        )
        parser.add_argument(
            "--all-models",
            action="store_true",
            help="Add triggers to all Django model tables"
        )
    
    def handle(self, *args, **options):
        db_engine = connection.settings_dict.get("ENGINE", "")
        if "postgresql" not in db_engine and "psycopg" not in db_engine:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ This command requires PostgreSQL. Current: {db_engine}"
                )
            )
            return
        
        if options.get("list"):
            self._list_triggers()
            return
        
        if options.get("all_models"):
            self._add_all_model_triggers()
            return
        
        table = options.get("table")
        if not table:
            self.stdout.write(self.style.ERROR("Please specify a table name"))
            return
        
        if options.get("remove"):
            self._remove_trigger(table)
        else:
            self._add_trigger(table)
    
    def _add_trigger(self, table: str):
        """Add NOTIFY trigger to a table."""
        # Ensure the function exists first
        check_function = """
            SELECT EXISTS (
                SELECT 1 FROM pg_proc 
                WHERE proname = 'automate_notify_changes'
            );
        """
        
        with connection.cursor() as cursor:
            cursor.execute(check_function)
            exists = cursor.fetchone()[0]
            
            if not exists:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠️  Trigger function not found. Run migrations first:\n"
                        "   python manage.py migrate automate"
                    )
                )
                return
            
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, [table])
            
            if not cursor.fetchone()[0]:
                self.stdout.write(self.style.ERROR(f"❌ Table '{table}' not found"))
                return
            
            # Create trigger
            trigger_sql = f"""
                DROP TRIGGER IF EXISTS automate_changes_trigger ON "{table}";
                CREATE TRIGGER automate_changes_trigger
                    AFTER INSERT OR UPDATE OR DELETE ON "{table}"
                    FOR EACH ROW
                    EXECUTE FUNCTION automate_notify_changes();
            """
            
            cursor.execute(trigger_sql)
            self.stdout.write(
                self.style.SUCCESS(f"✅ Trigger added to table: {table}")
            )
    
    def _remove_trigger(self, table: str):
        """Remove trigger from a table."""
        with connection.cursor() as cursor:
            cursor.execute(f'DROP TRIGGER IF EXISTS automate_changes_trigger ON "{table}";')
            self.stdout.write(
                self.style.SUCCESS(f"✅ Trigger removed from table: {table}")
            )
    
    def _list_triggers(self):
        """List all tables with automate triggers."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    event_object_table as table_name,
                    trigger_name,
                    action_timing,
                    event_manipulation
                FROM information_schema.triggers
                WHERE trigger_name = 'automate_changes_trigger'
                ORDER BY table_name;
            """)
            
            rows = cursor.fetchall()
            
            if not rows:
                self.stdout.write("No tables have automate triggers configured.")
                return
            
            self.stdout.write("\nTables with automate triggers:")
            self.stdout.write("-" * 50)
            
            for row in rows:
                self.stdout.write(f"  📋 {row[0]} ({row[2]} {row[3]})")
    
    def _add_all_model_triggers(self):
        """Add triggers to all Django model tables."""
        from django.apps import apps
        
        tables_added = 0
        
        for model in apps.get_models():
            table = model._meta.db_table
            
            # Skip Django internal tables
            if table.startswith("django_") or table.startswith("auth_permission"):
                continue
            
            # Skip automate's own tables (could cause loops)
            if table.startswith("automate_"):
                continue
            
            try:
                self._add_trigger(table)
                tables_added += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Skipped {table}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Added triggers to {tables_added} tables")
        )
