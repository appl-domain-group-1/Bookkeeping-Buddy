/* Enable foreign key support */
PRAGMA foreign_keys = ON;

/* Table to store user accounts */
CREATE TABLE users (
  username TEXT PRIMARY KEY UNIQUE,
  email_address TEXT NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  active INTEGER NOT NULL,
  role INTEGER NOT NULL,
  picture BLOB,
  password TEXT NOT NULL,
  address TEXT NOT NULL,
  DOB TEXT NOT NULL,
  old_passwords TEXT NOT NULL,
  password_refresh_date TEXT NOT NULL,
  incorrect_login_attempts INTEGER NOT NULL,
  suspend_start_date TEXT,
  suspend_end_date TEXT,
  creation_date TEXT NOT NULL,
  first_pet TEXT NOT NULL,
  city_born TEXT NOT NULL,
  year_graduated_hs INTEGER NOT NULL
);

/* Contains different financial account categories */
CREATE TABLE acct_categories (
    /* name of this category */
    name TEXT NOT NULL,
    /* unique identifier for this category */
    number INTEGER PRIMARY KEY UNIQUE
);

/* Contains different financial statements which may be collected */
CREATE TABLE statements (
    /* unique identifier for this statement */
    number INTEGER PRIMARY KEY UNIQUE,
    /* name of this statement */
    name TEXT NOT NULL
);

/* Contains financial accounts */
CREATE TABLE accounts (
    acct_name TEXT NOT NULL UNIQUE,
    acct_num INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
    acct_desc TEXT,
    /* category to which this account belongs. Must be in
       the acct_categories table */
    acct_category INTEGER NOT NULL REFERENCES acct_categories(number),
    /* Account subcategory. Must be in subcategory table */
    acct_subcategory INTEGER NOT NULL REFERENCES subcategories(id_num),
    /* debit acct == 1, credit acct == 0 */
    debit INTEGER NOT NULL,
    /* stored as cents (no decimals) */
    initial_bal INTEGER NOT NULL,
    /* stored as cents (no decimals) */
    balance INTEGER NOT NULL,
    /* string in the format YYYY-MM-DD */
    date_created TEXT NOT NULL,
    /* must have been created by someone in users table */
    created_by TEXT NOT NULL REFERENCES users(username),
    /* financial statement which uses this account */
    statement INTEGER NOT NULL REFERENCES statements(number),
    /* Comment about this account */
    comment TEXT,
    /* Account active? 0 == inactive, 1 == active */
    active INTEGER DEFAULT 0 NOT NULL
);

/* Contains all changes to financial accounts */
-- DROP TABLE IF EXISTS events;
CREATE TABLE events (
    /* Unique identifier for each event logged */
    event_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
    /* Account associated with the change */
    account INTEGER NOT NULL REFERENCES accounts(acct_num),
    /* User who made the change */
    user_id TEXT NOT NULL REFERENCES users(username),
    /* date and time when the change was committed */
    timestamp TEXT NOT NULL,
    /* JSON object of all account values before change */
    before_values TEXT,
    /* JSON object of all account values after change */
    after_values TEXT NOT NULL,
    /* Type of edit to the table (New account, deactivate, edit, etc.)
        Values:
            New account: 1
            Existing account edit: 2
            Deactivate account: 3
            Activate account: 4 */
    edit_type INTEGER NOT NULL
);

/* Contains subcategories for all financial account categories */
-- DROP TABLE IF EXISTS subcategories;
CREATE TABLE subcategories (
    /* Unique ID for this subcategory */
    id_num INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
    /* Which category does this subcategory belong to? */
    category INTEGER REFERENCES acct_categories(number),
    /* Name of this subcategory */
    name TEXT NOT NULL
)