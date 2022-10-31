

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
from appl_domain.db import get_db
from datetime import date, datetime, timedelta
from appl_domain.auth import login_required
import json

bp = Blueprint('journaling', __name__, url_prefix='/journaling')


@bp.route('/add_entry', methods=('GET', 'POST'))
@login_required
def add_entry():
    """
    Allows a user, manager, or admin to create a new journal entry
    """

    # Get a handle on the DB
    db = get_db()

    # Get a list of all accounts so we know which ones are available to credit/debit
    accounts = db.execute(
        "SELECT * FROM accounts"
    ).fetchall()

    if request.method == 'POST':
        # Empty dictionary to hold all the accounts that were credited and the value by which they were credited
        entry_credits = {}
        # Loop through 'credit_1_value' through 'credit_5_value' and add the entries which are > 0 to the dictionary
        for number in range(1, 6):
            value = request.form[f'credit_{number}_value'].replace(',', '').replace('.', '').replace('$', '')
            if (len(value) > 0) and (int(value) > 0):
                entry_credits[request.form[f'credit_{number}_account']] = int(value)
        # Dump the dictionary to a JSON object to be stored in the DB
        entry_credits = json.dumps(entry_credits)

        # Empty dictionary to hold all the accounts that were debited and the value by which they were debited
        entry_debits = {}
        # Loop through 'debit_1_value' through 'debit_5_value' and add the entries which are > 0 to the dictionary
        for number in range(1, 6):
            value = request.form[f'debit_{number}_value'].replace(',', '').replace('.', '').replace('$', '')
            if (len(value) > 0) and (int(value) > 0):
                entry_debits[request.form[f'debit_{number}_account']] = int(value)
        # Dump the dictionary to a JSON object to be stored in the DB
        entry_debits = json.dumps(entry_debits)

        # Get any attachments that the user uploaded
        if request.files['attachment'].filename:
            attachment_data = request.files['attachment'].read()
            attachment_name = request.files['attachment'].filename
        else:
            attachment_data = None
            attachment_name = None

        # Get entry's description
        description = request.form['description']

        db.execute(
            "INSERT INTO journal (status, date_submitted, user, credits, debits, attachment_data, attachment_name, "
            "description) VALUES (?, ? ,? ,? ,?, ?, ?, ?)",
            (0, datetime.now(), g.user['username'], entry_credits, entry_debits, attachment_data, attachment_name, description)
        )

        # Write the change
        db.commit()

    return render_template('journaling/add_entry.html', accounts=accounts)


@bp.route('/journal', methods=('GET',))
@login_required
def journal():
    # Get a handle on the DB
    db = get_db()

    # Get all approved entries
    approved_entries = db.execute(
        "SELECT * FROM journal WHERE status = ?", (1,)
    ).fetchall()

    # Get all pending entries
    pending_entries = db.execute(
        "SELECT * FROM journal WHERE status = ?", (0,)
    ).fetchall()

    # Get all rejected entries
    rejected_entries = db.execute(
        "SELECT * FROM journal WHERE status = ?", (-1,)
    ).fetchall()

    return render_template('journaling/journal.html', approved_entries=approved_entries, pending_entries=pending_entries, rejected_entries=rejected_entries)

@bp.route('/reject_entry')
@login_required
def reject_entry():
    if (g.user['role'] != 1) or (g.user['role'] != 2):
        abort(403)
    else:
        # Get the parameters from the request
        entry_idg.user['username']
        reject_reason = request.args.get('reject_reason')
        rejected_by = g.user['username']

        # Get a handle on the DB
        db = get_db()

        # Update the row for this ID number
        db.execute(
            "UPDATE journal SET status = ?, reject_reason = ?, approver = ? WHERE id_num = ?", (-1, reject_reason, rejected_by, entry_id)
        )

        # Write the change to the DB
        db.commit()

        return redirect(url_for('journaling.journal'))


@bp.route('/approve_entry')
@login_required
def approve_entry():
    # Get the parameters from the request
    entry_id = request.args.get('entry_id')
    approved_by = g.user['username']

    # Get a handle on the DB
    db = get_db()

    # Grab the journal entry
    this_entry = db.execute(
        "SELECT * from journal WHERE id_num = ?", (entry_id,)
    ).fetchone()

    # Update the row for this ID number
    db.execute(
        "UPDATE journal SET status = ?, approver = ? WHERE id_num = ?", (1, approved_by, entry_id)
    )

    # Write the change
    db.commit()

    # Get all of the different transactions for this journal entry
    credits = json.loads(this_entry['credits'])
    debits = json.loads(this_entry['debits'])

    # Update all the credits
    for account, value in credits:
        # Get the current balance
        current_balance = db.execute(
            "SELECT * FROM accounts WHERE acct_num = ?", (account,)
        ).fetchone()['balance']

        # Calculate the new balance
        new_bal = current_balance - value

        # Update the row
        db.execute(
            f"INSERT into ledger_{account} (date, description, credit, post_reference, balance) VALUES (?, ?, ?, ?, ?)",
            (this_entry['date'], this_entry['description'], value, this_entry['id_num'], new_bal)
        )

        # Write the change
        db.commit()

    # Update all the debits
    for account, value in debits:
        # Get current balance
        current_balance = db.execute(
            "SELECT * FROM accounts WHERE acct_num = ?", (account,)
        ).fetchone()['balance']

        # Calculate the new balance
        new_bal = current_balance + value

        # Update the row
        db.execute(
            f"INSERT INTO ledger_{account} (date, description, debit, post_reference, balance VALUES (?, ?, ?, ?, ?)",
            (this_entry['date'], this_entry['description'], value, this_entry['id_num'], new_bal)
        )

        # Write the change
        db.commit()

    return redirect(url_for('journaling.journal'))





@bp.route('/fix_db', methods=('GET', 'POST'))
@login_required
def fix_db():
    db = get_db()

    db.execute(
        "UPDATE journal SET status = ? WHERE id_num = ?", (0, 7)
    )

    # db.commit()
    #
    # db.execute(
    #     "CREATE TABLE journal (id_num INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, status INTEGER NOT NULL, date_submitted TEXT NOT NULL, user TEXT NOT NULL REFERENCES users(username), approver TEXT REFERENCES users(username), credits TEXT NOT NULL, debits TEXT NOT NULL, attachment BLOB, description TEXT, reject_reason TEXT)"
    # )

    db.commit()

    return "OK"