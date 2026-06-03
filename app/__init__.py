# app/__init__.py
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config())
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    from app import models
    from app.routes.main import main_bp
    from app.routes.movies import movies_bp
    from app.routes.tickets import tickets_bp
    from app.routes.auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(auth_bp)

    @app.context_processor
    def inject_user():
        return {'current_user_name': session.get('user_name')}

    return app