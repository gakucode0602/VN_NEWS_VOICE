-- Auth Service schema: Role, UserInfo, UserProvider, Admin, Editor, Reader, Notification, NotificationRole

CREATE TABLE Role (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE UserInfo (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(255),
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    birthday DATE,
    is_active BOOLEAN DEFAULT TRUE,
    address TEXT,
    phone_number VARCHAR(20),
    gender VARCHAR(10),
    role_id BIGINT,
    FOREIGN KEY (role_id) REFERENCES Role(id)
);

CREATE TABLE UserProvider (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    provider_id VARCHAR(100) NOT NULL,
    provider_type VARCHAR(50) NOT NULL,
    provider_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES UserInfo(id)
);

CREATE TABLE Admin (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES UserInfo(id)
);

CREATE TABLE Editor (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES UserInfo(id)
);

CREATE TABLE Reader (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES UserInfo(id)
);

CREATE TABLE Notification (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES UserInfo(id)
);

CREATE TABLE NotificationRole (
    id BIGSERIAL PRIMARY KEY,
    notification_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    FOREIGN KEY (notification_id) REFERENCES Notification(id),
    FOREIGN KEY (role_id) REFERENCES Role(id)
);
