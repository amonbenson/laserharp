CREATE TABLE calibration (
    `id` SERIAL PRIMARY KEY CHECK (id = 1),
    `data` JSONB NOT NULL
);

CREATE TABLE settings (
    `id` SERIAL PRIMARY KEY,
    `key` TEXT NOT NULL UNIQUE,
    `value` TEXT NOT NULL
);
