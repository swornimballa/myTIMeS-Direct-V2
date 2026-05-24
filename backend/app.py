from flask import Flask
from health import health_bp

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(health_bp, url_prefix='/health')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
