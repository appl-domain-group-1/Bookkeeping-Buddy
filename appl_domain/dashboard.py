from appl_domain.db import get_db


def get_assets():
    # Get a handle on the db
    db = get_db()

    # Get current assets
    current_assets = db.execute(
        "SELECT SUM(balance) as balance FROM accounts WHERE acct_category = ?", (1,)
    ).fetchone()['balance']

    return current_assets


def get_liabilities():
    # Get a handle on the db
    db = get_db()

    # Get current liabilities
    current_liabilities = db.execute(
        "SELECT SUM(balance) as balance FROM accounts WHERE acct_category = ?", (2,)
    ).fetchone()['balance']

    return current_liabilities


def get_current_ratio():
    """
    Returns (current assets) / (current liabilities)
    """
    return get_assets() / get_liabilities()


def get_working_capital():
    """
    Returns (inventory) / (accounts receivable)
    """
    # Get a handle on the db
    db = get_db()

    # Get accounts receivable
    accounts_receivable = db.execute(
        "SELECT balance FROM accounts WHERE acct_name = ?", ("Accounts Receivable",)
    ).fetchone()['balance']

    # Get inventory
    inventory = db.execute(
        "SELECT balance FROM accounts WHERE acct_name = ?", ("Inventory",)
    ).fetchone()['balance']

    return inventory / accounts_receivable


def get_debt_to_equity():
    """
    Returns (total liabilities) / (total assets)
    """

    return get_liabilities() / get_assets()


def get_equity_ratio():
    """
    Returns (total equity) / (total assets)
    """
    # Get a handle on the db
    db = get_db()

    # Get total equity
    total_equity = db.execute(
        "SELECT SUM(balance) as balance FROM accounts WHERE acct_category = ?", (3,)
    ).fetchone()['balance']

    return total_equity / get_assets()


def get_journal_entries(username):
    # Get a handle on the db
    db = get_db()

    # Get the entries
    entries = db.execute(
        "SELECT * FROM journal WHERE user = ? AND status = ?", (username, 0)
    ).fetchall()

    return entries


def get_next_suspension(username):
    # Get a handle on the db
    db = get_db()

    suspend_dates = db.execute(
        "SELECT suspend_start_date, suspend_end_date FROM users WHERE username = ?", (username,)
    ).fetchone()

    suspend_start = suspend_dates['suspend_start_date']
    suspend_end = suspend_dates['suspend_end_date']

    return (suspend_start, suspend_end)
