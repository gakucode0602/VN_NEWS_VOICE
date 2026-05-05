-- Article Service Database Schema
-- Note: editor_id is BIGINT with no FK (cross-service reference to UserInfo.id from auth_db)
-- Note: ArticleLike.reader_id is BIGINT with no FK (stores UserInfo.id extracted from JWT)

CREATE TABLE Generator (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    logo_url VARCHAR(255),
    url VARCHAR(255) NOT NULL UNIQUE,
    last_time_crawled TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Category (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE Article (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    generator_id BIGINT NOT NULL,
    published_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    audio_url VARCHAR(255),
    summary TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    -- editor_id: cross-service reference to UserInfo.id in auth_db (no FK constraint)
    editor_id BIGINT,
    category_id BIGINT,
    slug VARCHAR(255) NOT NULL UNIQUE,
    FOREIGN KEY (category_id) REFERENCES Category(id) ON DELETE SET NULL,
    FOREIGN KEY (generator_id) REFERENCES Generator(id) ON DELETE CASCADE
);

CREATE TABLE ArticleBlock (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT NOT NULL,
    order_index INT NOT NULL,
    type VARCHAR(50) NOT NULL,
    content TEXT,
    text TEXT,
    tag TEXT,
    src TEXT,
    alt TEXT,
    caption TEXT,
    FOREIGN KEY (article_id) REFERENCES Article(id) ON DELETE CASCADE
);

CREATE TABLE ArticleLike (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT NOT NULL,
    -- reader_id: cross-service reference to UserInfo.id in auth_db (no FK constraint)
    reader_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES Article(id) ON DELETE CASCADE
);
