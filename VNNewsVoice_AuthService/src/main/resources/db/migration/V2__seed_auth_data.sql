-- Seed default roles
INSERT INTO Role(name) VALUES ('ROLE_ADMIN'),
                               ('ROLE_EDITOR'),
                               ('ROLE_READER');

-- Seed dev users
-- Default password for all seed users: '123456'
-- Value below is BCrypt(10) encoded. Change before production deployment.
INSERT INTO userinfo(username, password, avatar_url, email, created_at, birthday, is_active, address, phone_number, gender, role_id) VALUES
    ('admin',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 'https://example.com/avatar/admin.jpg',  'admin@example.com',  CURRENT_TIMESTAMP, '1990-01-01', TRUE, '123 Admin St',  '1234567890', 'Male',   (SELECT id FROM role WHERE name = 'ROLE_ADMIN')),
    ('editor', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 'https://example.com/avatar/editor.jpg', 'editor@example.com', CURRENT_TIMESTAMP, '1992-02-02', TRUE, '456 Editor Ave', '0987654321', 'Female', (SELECT id FROM role WHERE name = 'ROLE_EDITOR')),
    ('reader', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 'https://example.com/avatar/reader.jpg', 'reader@example.com', CURRENT_TIMESTAMP, '1995-03-03', TRUE, '789 Reader Blvd', '1122334455', 'Male',   (SELECT id FROM role WHERE name = 'ROLE_READER'));

INSERT INTO admin(user_id)  VALUES ((SELECT id FROM userinfo WHERE username = 'admin'));
INSERT INTO editor(user_id) VALUES ((SELECT id FROM userinfo WHERE username = 'editor'));
INSERT INTO reader(user_id) VALUES ((SELECT id FROM userinfo WHERE username = 'reader'));
