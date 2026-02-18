-- This runs automatically on first container start
-- because it's mounted in /docker-entrypoint-initdb.d/

-- Enable UUID extension (required for our models)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema for better organization
CREATE SCHEMA IF NOT EXISTS fintech;

-- Set timezone
ALTER DATABASE postgres SET timezone TO 'UTC';

-- Create a read-only user for analytics (optional, sophisticated touch)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'analytics_user') THEN
    CREATE USER analytics_user WITH PASSWORD 'analytics_password';
    GRANT CONNECT ON DATABASE green_fintech TO analytics_user;
    GRANT USAGE ON SCHEMA fintech TO analytics_user;
    GRANT SELECT ON ALL TABLES IN SCHEMA fintech TO analytics_user;
  END IF;
END
$$;

-- Log initialization complete
DO $$
BEGIN
  RAISE NOTICE 'Database initialization complete at %', NOW();
END
$$;
