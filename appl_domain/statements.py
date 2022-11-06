from flask import Blueprint, g, redirect, render_template, request, url_for, abort, send_file
from appl_domain.db import get_db
from datetime import datetime
from appl_domain.auth import login_required
from appl_domain.email_tasks import send_email

bp = Blueprint('statements', __name__, url_prefix='/statements')


@bp.route('/balance_sheet', methods=('GET', 'POST'))
@login_required
def balance_sheet():
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

    # Walk the data from each of the account types into the dictionary and calculate totals for each category
    total_assets = 0
    total_liabilities = 0
    total_equity = 0
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
                           total_equity=total_equity)

