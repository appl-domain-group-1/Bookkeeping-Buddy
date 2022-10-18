from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
from appl_domain.db import get_db
from datetime import date, datetime, timedelta
from appl_domain.auth import login_required
import json

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
        # Remove unnecessary symbols from initial balance
        initial_bal = request.form['initial_bal'].replace(',', '').replace('.', '').replace('$', '')
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

                # Get the current values which were inserted into the DB and store them as a JSON object
                new_values = json.dumps([acct_name, acct_desc, acct_category, acct_subcategory, debit, initial_bal, initial_bal, today, g.user['username'], statement, comment])

                # Log the change
                db.execute(
                    "INSERT INTO events (account, user_id, timestamp, before_values, after_values) VALUES (?, ?, ?, ?, ?)",
                    (this_account_num, g.user['username'], datetime.now(), None, new_values)
                )

                # This is for debugging
                db.execute(f"DROP TABLE IF EXISTS ledger_{this_account_num}")

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
        account_info = db.execute(
            "SELECT active, balance from accounts WHERE acct_num = ?", (account_num,)
        ).fetchone()

        # Toggle the active value if the account is active and doesn't have a positive balance
        if (account_info['active'] == 1) and (account_info['balance'] <= 0):
            db.execute(
                "UPDATE accounts SET active = ? WHERE acct_num = ?", (0, account_num)
            )
            db.commit()

        # Do not allow accounts with balance > 0 to be deactivated
        elif (account_info['active']) and (account_info['balance'] > 0):
            flash("Accounts with positive balance may not be deactivated")
            return redirect(url_for('fin_accts.view_accounts'))

        # Always allow an inactive account to be activated
        else:
            db.execute(
                "UPDATE accounts SET active = ? WHERE acct_num = ?", (1, account_num)
            )
            db.commit()

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

    # Get all account info
    account = db.execute(
        "SELECT * FROM accounts WHERE acct_num = ?", (account_num,)
    ).fetchone()

    return render_template('fin_accts/ledger.html', entries=entries, account=account)


@bp.route('/view_logs/<account_num>', methods=('GET',))
@login_required
def view_logs(account_num):
    # Get a handle on the DB
    db = get_db()

    # Get all the events for this account number
    events = db.execute(
        "SELECT * FROM events WHERE account = ?", (account_num,)
    ).fetchall()

    return render_template('fin_accts/view_logs.html', events=events, account_num=account_num)