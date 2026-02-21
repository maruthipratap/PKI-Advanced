from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.auth.decorators import role_required
from app.auth.models import User, Role
from app.audit.logger import log_action

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/users')
@role_required('ca_admin')
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    roles = Role.query.all()
    return render_template('admin/users.html', users=users, roles=roles)


@admin_bp.route('/admin/users/role/<int:user_id>', methods=['POST'])
@role_required('ca_admin')
def change_role(user_id):
    user     = User.query.get_or_404(user_id)
    new_role_name = request.form.get('role', '').strip()
    role     = Role.query.filter_by(name=new_role_name).first()

    if not role:
        flash('Invalid role selected.', 'error')
        return redirect(url_for('admin.manage_users'))

    # Prevent demoting yourself
    from flask_login import current_user
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'error')
        return redirect(url_for('admin.manage_users'))

    old_role  = user.role_name
    user.role = role
    db.session.commit()

    log_action(
        'ROLE_CHANGED',
        detail=f'Changed {user.username} role from {old_role} → {new_role_name}'
    )
    flash(f'Role updated for {user.username}: {old_role} → {new_role_name}.', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/admin/users/toggle/<int:user_id>', methods=['POST'])
@role_required('ca_admin')
def toggle_user(user_id):
    from flask_login import current_user
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.manage_users'))

    user.is_active = not user.is_active
    db.session.commit()

    action = 'ACTIVATED' if user.is_active else 'DEACTIVATED'
    log_action(f'USER_{action}', detail=f'{user.username} was {action.lower()}')
    flash(f'User {user.username} has been {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.manage_users'))