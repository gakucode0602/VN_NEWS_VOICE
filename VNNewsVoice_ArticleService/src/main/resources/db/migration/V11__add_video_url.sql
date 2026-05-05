-- V11: Add video_url column to article table for AI-generated video (Veo integration)
-- Safe to rollback: nullable column, old code simply ignores the extra column (ddl-auto=validate)
ALTER TABLE article ADD COLUMN video_url VARCHAR(500);
