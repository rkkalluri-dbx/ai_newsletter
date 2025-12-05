"""WSGI entry point for production deployment."""
import os
from app import create_app

config_name = os.environ.get("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    print("Starting GPC Reliability Tracker App...")
    app.run()
