from flask import Flask, jsonify, send_from_directory
import os


from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config
from app import extensions


def create_app():
    
    FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)

    app = Flask(
        __name__,
        static_folder=FRONTEND_DIR,
        static_url_path="/static"
    )

    Config.validate()
    app.config.from_object(Config)

    CORS(app)
    extensions.init_extensions(app)

    # Import routes after initializing MongoDB
    from app.routes.auth_routes import auth_bp
    from app.routes.document_routes import document_bp
    from app.routes.access_routes import access_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.search_routes import search_bp

    # Register routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(access_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(search_bp)

    # Home route
    @app.route("/")
    def home():
        return send_from_directory(FRONTEND_DIR, "index.html")

    # Database health check
    @app.route("/api/health/db")
    def database_health():
        try:
            extensions.mongo_client.admin.command("ping")

            return jsonify({
                "status": "success",
                "message": "MongoDB connected successfully"
            }), 200

        except Exception:
            app.logger.exception("MongoDB connection failed")

            return jsonify({
                "status": "error",
                "message": "MongoDB connection failed"
            }), 500

    return app
