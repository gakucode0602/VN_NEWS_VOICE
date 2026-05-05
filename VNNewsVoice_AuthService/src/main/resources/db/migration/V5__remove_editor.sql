-- Remove Editor role and table — Editor role is no longer used.
-- Article processing (summary, audio) is now fully automated by the ML pipeline via RabbitMQ.

-- Remove seed editor user first (cascades to Editor table row)
DELETE FROM Editor WHERE user_id = (SELECT id FROM UserInfo WHERE username = 'editor');
DELETE FROM UserInfo WHERE username = 'editor';

-- Remove ROLE_EDITOR from Role table
DELETE FROM Role WHERE name = 'ROLE_EDITOR';

-- Drop the Editor table
DROP TABLE IF EXISTS Editor;
