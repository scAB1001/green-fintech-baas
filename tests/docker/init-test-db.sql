-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema
CREATE SCHEMA IF NOT EXISTS fintech;

-- Create a test user with limited permissions (optional)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'test_user') THEN
    CREATE USER test_user WITH PASSWORD 'test_password';
    GRANT CONNECT ON DATABASE green_fintech_test TO test_user;
    GRANT USAGE ON SCHEMA public TO test_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO test_user;
  END IF;
END
$$;
