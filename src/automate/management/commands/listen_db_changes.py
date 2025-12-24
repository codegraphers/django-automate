"""
PostgreSQL LISTEN/NOTIFY Listener

Listens for database change notifications and creates Events in the automation system.
Uses asyncpg for efficient async listening.

Usage:
    python manage.py listen_db_changes
    python manage.py listen_db_changes --channel=table_changes
"""
import asyncio
import json
import logging
import signal
import sys
from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Listen for PostgreSQL NOTIFY events and create automation Events"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--channel",
            type=str,
            default="automate_table_changes",
            help="PostgreSQL channel to listen on"
        )
        parser.add_argument(
            "--use-psycopg",
            action="store_true",
            help="Use psycopg3 instead of asyncpg (synchronous)"
        )
    
    def handle(self, *args, **options):
        channel = options["channel"]
        use_psycopg = options.get("use_psycopg", False)
        
        # Check if using PostgreSQL
        db_engine = connection.settings_dict.get("ENGINE", "")
        if "postgresql" not in db_engine and "psycopg" not in db_engine:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Current database is not PostgreSQL ({db_engine}).\n"
                    "   DB triggers require PostgreSQL with LISTEN/NOTIFY support.\n"
                    "   For SQLite, use polling-based triggers instead."
                )
            )
            return
        
        self.stdout.write(self.style.SUCCESS(f"🎧 Starting LISTEN on channel: {channel}"))
        self.stdout.write("Press Ctrl+C to stop\n")
        
        if use_psycopg:
            self._listen_psycopg(channel)
        else:
            try:
                asyncio.run(self._listen_asyncpg(channel))
            except ImportError:
                self.stdout.write(
                    self.style.WARNING(
                        "asyncpg not installed, falling back to psycopg3..."
                    )
                )
                self._listen_psycopg(channel)
    
    async def _listen_asyncpg(self, channel: str):
        """Async listener using asyncpg (recommended for production)."""
        try:
            import asyncpg
        except ImportError:
            raise ImportError("asyncpg required: pip install asyncpg")
        
        db_settings = connection.settings_dict
        dsn = f"postgresql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings.get('PORT', 5432)}/{db_settings['NAME']}"
        
        conn = await asyncpg.connect(dsn)
        
        async def handle_notification(conn, pid, channel, payload):
            self.stdout.write(f"📨 Received: {payload[:100]}...")
            await self._process_notification(payload)
        
        await conn.add_listener(channel, handle_notification)
        self.stdout.write(self.style.SUCCESS(f"✅ Listening on {channel}..."))
        
        # Keep running
        stop_event = asyncio.Event()
        
        def signal_handler():
            stop_event.set()
        
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
        
        await stop_event.wait()
        
        await conn.remove_listener(channel, handle_notification)
        await conn.close()
        self.stdout.write("\n🛑 Listener stopped.")
    
    def _listen_psycopg(self, channel: str):
        """Synchronous listener using psycopg3 or Django's connection."""
        import select
        
        with connection.cursor() as cursor:
            cursor.execute(f"LISTEN {channel};")
            self.stdout.write(self.style.SUCCESS(f"✅ Listening on {channel}..."))
            
            try:
                while True:
                    # Wait for notification
                    if select.select([connection.connection], [], [], 5.0) == ([], [], []):
                        # Timeout, check for interrupts
                        continue
                    
                    connection.connection.poll()
                    
                    while connection.connection.notifies:
                        notify = connection.connection.notifies.pop(0)
                        self.stdout.write(f"📨 Received: {notify.payload[:100]}...")
                        self._process_notification_sync(notify.payload)
                        
            except KeyboardInterrupt:
                self.stdout.write("\n🛑 Listener stopped.")
    
    async def _process_notification(self, payload: str):
        """Process notification async - create Event and dispatch."""
        # Run in thread pool to use Django ORM
        await asyncio.get_event_loop().run_in_executor(
            None, self._process_notification_sync, payload
        )
    
    def _process_notification_sync(self, payload: str):
        """Process notification - create Event in database."""
        from automate.models import Event
        from automate.ingestion import ingest_event
        
        try:
            data = json.loads(payload)
            
            # Create event
            event = ingest_event(
                event_type=f"db.{data.get('table', 'unknown')}.{data.get('action', 'change').lower()}",
                source="postgres_trigger",
                payload=data.get("data", {}),
                idempotency_key=f"pg_{data.get('table')}_{data.get('action')}_{data.get('data', {}).get('id', '')}_{data.get('timestamp', '')}"
            )
            
            self.stdout.write(
                self.style.SUCCESS(f"    ✅ Created Event: {event.id}")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
        except Exception as e:
            logger.exception(f"Failed to process notification: {e}")
