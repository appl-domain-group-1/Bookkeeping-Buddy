DROP TABLE IF EXISTS users;

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
  suspend_start_date TEXT,
  suspend_end_date TEXT,
  creation_date TEXT NOT NULL,
  first_pet TEXT NOT NULL,
  city_born TEXT NOT NULL,
  year_graduated_hs INTEGER NOT NULL
);