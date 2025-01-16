PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS posts (submission TEXT, rank INTEGER, ts INTEGER);
CREATE UNIQUE INDEX IF NOT EXISTS post on posts (submission);
COMMIT;