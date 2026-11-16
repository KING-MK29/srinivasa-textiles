import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure backend root is always on sys.path
BACKEND_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BACKEND_DIR.parent
for p in [str(BACKEND_DIR), str(WORKSPACE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Load environment
env_path = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# Database & Seed
from database.db import init_db
from utils.logger import logger

# Import Route Blueprints
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.order_routes import order_bp
from routes.analytics_routes import analytics_bp
from routes.utility_routes import utility_bp
from routes.store_sync_routes import store_sync_bp

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "48316ee8d8a31b3972d811c06df3de91c92554fcffe72aee6e150660dddf02e1")

    # Configurable CORS
    cors_origins_env = os.getenv("CORS_ORIGINS", "*")
    if cors_origins_env == "*":
        allowed_origins = "*"
    else:
        allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    # Preflight OPTIONS handler for seamless cross-origin API calls from GitHub Pages
    @app.before_request
    def handle_options_preflight():
        if request.method == "OPTIONS":
            response = app.make_default_options_response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, x-order-id"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            return response

    # HTTP Security Headers & Cross-Origin Middleware
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, x-order-id"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        return response
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob:; img-src 'self' data: https: blob:; font-src 'self' https: data:; style-src 'self' 'unsafe-inline' https:; connect-src 'self' https: http://localhost:* http://127.0.0.1:*;"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(product_bp, url_prefix="/api/products")
    app.register_blueprint(order_bp, url_prefix="/api/orders")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(utility_bp, url_prefix="/api")
    app.register_blueprint(store_sync_bp, url_prefix="/api/store")

    # Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "error": "Bad Request", "message": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Resource Not Found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({"success": False, "error": "Internal Server Error"}), 500

    # Frontend Static & Single Page Application Serving
    from flask import send_from_directory

    @app.route("/", methods=["GET"])
    def index():
        if (FRONTEND_DIR / "index.html").is_file():
            return send_from_directory(FRONTEND_DIR, "index.html")
        return jsonify({
            "brand": "Srinivasa Textiles",
            "tagline": "Master Weavers & Pure Silk Handloom Emporium Since 1978",
            "apiDocumentation": "/api/health",
            "status": "operational"
        })

    @app.route("/<path:path>", methods=["GET"])
    def serve_frontend_file(path):
        if path.startswith("api/"):
            return jsonify({"success": False, "error": "Resource Not Found"}), 404
        target_file = FRONTEND_DIR / path
        if target_file.is_file():
            return send_from_directory(FRONTEND_DIR, path)
        if (FRONTEND_DIR / f"{path}.html").is_file():
            return send_from_directory(FRONTEND_DIR, f"{path}.html")
        if (FRONTEND_DIR / "index.html").is_file():
            return send_from_directory(FRONTEND_DIR, "index.html")
        return jsonify({"success": False, "error": "Not Found"}), 404

    # Auto-initialize database on launch
    with app.app_context():
        try:
            init_db()
        except Exception as err:
            logger.warning(f"Database startup check: {err}")

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5500))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1")
    logger.info(f"✨ Srinivasa Textiles REST Engine & Unified Web App running on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
