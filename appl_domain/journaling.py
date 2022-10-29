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
