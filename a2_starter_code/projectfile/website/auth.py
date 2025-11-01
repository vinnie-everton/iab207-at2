from flask import Blueprint, flash, render_template, request, url_for, redirect
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from .models import User
from .forms import LoginForm, RegisterForm
from . import db

auth_bp = Blueprint('auth', __name__)

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
# Login function
# This function will allow users to login in the website.
def login():
    login_form = LoginForm()
    error = None
    if login_form.validate_on_submit():
        user_name = login_form.user_name.data
        password = login_form.password.data
        user = db.session.scalar(db.select(User).where(User.username==user_name))
        # Validation is included if users writes the wrong username or password
        if user is None:
            error = 'Incorrect user name'
        elif not check_password_hash(user.password_hash, password):
            error = 'Incorrect password'
        if error is None:
            login_user(user)
            nextp = request.args.get('next') 
            print(nextp)
            if nextp is None or not nextp.startswith('/'):
                return redirect(url_for('main.index'))
            return redirect(nextp)
        else:
            flash(error)
    return render_template('user.html', form=login_form, heading='Login')


# Register route 

@auth_bp.route('/register', methods=['GET', 'POST'])
# Register function
# This is the function which will allow users to register new accounts in the website. 
def register():
    register_form = RegisterForm()
    error = None
    if register_form.validate_on_submit():
        user_name = register_form.user_name.data
        full_name = register_form.full_name.data
        password = register_form.password.data
        email = register_form.email.data
        address = register_form.address.data
        contact = register_form.contact.data
        # It will also check if the user name or email already exists in the database 
        # and if it does, the user will not be allowed to register with that user name or email.
        existing_user = db.session.scalar(db.select(User).where(User.username==user_name))
        existing_email = db.session.scalar(db.select(User).where(User.emailid==email))

        if existing_user:
            flash('Username already exists. Please choose another one.')
            return render_template('user.html', form=register_form, heading='Register')
        if existing_email:
            flash('Email already registered. Please use another email.')
            return render_template('user.html', form=register_form, heading='Register')


       # Before the new user details are added to the db, the user's password will be hashed.
        hashed_pwd = generate_password_hash(password)
        new_user = User(username=user_name, fullname=full_name, address=address, contact=contact, emailid=email, password_hash = hashed_pwd)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        flash('Registration successful! Welcome!')
        return redirect(url_for('main.index'))



    
    return render_template('user.html', form=register_form, heading='Register')

# Logout route

@auth_bp.route('/logout')
# Logout function will simply log out the user from the website and redirect them to the index page.
def logout():
    logout_user()
    return redirect(url_for('main.index'))