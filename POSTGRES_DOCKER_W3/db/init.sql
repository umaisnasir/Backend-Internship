CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    title TEXT NOT NULL
        CHECK (BTRIM(title) <> ''),
    done BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO tasks (title, done)
VALUES
    ('Learn FastAPI', TRUE),
    ('Build a CRUD API', FALSE),
    ('Publish it to GitHub', FALSE);