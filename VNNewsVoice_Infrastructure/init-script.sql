CREATE DATABASE news;
CREATE DATABASE testdb;
CREATE DATABASE article_db;
CREATE DATABASE auth_db;
CREATE DATABASE scheduler_db;
CREATE DATABASE comment_db;

-- Create admin user for RAG service
-- Password is set via POSTGRES_PASSWORD env var; never hardcode here.
CREATE USER admin WITH PASSWORD :'ADMIN_DB_PASSWORD';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE testdb TO admin;
ALTER DATABASE testdb OWNER TO admin;
