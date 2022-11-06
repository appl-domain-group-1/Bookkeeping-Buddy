from flask import Blueprint, g, redirect, render_template, request, url_for, abort, send_file
from appl_domain.db import get_db
from datetime import datetime
from appl_domain.auth import login_required
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch

bp = Blueprint('statements', __name__, url_prefix='/statements')


@bp.route('/balance_sheet', methods=('GET', 'POST'))
@login_required
def balance_sheet():
    # canvas = Canvas("balance_sheet.pdf", pagesize=LETTER)
    # canvas.setFont("Times-Roman", 20)
    # canvas.drawString(1 * inch, 10 * inch, "Balance Sheet")
    # canvas.setFontSize(14)
    # canvas.dr
    # canvas.save()

    # Get a handle on the DB
    db = get_db()

    # Get all asset account names, numbers and balances
    asset_accounts = db.execute(
        "SELECT acct_name, acct_num, balance FROM accounts WHERE acct_category = ?", (1,)
    ).fetchall()

    # Get all liability account names, numbers, and balances
    liability_accounts = db.execute(
        "SELECT acct_name, acct_num, balance FROM accounts WHERE acct_category = ?", (2,)
    ).fetchall()

    # Get all equity account names, numbers, and balances
    equity_accounts = db.execute(
        "SELECT acct_name, acct_num, balance FROM accounts WHERE acct_category = ?", (3,)
    ).fetchall()

    # Dictionary to hold the data
    balance_sheet_dict = {
        "Asset Accounts": [],
        "Liability Accounts": [],
        "Equity Accounts": []
    }

    # Walk the data from each of the account types into the dictionary
    for account in asset_accounts:
        balance_sheet_dict["Asset Accounts"].append([account['acct_num'], account['acct_name'], account['balance']])
    for account in liability_accounts:
        balance_sheet_dict["Liability Accounts"].append([account['acct_num'], account['acct_name'], account['balance']])
    for account in equity_accounts:
        balance_sheet_dict["Equity Accounts"].append([account['acct_num'], account['acct_name'], account['balance']])

    return render_template('statements/balance_sheet.html', data=balance_sheet_dict)

