-- Add avatar_public_id column to UserInfo (mirrors original V9)
ALTER TABLE userinfo
    ADD COLUMN avatar_public_id VARCHAR(255);

COMMENT ON COLUMN userinfo.avatar_public_id IS 'Public ID of the avatar image on Cloudinary';
