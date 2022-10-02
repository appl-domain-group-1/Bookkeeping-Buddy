from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
from appl_domain.db import get_db
from datetime import date, datetime, timedelta
from appl_domain.auth import login_required

bp = Blueprint('fin_accts', __name__, url_prefix='/fin_accts')


@bp.route('/create_acct', methods=('GET', 'POST'))
@login_required
def create_acct():
    """
    Allow an administrator to create a new financial account
    """
    # If the user isn't an admin, boot them
    if g.user['role'] != 2:
        abort(403)

    # Get a handle on the database
    db = get_db()
    # Get all account categories
    categories = db.execute(
        "SELECT * FROM acct_categories"
    ).fetchall()

    # Get all statement types
    statements = db.execute(
        "SELECT * FROM statements"
    ).fetchall()

    if request.method == 'POST':
        error = None

        # Get a handle on the DB
        db = get_db()

        # Get today's date
        today = datetime.today().date()
        # Format today's date as a string for the database (YYYY-MM-DD)
        today = f"{today.year}-{today.month:02d}-{today.day:02d}"

        # Get info from form
        acct_name = request.form['acct_name']
        acct_desc = request.form['acct_desc']
        acct_category = request.form['acct_category']
        acct_subcategory = request.form['acct_subcategory']
        debit = request.form['debit']
        initial_bal = request.form['initial_bal']
        statement = request.form['statement']
        comment = request.form['comment']

        # Validate input  # TODO: perform more field validation
        if not acct_name:
            error = "Account must have a name"
        # Check that the account category supplied is valid

        if error is None:
            try:
                # Generate new account number
                highest_acct_number = db.execute(
                    "SELECT acct_num FROM accounts WHERE acct_num = (SELECT MAX(acct_num) FROM accounts WHERE "
                    "acct_category = ?)", (acct_category,)
                ).fetchone()
                if highest_acct_number:
                    highest_acct_number = highest_acct_number['acct_num']
                    this_account_num = highest_acct_number + 1
                else:
                    this_account_num = (int(acct_category) * 1000) + 1

                # Add the new row
                this_account = db.execute(
                    "INSERT INTO accounts (acct_name, acct_desc, acct_category, acct_subcategory, debit, initial_bal, "
                    "balance, date_created, created_by, statement, comment, acct_num) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                    "RETURNING *", (acct_name, acct_desc, acct_category, acct_subcategory, debit, initial_bal, initial_bal, today,
                     g.user['username'], statement, comment, this_account_num)
                ).fetchone()
                # Commit the change
                db.commit()

            except (db.InternalError,
                    db.IntegrityError):
                error = f"Database error. Contact your administrator."
            else:
                return redirect(url_for('fin_accts.view_accounts'))
        flash(error)

    return render_template('fin_accts/create_account.html', categories=categories, statements=statements)


@bp.route('/', methods=('GET',))
@login_required
def view_accounts():
    # Get a handle on the DB
    db = get_db()
    # Get all the different account categories
    acct_categories = db.execute(
        "SELECT * FROM acct_categories"
    ).fetchall()
    # Get all the different accounts
    accounts = db.execute(
        "SELECT * FROM accounts ORDER BY acct_num"
    ).fetchall()

    return render_template('fin_accts/view_accounts.html', acct_categories=acct_categories, accounts=accounts)
