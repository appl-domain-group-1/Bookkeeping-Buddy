from flask import (Blueprint, flash, redirect, render_template, request, url_for)
from appl_domain.db import get_db

bp = Blueprint('list_users', __name__, url_prefix='/')

@bp.route('list_users', methods=['GET'])
def list_users():
    db = get_db()
    users = db.execute(
        'SELECT * from users'
    ).fetchall()
    return render_template('index.html', z="List of all users", users=users)