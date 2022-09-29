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
    acct_name TEXT NOT NULL,
    acct_num INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
    acct_desc TEXT,
    /* category to which this account belongs. Must be in
       the acct_categories table */
    acct_category INTEGER NOT NULL REFERENCES acct_categories(number),
    /* Account subcategory */
    acct_subcategory INTEGER NOT NULL,
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
    /* Comment about this table */
    comment TEXT
);