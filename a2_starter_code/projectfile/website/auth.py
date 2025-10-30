from flask import Blueprint, flash, render_template, request, url_for, redirect
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from .models import User
from .forms import LoginForm, RegisterForm
from . import db

# Create a blueprint - make sure all BPs have unique names
auth_bp = Blueprint('auth', __name__)

# this is a hint for a login function
@auth_bp.route('/login', methods=['GET', 'POST'])
# view function
def login():
    login_form = LoginForm()
    error = None
    if login_form.validate_on_submit():
        user_name = login_form.user_name.data
        password = login_form.password.data
        user = db.session.scalar(db.select(User).where(User.username==user_name))
        
        if user is None:
            error = 'Incorrect user name'
        elif not check_password_hash(user.password_hash, password): # takes the hash and cleartext password
            error = 'Incorrect password'
        if error is None:
            login_user(user)
            nextp = request.args.get('next') # this gives the url from where the login page was accessed
            print(nextp)
            if nextp is None or not nextp.startswith('/'):
                return redirect(url_for('main.index'))
            return redirect(nextp)
        else:
            flash(error)
    return render_template('user.html', form=login_form, heading='Login')


# Register Route 
@auth_bp.route('/register', methods=['GET', 'POST'])

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

        existing_user = db.session.scalar(db.select(User).where(User.username==user_name))
        existing_email = db.session.scalar(db.select(User).where(User.emailid==email))

        if existing_user:
            flash('Username already exists. Please choose another one.')
            return render_template('user.html', form=register_form, heading='Register')
        if existing_email:
            flash('Email already registered. Please use another email.')
            return render_template('user.html', form=register_form, heading='Register')




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
def logout():
    logout_user()
    return redirect(url_for('main.index'))