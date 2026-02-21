from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth.models import User, Role
from app.audit.logger import log_action

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('portal.landing'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=True)
            log_action('LOGIN_SUCCESS', detail=f'User {username} logged in', user=user)
            flash(f'Welcome back, {user.username}!', 'success')

            # Redirect based on role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('portal.landing'))

        else:
            log_action('LOGIN_FAILED',
                detail=f'Failed login attempt for username: {username}',
                status='FAILED'
            )
            flash('Invalid username or password.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('portal.landing'))

    if request.method == 'POST':
        username     = request.form.get('username', '').strip()
        email        = request.form.get('email', '').strip()
        password     = request.form.get('password', '')
        confirm      = request.form.get('confirm_password', '')

        # Validations
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('auth.register'))

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.register'))

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.register'))

        # Assign default 'user' role
        user_role = Role.query.filter_by(name='user').first()

        new_user = User(
            username = username,
            email    = email,
            role     = user_role
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        log_action('USER_REGISTERED',
            detail=f'New user registered: {username}',
            user=new_user
        )

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        log_action('LOGOUT', detail=f'{current_user.username} logged out')
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_email':
            new_email = request.form.get('email', '').strip()
            if User.query.filter_by(email=new_email).first():
                flash('Email already in use.', 'error')
            else:
                current_user.email = new_email
                db.session.commit()
                log_action('PROFILE_UPDATED', detail='Email updated')
                flash('Email updated successfully.', 'success')

        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw     = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')

            if not current_user.check_password(current_pw):
                flash('Current password is incorrect.', 'error')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'error')
            elif len(new_pw) < 8:
                flash('Password must be at least 8 characters.', 'error')
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                log_action('PASSWORD_CHANGED', detail='Password changed')
                flash('Password changed successfully.', 'success')

    from app.models.certificate_db import Certificate
    my_certs = Certificate.query.filter_by(owner_name=current_user.username).all()
    return render_template('profile.html', my_certs=my_certs)