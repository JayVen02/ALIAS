from flask import Flask
from config import Config
from models import db
from routes.inventory import inventory_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(inventory_bp)

if __name__ == '__main__':
    app.run(debug=True)