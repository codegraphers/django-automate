import os
import subprocess
import sys
import time

# Configuration
DJANGO_PORT = 8000
MKDOCS_PORT = 8001
HOST = "127.0.0.1"


def main():
    print("🚀 Starting Django Automate Dev Environment...")

    # Define commands
    django_cmd = [sys.executable, "example_project/manage.py", "runserver", f"{HOST}:{DJANGO_PORT}"]
    mkdocs_cmd = ["mkdocs", "serve", "-a", f"{HOST}:{MKDOCS_PORT}"]

    # Environment variables
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    processes = []

    try:
        # Start Django
        print("   -> Launching Django...")
        p_django = subprocess.Popen(django_cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        processes.append(p_django)

        # Start MkDocs
        print("   -> Launching MkDocs...")
        p_mkdocs = subprocess.Popen(mkdocs_cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        processes.append(p_mkdocs)

        # Give them a moment to start
        time.sleep(3)

        # Check for immediate failures
        if p_django.poll() is not None:
            print("❌ Django failed to start:")
            print(p_django.stderr.read().decode())
            return

        if p_mkdocs.poll() is not None:
            print("❌ MkDocs failed to start:")
            print(p_mkdocs.stderr.read().decode())
            return

        print("\n✅ Services Running!")
        print("-" * 30)
        print(f"📱 Admin Panel:   http://{HOST}:{DJANGO_PORT}/admin/")
        print(f"🔌 Swagger UI:    http://{HOST}:{DJANGO_PORT}/api/docs/")
        print(f"📚 Documentation: http://{HOST}:{MKDOCS_PORT}/")
        print("-" * 30)
        print("Press Ctrl+C to stop all services.")

        # Keep alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping services...")
    finally:
        for p in processes:
            p.terminate()
        print("Done.")


if __name__ == "__main__":
    main()
