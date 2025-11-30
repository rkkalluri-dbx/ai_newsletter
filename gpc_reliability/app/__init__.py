"""Flask application factory."""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from app.database import db


def create_app(config_name: str = "development") -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: Configuration environment (development, staging, production)

    Returns:
        Configured Flask application instance
    """
    # Set up static folder for frontend
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    app = Flask(__name__, static_folder=static_folder, static_url_path='')

    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config.get("CORS_ORIGINS", ["http://localhost:5173"]))

    # Register blueprints
    from app.routes.projects import projects_bp
    from app.routes.vendors import vendors_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.alerts import alerts_bp
    from app.routes.gantt import gantt_bp
    from app.routes.milestones import milestones_bp

    app.register_blueprint(projects_bp, url_prefix="/api/v1/projects")
    app.register_blueprint(vendors_bp, url_prefix="/api/v1/vendors")
    app.register_blueprint(dashboard_bp, url_prefix="/api/v1/dashboard")
    app.register_blueprint(alerts_bp, url_prefix="/api/v1/alerts")
    app.register_blueprint(gantt_bp, url_prefix="/api/v1/gantt")
    app.register_blueprint(milestones_bp, url_prefix="/api/v1/milestones")

    # Register error handlers
    from app.utils.errors import register_error_handlers
    register_error_handlers(app)

    # Register CLI commands
    from app.cli import register_cli_commands
    register_cli_commands(app)

    # Health check endpoint
    @app.route("/health")
    def health():
        return {"status": "healthy", "service": "gpc-reliability-tracker"}

    # Debug endpoint to check database connectivity
    @app.route("/api/v1/debug")
    def debug_info():
        import traceback
        debug = {
            "status": "ok",
            "database_check": None,
            "env_check": {
                "DATABRICKS_SERVER_HOSTNAME": bool(os.environ.get("DATABRICKS_SERVER_HOSTNAME")),
                "DATABRICKS_HTTP_PATH": bool(os.environ.get("DATABRICKS_HTTP_PATH")),
                "DATABRICKS_CATALOG": os.environ.get("DATABRICKS_CATALOG"),
                "DATABRICKS_SCHEMA": os.environ.get("DATABRICKS_SCHEMA"),
            },
            "static_folder": app.static_folder,
            "static_folder_exists": os.path.exists(app.static_folder) if app.static_folder else False,
        }
        try:
            # Test database connection
            result = db.execute("SELECT 1 as test")
            debug["database_check"] = "connected" if result else "no result"
        except Exception as e:
            debug["database_check"] = f"error: {str(e)}"
            debug["database_traceback"] = traceback.format_exc()
        return debug

    # API info endpoint
    @app.route("/api")
    def api_info():
        return {
            "service": "GPC Reliability Tracker API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "projects": "/api/v1/projects",
                "vendors": "/api/v1/vendors",
                "dashboard": "/api/v1/dashboard/summary",
                "alerts": "/api/v1/alerts",
                "milestones": "/api/v1/milestones",
                "gantt": "/api/v1/gantt"
            }
        }

    # Serve React frontend for all non-API routes
    @app.route('/')
    def serve_frontend():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        # Serve static files or fallback to index.html for SPA routing
        if os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    return app
