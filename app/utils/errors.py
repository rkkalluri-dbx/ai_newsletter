"""Error handlers and custom exceptions."""
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


class APIError(Exception):
    """Base API error class."""

    def __init__(self, message: str, status_code: int = 400, payload: dict = None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["error"] = self.message
        rv["status_code"] = self.status_code
        return rv


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(APIError):
    """Validation error."""

    def __init__(self, message: str, errors: dict = None):
        super().__init__(message, status_code=400, payload={"validation_errors": errors})


class ConflictError(APIError):
    """Conflict error for optimistic locking."""

    def __init__(self, message: str = "Resource has been modified", changed_fields: dict = None):
        super().__init__(
            message, status_code=409, payload={"changed_fields": changed_fields}
        )


def register_error_handlers(app: Flask):
    """Register error handlers on the Flask app."""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify({"error": "Bad request", "status_code": 400}), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        from flask import request, send_from_directory
        # For API routes, return JSON error
        if request.path.startswith('/api/'):
            return jsonify({"error": "Resource not found", "status_code": 404}), 404
        # For all other routes, serve the React frontend (SPA routing)
        try:
            return send_from_directory(app.static_folder, 'index.html')
        except Exception:
            return jsonify({"error": "Resource not found", "status_code": 404}), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        import traceback
        app.logger.error(f"Internal server error: {error}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            "error": "Internal server error",
            "status_code": 500,
            "message": str(error)
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        import traceback
        app.logger.error(f"Unhandled exception: {error}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            "error": "Unexpected error",
            "status_code": 500,
            "message": str(error),
            "type": type(error).__name__
        }), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return (
            jsonify({"error": error.description, "status_code": error.code}),
            error.code,
        )
