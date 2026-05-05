-- Add first_name and last_name columns to UserInfo (mirrors original V10)
ALTER TABLE userinfo
    ADD COLUMN IF NOT EXISTS first_name VARCHAR(255);

ALTER TABLE userinfo
    ADD COLUMN IF NOT EXISTS last_name VARCHAR(255);
