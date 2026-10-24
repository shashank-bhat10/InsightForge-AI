# Database

PostgreSQL is the application database. Set `DATABASE_URL` in root `.env`; see the README for database creation and startup. SQLAlchemy uses pooled connections with pre-ping and disables SQL echo to avoid writing sensitive query parameters into ordinary logs.

| Table | Main fields | Relationship |
| --- | --- | --- |
| `users` | id, full_name, unique email, hashed_password | Owns datasets/conversations/chats |
| `datasets` | id, filename, original_filename, type, size, file_path, user_id, created_at | Metadata only; rows remain on disk |
| `conversations` | id, title, user_id, created_at | Owns chats |
| `chat_history` | id, prompt, response, user_id, conversation_id, created_at | Belongs to a user and conversation |

Ownership filters include both ID and current-user ID. Conversation deletion removes chats through ORM cascades. Dataset deletion removes its file after metadata deletion. There is no user-deletion endpoint, migration history, or backup tool.

Missing tables are created at app startup or explicitly with `python -m app.database.init_db` from `backend/` using the root virtual environment. `create_all` cannot update an existing table definition.

Default tests use SQLite in memory. Optional PostgreSQL tests create random `insightforge_test_...` schemas and remove only those schemas afterward; they do not operate on application tables. The test user needs schema creation rights. Never point test credentials at a production database.
