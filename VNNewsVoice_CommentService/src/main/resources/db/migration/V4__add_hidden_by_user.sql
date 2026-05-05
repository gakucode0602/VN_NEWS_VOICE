-- V4: Add hidden_by_user flag to support hiding comments when the author's account is locked.
-- When a user is locked, their comments are hidden (hidden_by_user = true).
-- When unlocked, comments are restored (hidden_by_user = false).
ALTER TABLE comment ADD COLUMN IF NOT EXISTS hidden_by_user BOOLEAN NOT NULL DEFAULT FALSE;
