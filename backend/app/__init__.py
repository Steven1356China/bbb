from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    CORS(app, supports_credentials=True)
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    from app.auth import bp as auth_bp
    from app.problems import bp as problems_bp
    from app.submissions import bp as submissions_bp
    from app.contests import bp as contests_bp
    from app.users import bp as users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(problems_bp, url_prefix='/api/problems')
    app.register_blueprint(submissions_bp, url_prefix='/api/submissions')
    app.register_blueprint(contests_bp, url_prefix='/api/contests')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    return app
