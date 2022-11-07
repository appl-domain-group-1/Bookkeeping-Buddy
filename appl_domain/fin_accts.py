from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
from appl_domain.db import get_db
from appl_domain.email_tasks import send_email
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

    # Get all subcategories
    subcategories = db.execute(
        "SELECT * FROM subcategories"
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
        acct_category = int(request.form['acct_category'])
        acct_subcategory = int(request.form['acct_subcategory'])
        debit = int(request.form['debit'])
        # Remove unnecessary symbols from initial balance
        initial_bal = int(request.form['initial_bal'].replace(',', '').replace('.', '').replace('$', ''))
        statement = int(request.form['statement'])
        comment = request.form['comment']

        # Validate input  # TODO: perform more field validation
        if not acct_name:
            error = "Account must have a name"

        # Ensure that the subcategory is valid for the chosen category
        subcategory_category = db.execute(
            "SELECT * from subcategories WHERE id_num = ?", (acct_subcategory,)
        ).fetchone()['category']
        if subcategory_category != acct_category:
            error = "Invalid subcategory for account category"

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
                new_values = json.dumps(
                    [acct_name, acct_desc, acct_category, acct_subcategory, debit, initial_bal, initial_bal, today,
                     g.user['username'], statement, comment])

                # Log the change in the event logs table
                db.execute(
                    "INSERT INTO events (account, user_id, timestamp, before_values, after_values, edit_type) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (this_account_num, g.user['username'], datetime.now(), None, new_values, 1)
                )

                # If this account already had a ledger table created (ex: if the account creation process failed
                # for some reason), then drop the table before trying to create it
                db.execute(f"DROP TABLE IF EXISTS ledger_{this_account_num}")

                # Create ledger table for the new account
                db.execute(
                    f"CREATE TABLE ledger_{this_account_num} ("
                    "date TEXT NOT NULL,"
                    "description TEXT,"
                    "debit INTEGER,"
                    "credit INTEGER,"
                    "post_reference TEXT REFERENCES journal(id_num),"
                    "balance INTEGER NOT NULL"
                    ")"
                )

                # Commit the change
                db.commit()

                # Add the first row to the account with creation info
                db.execute(
                    f"INSERT INTO ledger_{this_account_num} "
                    f"(date, description, debit, credit, post_reference, balance) "
                    f"VALUES (?, ?, ?, ?, ?, ?)",
                    (datetime.now(), "Account creation", None, None, None, initial_bal)
                )

                # Commit the change
                db.commit()

            except (db.InternalError,
                    db.IntegrityError) as E:
                error = f"Database error. Contact your administrator.{E}"
            else:
                return redirect(url_for('fin_accts.view_accounts'))
        flash(error)

    return render_template('fin_accts/create_account.html',
                           categories=categories,
                           statements=statements,
                           subcategories=subcategories)


@bp.route('/', methods=('GET',))
@login_required
def view_accounts():
    # Get a handle on the DB
    db = get_db()

    # Get all the different account categories
    acct_categories = db.execute(
        "SELECT * FROM acct_categories"
    ).fetchall()

    # Get all the subcategories
    subcategories = db.execute(
        "SELECT * FROM subcategories"
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
                           subcategories=subcategories,
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

    # Get all subcategories
    subcategories = db.execute(
        "SELECT * FROM subcategories"
    ).fetchall()

    # Get all statements
    statements = db.execute(
        "SELECT * FROM statements"
    ).fetchall()

    if request.method == 'POST':

        # Get info from form
        acct_name = request.form['acct_name']
        acct_desc = request.form['acct_desc']
        acct_category = int(request.form['acct_category'])
        acct_subcategory = int(request.form['acct_subcategory'])
        debit = int(request.form['debit'])
        statement = int(request.form['statement'])
        comment = request.form['comment']

        # Check that the subcategory is valid with the chosen category
        subcategory_category = db.execute(
            "SELECT * from subcategories WHERE id_num = ?", (acct_subcategory,)
        ).fetchone()['category']
        if subcategory_category != acct_category:
            flash("Invalid subcategory for account category")
        else:
            try:
                # Put the new values and the old values into JSON objects for the events database
                new_values = json.dumps(
                    [acct_name, acct_desc, acct_category, acct_subcategory, debit, statement, comment])

                old_values = json.dumps(
                    [account['acct_name'], account['acct_desc'], account['acct_category'], account['acct_subcategory'],
                     account['debit'], account['statement'], account['comment']])

                if new_values != old_values:
                    # Update the row
                    db.execute(
                        "UPDATE accounts SET acct_name = ?, acct_desc = ?, acct_category = ?, acct_subcategory = ?, debit = ?, "
                        "statement = ?, comment = ? WHERE acct_num = ?", (acct_name, acct_desc, acct_category, acct_subcategory,
                                                                          debit, statement, comment, account_num)
                    )


                    # Log the change in the event logs table
                    db.execute(
                        "INSERT INTO events (account, user_id, timestamp, before_values, after_values, edit_type) VALUES (?, ?, ?, ?, ?, ?)",
                        (account_num, g.user['username'], datetime.now(), old_values, new_values, 2)
                    )

                    # Write changes to the database
                    db.commit()
                    flash("Account updated!")

            except db.IntegrityError:
                flash("Duplicate account names not allowed")

    # Get a fresh copy of the DB info
    account = db.execute(
        "SELECT * from accounts WHERE acct_num = ?", (account_num,)
    ).fetchone()

    # Return the template
    return render_template('fin_accts/create_account.html',
                           account=account,
                           statements=statements,
                           categories=categories,
                           subcategories=subcategories)


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

            # Log the event to the events table
            db.execute(
                "INSERT INTO events (account, user_id, timestamp, before_values, after_values, edit_type) VALUES (?, ?, ?, ?, ?, ?)",
                (account_num, g.user['username'], datetime.now(), "Active", "Inactive", 3)
            )

            # Write the changes to the DB
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

            # Log the event to the events table
            db.execute(
                "INSERT INTO events (account, user_id, timestamp, before_values, after_values, edit_type) VALUES (?, ?, ?, ?, ?, ?)",
                (account_num, g.user['username'], datetime.now(), "Inactive", "Active", 4)
            )

            # Write the changes to the DB
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
@bp.route('/view_logs', methods=('GET',))
@login_required
def view_logs(account_num=None):
    # Get a handle on the DB
    db = get_db()

    # If account_num was specified, get all the events for this account number
    if account_num is not None:
        events = db.execute(
            "SELECT * FROM events WHERE account = ?", (account_num,)
        ).fetchall()
    # If there was no account number, this is a request to view ALL logs, so get them all
    else:
        events = db.execute(
            "SELECT * FROM events"
        ).fetchall()

    #######################################################
    # Turn the sqlite Row object into a Python dictionary #
    #######################################################
    # Create empty list to hold new dictionaries
    events2 = []
    # Loop through each event in the DB
    for event in events:
        # Temporary dictionary to hold each key/value
        temp_dict = {}
        # Go through each item in the Row object and assign it with the correct key to the temp_dict
        temp_dict['event_id'] = event[0]
        temp_dict["event_id"] = event[0]
        temp_dict["account"] = event[1]
        temp_dict["user_id"] = event[2]
        temp_dict["timestamp"] = datetime.fromisoformat(event[3]).strftime("%A, %B %d %X")
        temp_dict["edit_type"] = event[6]
        # The 'before_values' column can be: None, 'Active', 'Inactive', or contain a string which is a python list
        # Don't do anything to the data if 'before_values' isn't a list which has been dumped to a string
        if (event[4] is None) or (event[4] in ('Active', 'Inactive')):
            temp_dict['before_values'] = event[4]
        # If it is a list dumped to a string, convert it back to a list
        else:
            temp_dict['before_values'] = json.loads(event[4])
        # Same thing as above with 'before_values' except 'after_values' should never be None
        if event[5] in ('Active', 'Inactive'):
            temp_dict['after_values'] = event[5]
        else:
            temp_dict['after_values'] = json.loads(event[5])

        # Append this new dictionary to the list of dictionaries we're building
        events2.append(temp_dict)

    # Get the names of the account categories
    categories = db.execute("SELECT * FROM acct_categories").fetchall()
    # dictionary to hold results
    cat_dict = {}
    for count, category in enumerate(categories, start=1):
        cat_dict[count] = category['name']

    # Get the names of the account subcategories
    subcategories = db.execute("SELECT * FROM subcategories").fetchall()
    # dictionary to hold results
    subcat_dict = {}
    for count, subcategory in enumerate(subcategories, start=1):
        subcat_dict[count] = subcategory['name']

    # Get the names of the statements
    statements = db.execute("SELECT * FROM statements").fetchall()
    # dictionary to hold results
    statements_dict = {}
    for count, statement in enumerate(statements, start=1):
        statements_dict[count] = statement['name']

    return render_template('fin_accts/view_logs.html',
                           events=events2,
                           account_num=account_num,
                           categories=cat_dict,
                           subcategories=subcat_dict,
                           statements=statements_dict)

@bp.route('/email', methods=('GET', 'POST'))
@login_required
def email():
    """
    Allow an administrator to email other users
    """
    # Get a handle on the DB
    db = get_db()

    # Get users' names and email addresses
    db_info = db.execute(
        "SELECT first_name, last_name, email_address, role FROM users WHERE role = ? OR role = ? OR role = ?", (0, 1, 2)
    ).fetchall()

    # Put all entries into a dictionary
    email_info = {}
    for row in db_info:
        if row['role'] == 0:
            title = "Accountant"
        elif row['role'] == 1:
            title = "Manager"
        else:
            title = "Administrator"
        name = f"{row['first_name']} {row['last_name']} -- {title}"
        email_info[name] = row['email_address']

    if request.method == 'POST':
        user_email = request.form['user_email']
        subject = request.form['subject']
        message = f"New message from {g.user['first_name']} {g.user['last_name']}:<br><br><br>{request.form['message']}"
        send_email(user_email, subject, message)
    return render_template('fin_accts/email.html', email_info=email_info)
