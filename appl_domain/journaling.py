

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
                entry_credits[request.form[f'credit_{number}_account']] = value
        # Dump the dictionary to a JSON object to be stored in the DB
        entry_credits = json.dumps(entry_credits)

        # Empty dictionary to hold all the accounts that were debited and the value by which they were debited
        entry_debits = {}
        # Loop through 'debit_1_value' through 'debit_5_value' and add the entries which are > 0 to the dictionary
        for number in range(1, 6):
            value = request.form[f'debit_{number}_value'].replace(',', '').replace('.', '').replace('$', '')
            if (len(value) > 0) and (int(value) > 0):
                entry_debits[request.form[f'debit_{number}_account']] = value
        # Dump the dictionary to a JSON object to be stored in the DB
        entry_debits = json.dumps(entry_debits)

        # Get any attachments that the user uploaded
        if request.files['attachment'].filename:
            attachment = request.files['attachment'].read()
        else:
            attachment = None

        # Get entry's description
        description = request.form['description']

        db.execute(
            "INSERT INTO journal (status, date_submitted, user, credits, debits, attachment, description) "
            "VALUES (?, ? ,? ,? ,?, ?, ?)",
            (0, datetime.now(), g.user['username'], entry_credits, entry_debits, attachment, description)
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
    entry_id = request.args.get('entry_id')
    reject_reason = request.args.get('reject_reason')
    print(f"Entry ID: {entry_id}")
    print(f"Reject reason: {reject_reason}")
    return redirect(url_for('journaling.journal'))

@bp.route('/fix_db', methods=('GET', 'POST'))
@login_required
def fix_db():
    db = get_db()

    db.execute(
        "DROP TABLE IF EXISTS journal;"
    )

    db.commit()

    db.execute(
        "CREATE TABLE journal (id_num INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, status INTEGER NOT NULL, date_submitted TEXT NOT NULL, user TEXT NOT NULL REFERENCES users(username), approver TEXT REFERENCES users(username), credits TEXT NOT NULL, debits TEXT NOT NULL, attachment BLOB, description TEXT, reject_reason TEXT)"
    )

    db.commit()

    return "OK"