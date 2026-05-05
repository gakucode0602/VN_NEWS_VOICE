-- Remove editor-related columns from Article table
-- These fields are no longer needed since the ML pipeline (RabbitMQ → ML Service)
-- automatically generates summary and audio, removing the need for a human editor role.
ALTER TABLE Article DROP COLUMN IF EXISTS editor_id;
ALTER TABLE Article DROP COLUMN IF EXISTS is_being_edited;
ALTER TABLE Article DROP COLUMN IF EXISTS edit_started_at;
