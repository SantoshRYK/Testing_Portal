"""
Home Blueprint - Dashboard/Landing Page
"""
from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps

# Create blueprint
home_bp = Blueprint('home', __name__)


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@home_bp.route('/')
@home_bp.route('/home')
@home_bp.route('/index')
@login_required
def index():
    """Home/Dashboard page"""
    user = session.get('user', {})
    return render_template('home/index.html', user=user)


@home_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page (alias for index)"""
    return redirect(url_for('home.index'))