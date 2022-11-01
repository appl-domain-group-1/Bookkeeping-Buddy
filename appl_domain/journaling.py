from flask import Blueprint, g, redirect, render_template, request, url_for, abort, send_file
from appl_domain.db import get_db
from datetime import datetime
from appl_domain.auth import login_required
import json
from io import BytesIO

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
    # Convert each entry to a Python dictionary
    approved_entries2 = []
    for entry in approved_entries:
        # Temporary dictionary to hold each key/value
        temp_dict = {}
        # Go through each item in the Row object and assign it with the correct key to the temp_dict
        temp_dict['id_num'] = entry[0]
        temp_dict['status'] = entry[1]
        temp_dict['date_submitted'] = datetime.fromisoformat(entry[2]).strftime("%A, %B %d %X")
        temp_dict['user'] = entry[3]
        temp_dict['approver'] = entry[4]
        if entry[5] is not None:
            temp_dict['credits'] = json.loads(entry[5])
        else:
            temp_dict['credits'] = None
        if entry[6] is not None:
            temp_dict['debits'] = json.loads(entry[6])
        else:
            temp_dict['debits'] = None
        temp_dict['attachment_name'] = entry[8]
        temp_dict['description'] = entry[9]

        # Append this new dictionary to the list of dictionaries
        approved_entries2.append(temp_dict)


    # Get all pending entries
    pending_entries = db.execute(
        "SELECT * FROM journal WHERE status = ?", (0,)
    ).fetchall()
    # Convert each entry to a Python dictionary
    pending_entries2 = []
    for entry in pending_entries:
        # Temporary dictionary to hold each key/value
        temp_dict = {}
        # Go through each item in the Row object and assign it with the correct key to the temp_dict
        temp_dict['id_num'] = entry[0]
        temp_dict['status'] = entry[1]
        temp_dict['date_submitted'] = datetime.fromisoformat(entry[2]).strftime("%A, %B %d %X")
        temp_dict['user'] = entry[3]
        temp_dict['approver'] = entry[4]
        if entry[5] is not None:
            temp_dict['credits'] = json.loads(entry[5])
        else:
            temp_dict['credits'] = None
        if entry[6] is not None:
            temp_dict['debits'] = json.loads(entry[6])
        else:
            temp_dict['debits'] = None
        temp_dict['attachment_name'] = entry[8]
        temp_dict['description'] = entry[9]

        # Append this new dictionary to the list of dictionaries
        pending_entries2.append(temp_dict)


    # Get all rejected entries
    rejected_entries = db.execute(
        "SELECT * FROM journal WHERE status = ?", (-1,)
    ).fetchall()
    # Convert each entry to a Python dictionary
    rejected_entries2 = []
    for entry in rejected_entries:
        # Temporary dictionary to hold each key/value
        temp_dict = {}
        # Go through each item in the Row object and assign it with the correct key to the temp_dict
        temp_dict['id_num'] = entry[0]
        temp_dict['status'] = entry[1]
        temp_dict['date_submitted'] = datetime.fromisoformat(entry[2]).strftime("%A, %B %d %X")
        temp_dict['user'] = entry[3]
        temp_dict['approver'] = entry[4]
        if entry[5] is not None:
            temp_dict['credits'] = json.loads(entry[5])
        else:
            temp_dict['credits'] = None
        if entry[6] is not None:
            temp_dict['debits'] = json.loads(entry[6])
        else:
            temp_dict['debits'] = None
        temp_dict['attachment_name'] = entry[8]
        temp_dict['description'] = entry[9]
        temp_dict['reject_reason'] = entry[10]

        # Append this new dictionary to the list of dictionaries
        rejected_entries2.append(temp_dict)

    return render_template('journaling/journal.html', approved_entries=approved_entries2, pending_entries=pending_entries2, rejected_entries=rejected_entries2)

@bp.route('/reject_entry')
@login_required
def reject_entry():
    # If the user is not a manager or admin, boot them
    if g.user['role'] not in (1, 2):
        abort(403)
    else:
        # Get the parameters from the request
        entry_id = request.args.get('entry_id')
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
    for account, value in credits.items():
        # Get the current balance
        current_balance = db.execute(
            "SELECT * FROM accounts WHERE acct_num = ?", (account,)
        ).fetchone()['balance']

        # Calculate the new balance
        new_bal = current_balance - value

        # Update the row in the ledger
        db.execute(
            f"INSERT into ledger_{account} (date, description, credit, post_reference, balance) VALUES (?, ?, ?, ?, ?)",
            (this_entry['date_submitted'], this_entry['description'], value, this_entry['id_num'], new_bal)
        )

        # Write the change
        db.commit()

        # Update the balance in the account table
        db.execute(
            "UPDATE accounts SET balance = ? WHERE acct_num = ?", (new_bal, account)
        )

        # Write the change
        db.commit()

    # Update all the debits
    for account, value in debits.items():
        # Get current balance
        current_balance = db.execute(
            "SELECT * FROM accounts WHERE acct_num = ?", (account,)
        ).fetchone()['balance']

        # Calculate the new balance
        new_bal = current_balance + value

        # Update the row
        db.execute(
            f"INSERT INTO ledger_{account} (date, description, debit, post_reference, balance) VALUES (?, ?, ?, ?, ?)",
            (this_entry['date_submitted'], this_entry['description'], value, this_entry['id_num'], new_bal)
        )

        # Write the change
        db.commit()

        # Update the balance in the account table
        db.execute(
            "UPDATE accounts SET balance = ? WHERE acct_num = ?", (new_bal, account)
        )

        # Write the change
        db.commit()

    return redirect(url_for('journaling.journal'))

@bp.route('/get_attachment')
@login_required
def get_attachment():
    entry_id = request.args.get('entry_id')

    # Get a handle on the DB
    db = get_db()

    # Get the file's raw data and filename
    file_info = db.execute(
        "SELECT attachment_data, attachment_name FROM journal WHERE id_num = ?", (entry_id,)
    ).fetchone()

    # Get file data and store it in a temporary byte buffer
    file_data = file_info['attachment_data']
    temp_file = BytesIO()
    temp_file.write(file_data)
    # Seek back to the beginning of the file so it's ready to download
    temp_file.seek(0)

    # Get the filename of the new file
    file_name = file_info['attachment_name']

    # Send the file to the user
    return send_file(temp_file, download_name=file_name)
