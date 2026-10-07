"""
Authentication routes - Login, Logout, Register, Profile.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        from ..services.auth_service import authenticate_user
        from ..services.additional_services import create_audit_log
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        user = authenticate_user(email, password)
        if user:
            login_user(user, remember=remember)
            create_audit_log(user.id, user.full_name, 'login', 'user', user.id, request_obj=request)
            flash('Welcome back!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    from ..services.additional_services import create_audit_log
    create_audit_log(current_user.id, current_user.full_name, 'logout', 'user', current_user.id, request_obj=request)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'admin':
        flash('Only admins can register new users.', 'error')
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        from ..services.auth_service import create_user, get_user_by_email
        from ..utils.validators import validate_email, validate_password_strength
        data = request.form.to_dict()
        if not validate_email(data.get('email', '')):
            flash('Invalid email address.', 'error')
            return render_template('auth/register.html')
        if get_user_by_email(data['email']):
            flash('Email already exists.', 'error')
            return render_template('auth/register.html')
        if data.get('password') != data.get('confirm_password'):
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        valid, msg = validate_password_strength(data.get('password', ''))
        if not valid:
            flash(msg, 'error')
            return render_template('auth/register.html')
        try:
            create_user(data)
            flash('User created successfully!', 'success')
            return redirect(url_for('users.list_users'))
        except Exception as e:
            flash(f'Error creating user: {e}', 'error')
    return render_template('auth/register.html')


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        from ..services.auth_service import update_user, change_password
        action = request.form.get('action')
        if action == 'update_profile':
            update_user(current_user.id, {
                'first_name': request.form.get('first_name', ''),
                'last_name': request.form.get('last_name', ''),
                'phone': request.form.get('phone', '')
            })
            flash('Profile updated.', 'success')
        elif action == 'change_password':
            success, msg = change_password(
                current_user.id,
                request.form.get('current_password', ''),
                request.form.get('new_password', '')
            )
            flash(msg, 'success' if success else 'error')
        return redirect(url_for('auth.profile'))
    return render_template('users/profile.html', user=current_user)
