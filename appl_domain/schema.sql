DROP TABLE IF EXISTS users;

CREATE TABLE users (
  username TEXT PRIMARY KEY UNIQUE,
  email_address TEXT NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  active INTEGER NOT NULL,
  picture BLOB,
  password text NOT NULL,
  address TEXT NOT NULL,
  DOB TEXT NOT NULL,
  old_passwords BLOB NOT NULL,
  password_refresh_date TEXT NOT NULL,
  suspend_start_date TEXT NOT NULL,
  suspend_end_date TEXT NOT NULL,
  creation_date TEXT NOT NULL
);