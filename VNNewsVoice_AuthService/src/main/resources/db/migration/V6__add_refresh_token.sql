-- Add RefreshToken table for refresh token rotation
CREATE TABLE refresh_token (
    id          BIGSERIAL PRIMARY KEY,
    token       VARCHAR(255) NOT NULL UNIQUE,
    user_id     BIGINT NOT NULL REFERENCES userinfo(id) ON DELETE CASCADE,
    expires_at  TIMESTAMP NOT NULL,
    is_revoked  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refresh_token_token   ON refresh_token(token);
CREATE INDEX idx_refresh_token_user_id ON refresh_token(user_id);
