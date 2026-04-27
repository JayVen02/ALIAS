import os
from flask import Flask
from config import Config
from extensions import mysql
from routes.auth import auth_bp
from routes.pages import pages_bp
from routes.inventory import inventory_bp
from routes.users import users_bp
from routes.pdf import pdf_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    mysql.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(pdf_bp)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)