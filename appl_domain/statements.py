from flask import Blueprint, g, redirect, render_template, request, url_for, abort, send_file, flash
from appl_domain.db import get_db
from appl_domain.auth import login_required
from appl_domain.email_tasks import send_email

bp = Blueprint('statements', __name__, url_prefix='/statements')


def get_updated_ledger_entries(start_date, end_date, list_of_accounts):
    # Get a handle on the db
    db = get_db()

    temp_total = 0
    temp_accounts = []

    for account in list_of_accounts:
        # Get the account number
        account_num = account['acct_num']

        # Get the last transaction in the ledger between the user's dates
        query = f"SELECT MAX(date) as date, balance from ledger_{account_num} WHERE date(date) BETWEEN date('{start_date}') AND date('{end_date}')"
        last_entry = db.execute(query).fetchone()

        # Update the total with this dollar amount
        if last_entry and last_entry['balance']:
            temp_total = temp_total + last_entry['balance']

        # Update the new list with accounts that have transactions within the specified date window
        if last_entry and last_entry['date']:
            temp_accounts.append(
                {
                    'acct_name': account['acct_name'],
                    'balance': last_entry['balance'],
                    'acct_subcategory': account['acct_subcategory'],
                    'debit': account['debit']
                }
            )

    return temp_total, temp_accounts


@bp.route('/balance_sheet', methods=('GET', 'POST'))
@login_required
def balance_sheet():
    # Placeholders for start_date and end_date. Not used in GET requests
    start_date = None
    end_date = None

    # Start the counts for each account type at 0
    total_assets = 0
    total_liabilities = 0
    total_equity = 0

    # Get a handle on the DB
    db = get_db()

    # Get all asset account names, numbers and balances
    asset_accounts = db.execute(
        "SELECT acct_name, acct_num, balance, acct_subcategory FROM accounts WHERE acct_category = ?", (1,)
    ).fetchall()

    # Get all liability account names, numbers, and balances
    liability_accounts = db.execute(
        "SELECT acct_name, acct_num, balance, acct_subcategory FROM accounts WHERE acct_category = ?", (2,)
    ).fetchall()

    # Get all equity account names, numbers, and balances
    equity_accounts = db.execute(
        "SELECT acct_name, acct_num, balance, acct_subcategory FROM accounts WHERE acct_category = ?", (3,)
    ).fetchall()

    # Get all subcategories
    asset_subcategories = db.execute(
        "SELECT * from subcategories WHERE category = ?", (1,)
    ).fetchall()
    liability_subcategories = db.execute(
        "SELECT * from subcategories WHERE category = ?", (2,)
    ).fetchall()
    equity_subcategories = db.execute(
        "SELECT * from subcategories WHERE category = ?", (3,)
    ).fetchall()

    if request.method == 'POST':
        # Get the end date that the user wants to focus on
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Get updated totals and list of accounts for the user's date range
        total_assets, asset_accounts = get_updated_ledger_entries(start_date, end_date, asset_accounts)
        total_liabilities, liability_accounts = get_updated_ledger_entries(start_date, end_date, liability_accounts)
        total_equity, equity_accounts = get_updated_ledger_entries(start_date, end_date, equity_accounts)

    if request.method == 'GET':
        # Walk the data from each of the account types into the dictionary and calculate totals for each category
        for account in asset_accounts:
            total_assets = total_assets + account['balance']
        for account in liability_accounts:
            total_liabilities = total_liabilities + account['balance']
        for account in equity_accounts:
            total_equity = total_equity + account['balance']

    return render_template('statements/balance_sheet.html',
                           asset_subcategories=asset_subcategories,
                           asset_accounts=asset_accounts,
                           liability_subcategories=liability_subcategories,
                           liability_accounts=liability_accounts,
                           equity_subcategories=equity_subcategories,
                           equity_accounts=equity_accounts,
                           total_assets=total_assets,
                           total_liabilities=total_liabilities,
                           total_equity=total_equity,
                           start_date=start_date,
                           end_date=end_date)


@bp.route('/income_statement', methods=('GET', 'POST'))
@login_required
def income_statement():
    # Placeholders for start_date and end_date. Not used in GET requests
    start_date = None
    end_date = None

    # Get a handle on the db
    db = get_db()

    revenue_accounts = db.execute(
        "SELECT * from accounts WHERE acct_category = 4"
    ).fetchall()

    expense_accounts = db.execute(
        "SELECT * FROM accounts WHERE acct_category = 5"
    ).fetchall()

    if request.method == 'POST':
        # Get the end date that the user wants to focus on
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Get all the ledger entries for revenue accounts
        total_revenue, revenue_accounts = get_updated_ledger_entries(start_date, end_date, revenue_accounts)

        # Get all the ledger entries for expense accounts
        total_expenses, expense_accounts = get_updated_ledger_entries(start_date, end_date, expense_accounts)

    if request.method == 'GET':
        total_revenue = 0
        total_expenses = 0
        for account in revenue_accounts:
            total_revenue = total_revenue + account['balance']
        for account in expense_accounts:
            total_expenses = total_expenses + account['balance']

    return render_template('statements/income.html',
                           revenue_accounts=revenue_accounts,
                           expense_accounts=expense_accounts,
                           total_revenue=total_revenue,
                           total_expenses=total_expenses,
                           start_date=start_date,
                           end_date=end_date)


@bp.route('/retained_earnings', methods=('GET', 'POST'))
@login_required
def retained_earnings():
    # Placeholders for start_date and end_date. Not used in GET requests
    start_date = None
    end_date = None

    # Get a handle on the db
    db = get_db()

    # Start the counts for each account type at 0
    total_revenue = 0
    total_expenses = 0

    revenue_accounts = db.execute(
        "SELECT * from accounts WHERE acct_category = 4"
    ).fetchall()

    expense_accounts = db.execute(
        "SELECT * FROM accounts WHERE acct_category = 5"
    ).fetchall()

    re_accounts = db.execute(
        "SELECT * FROM accounts WHERE acct_category = ? AND acct_subcategory = ?", (3, 6)
    ).fetchall()

    dividends_accounts = db.execute(
        "SELECT * from accounts where acct_category = ? AND acct_subcategory = ?", (3, 5)
    ).fetchall()

    if request.method == 'POST':
        # Get the end date that the user wants to focus on
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Get updated information for the report
        total_revenue, revenue_accounts = get_updated_ledger_entries(start_date, end_date, revenue_accounts)
        total_expenses, expense_accounts = get_updated_ledger_entries(start_date, end_date, expense_accounts)
        _, re_accounts = get_updated_ledger_entries(start_date, end_date, re_accounts)
        _, dividends_accounts = get_updated_ledger_entries(start_date, end_date, dividends_accounts)

    if request.method == 'GET':
        for account in revenue_accounts:
            total_revenue = total_revenue + account['balance']
        for account in expense_accounts:
            total_expenses = total_expenses + account['balance']

    return render_template('statements/retained_earnings.html',
                           total_revenue=total_revenue,
                           total_expenses=total_expenses,
                           re_accounts=re_accounts,
                           dividends_accounts=dividends_accounts,
                           start_date=start_date,
                           end_date=end_date)


@bp.route('/trial_balance', methods=('GET', 'POST'))
@login_required
def trial_balance():
    # Placeholders for start_date and end_date. Not used in GET requests
    start_date = None
    end_date = None

    # Get a handle on the DB
    db = get_db()

    # Get all accounts
    accounts = db.execute(
        "SELECT * FROM accounts"
    ).fetchall()

    # Get all categories
    categories = db.execute(
        "SELECT * FROM acct_categories"
    ).fetchall()

    # Get all subcategories
    subcategories = db.execute(
        "SELECT * FROM subcategories"
    ).fetchall()

    if request.method == 'POST':
        # Get the end date that the user wants to focus on
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Get updated information for the report
        _, accounts = get_updated_ledger_entries(start_date, end_date, accounts)

    return render_template('statements/trial_balance.html',
                           accounts=accounts,
                           categories=categories,
                           subcategories=subcategories,
                           start_date=start_date,
                           end_date=end_date)


@bp.route('/email_statement', methods=('GET', 'POST'))
@login_required
def email_statement():
    """
    Allow a user to email a specific statement
    """
    # Get a handle on the DB
    db = get_db()

    # Get users' names and email addresses
    admins = db.execute(
        "SELECT first_name, last_name, email_address FROM users WHERE role = ?", (2,)
    ).fetchall()
    managers = db.execute(
        "SELECT first_name, last_name, email_address FROM users WHERE role = ?", (1,)
    ).fetchall()
    users = db.execute(
        "SELECT first_name, last_name, email_address FROM users WHERE role = ?", (0,)
    ).fetchall()

    # Get the parameters from the form
    statement = request.args.get('statement')
    included_message = request.args.get('included_message')

    if request.method == 'POST':
        user_email = request.form['user_email']
        subject = request.form['subject']
        message = f"New message from {g.user['first_name']} {g.user['last_name']}:<br><br><br>{request.form['message']}"
        # Add on the HTML for the statement
        message = message + '<br><br><br>' + included_message
        # Send the message
        send_email(user_email, subject, message)

        # Tell the user that the message was sent
        flash("Message sent!")

    return render_template('fin_accts/email.html',
                           included_message=included_message,
                           statement=statement,
                           admins=admins,
                           managers=managers,
                           users=users)
