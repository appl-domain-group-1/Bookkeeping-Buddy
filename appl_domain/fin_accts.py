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
                db.execute(
                    "INSERT INTO accounts (acct_name, acct_desc, acct_category, acct_subcategory, debit, initial_bal, "
                    "balance, date_created, created_by, statement, comment, acct_num) VALUES (?, ?, ?, ?, ?, ?, ?, ?, "
                    "?, ?, ?, ?)", (acct_name, acct_desc, acct_category, acct_subcategory, debit, initial_bal,
                                    initial_bal, today, g.user['username'], statement, comment, this_account_num)
                ).fetchone()

                # Create ledger table for the new account
                db.execute(
                    f"CREATE TABLE ledger_{this_account_num} ("
                    "date TEXT NOT NULL,"
                    "description TEXT,"
                    "debit_accounts TEXT NOT NULL,"
                    "credit_accounts TEXT NOT NULL,"
                    "post_reference TEXT NOT NULL,"
                    "balance INTEGER NOT NULL"
                    ")"
                )

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
    # Get all the statements
    statements = db.execute(
        "SELECT * FROM statements"
    ).fetchall()
    statements_dict = {}
    for statement in statements:
        statements_dict[statement['number']] = statement['name']

    return render_template('fin_accts/view_accounts.html',
                           acct_categories=acct_categories,
                           accounts=accounts,
                           statements=statements_dict)


@bp.route('/edit_acct/<account_num>', methods=('GET', 'POST'))
@login_required
def edit_account(account_num):
    # Get a handle on the DB
    db = get_db()

    # Look up the account
    account = db.execute(
        "SELECT * from accounts WHERE acct_num = ?", (account_num,)
    ).fetchone()

    # Get all account categories
    categories = db.execute(
        "SELECT * FROM acct_categories"
    ).fetchall()

    # Get all statements
    statements = db.execute(
        "SELECT * FROM statements"
    ).fetchall()

    if request.method == 'POST':
        try:
            # Get info from form
            acct_name = request.form['acct_name']
            acct_desc = request.form['acct_desc']
            acct_category = request.form['acct_category']
            acct_subcategory = request.form['acct_subcategory']
            debit = request.form['debit']
            statement = request.form['statement']
            comment = request.form['comment']

            # Update the row
            db.execute(
                "UPDATE accounts SET acct_name = ?, acct_desc = ?, acct_category = ?, acct_subcategory = ?, debit = ?, "
                "statement = ?, comment = ? WHERE acct_num = ?", (acct_name, acct_desc, acct_category, acct_subcategory,
                                                                  debit, statement, comment, account_num)
            )
            # Write changes
            db.commit()
            flash("Account updated!")

            # Get a fresh copy of the DB info
            account = db.execute(
                "SELECT * from accounts WHERE acct_num = ?", (account_num,)
            ).fetchone()

        except db.IntegrityError:
            flash("Duplicate account names not allowed")

    # Return the template
    return render_template('fin_accts/create_account.html',
                           account=account,
                           statements=statements,
                           categories=categories)


@bp.route('/deactivate_acct/<account_num>', methods=('GET',))
@login_required
def deactivate_account(account_num):
    if g.user['role'] == 2:
        # Get a handle on the db
        db = get_db()

        # Get the current activation status of the account
        active = db.execute(
            "SELECT active from accounts WHERE acct_num = ?", (account_num,)
        ).fetchone()['active']

        # Toggle the active value
        if active == 1:
            db.execute(
                "UPDATE accounts SET active = ? WHERE acct_num = ?", (0, account_num)
            )
            db.commit()
        else:
            db.execute(
                "UPDATE accounts SET active = ? WHERE acct_num = ?", (1, account_num)
            )
            db.commit()

        # Get fresh DB info
        # acct_categories = db.execute("SELECT * FROM acct_categories")
        # accounts = db.execute("SELECT * FROM accounts")

        return redirect(url_for('fin_accts.view_accounts'))
    else:
        abort(403)


@bp.route('/view_ledger/<account_num>', methods=('GET',))
@login_required
def view_ledger(account_num):
    # Get a handle on the DB
    db = get_db()

    # Get entries from ledger
    entries = db.execute(
        f"SELECT * FROM ledger_{account_num}"
    ).fetchall()

    return render_template('fin_accts/ledger.html', acct_num=account_num, entries=entries)