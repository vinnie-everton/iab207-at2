from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()

# create a function that creates a web application
# a web server will run this web application
def create_app():
  
    app = Flask(__name__)  
    app.debug = True
    app.secret_key = 'somesecretkey'
    # set the app configuration data 
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sitedata.sqlite'
    # set the upload folder for images when creating events
    app.config['UPLOAD_FOLDER'] = 'website/static/img'
    # set the max length for images uploaded
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  
    
    os.makedirs(os.path.join(app.root_path, 'static', 'img'), exist_ok=True)
    # initialise db with flask app
    db.init_app(app)

    Bootstrap5(app)
    
    # initialise the login manager
    login_manager = LoginManager()
    
    # set the name of the login function that lets user login
    # in our case it is auth.login (blueprintname.viewfunction name)
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # create a user loader function takes userid and returns User
    # Importing inside the create_app function avoids circular references
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
       return db.session.scalar(db.select(User).where(User.id==user_id))
  

    from . import views
    app.register_blueprint(views.main_bp)

    from . import auth
    app.register_blueprint(auth.auth_bp)

    # This error handler will be called when opening when getting a 404 error.
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500


    return app