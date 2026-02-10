# scripts/init-db.sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema for better organization (optional but professional)
CREATE SCHEMA IF NOT EXISTS fintech;