# API reference

Start the server using the root README. Interactive OpenAPI documentation is at `/docs`; machine-readable schema is `/openapi.json`.

## Authentication

`POST /register` accepts JSON `full_name`, `email`, `password`. Names are 1–100 characters; passwords are 8–72 characters and at most 72 UTF-8 bytes. Duplicate emails return 400.

`POST /login` uses `application/x-www-form-urlencoded`, with the email in `username`. It returns `access_token` and `token_type`. Supply `Authorization: Bearer <token>` on protected routes. Invalid credentials/tokens return 401.

## Datasets and analytics

`POST /api/v1/datasets/` accepts multipart field `file` with `.csv`, `.xlsx`, or `.xls`. Files must parse and contain data rows. Default maximum is 10 MiB. Metadata includes ID, original name, generated name, path, byte count, owner, and creation time. `GET` on the same collection lists your datasets. `GET` and `DELETE /api/v1/datasets/{id}` operate only on owned resources; deletion also removes the upload.

`GET /api/v1/analytics/{id}/` operations:

| Suffix | Response |
| --- | --- |
| `preview` | First 10 rows as records; missing values become null |
| `summary` | Row/column counts, names, dtypes, missing counts |
| `statistics` | Numeric count, mean, median, min, max, standard deviation |
| `insights` | Deterministic summary sentences |
| `grouped-analysis` | Category/numeric counts, means, totals; top 20 groups, at most 50 unique categories |
| `quality` | Missingness, duplicates, constants, categorical inconsistencies, IQR outliers, heuristic score |
| `advanced` | Distributions and numeric correlations |

## ML

`POST /api/v1/ml/{id}/train`:

```json
{"target_column":"Sales","problem_type":"regression"}
```

Tasks: `auto`, `classification`, `regression`. Response includes actual usable row counts, feature names, split sizes, candidate results, selected model/metric/score, and permutation importance. Requires at least 10 usable rows and valid class support. Invalid targets/tasks return 400. Models are not persisted.

## Forecasting

`GET /api/v1/forecast/{id}/columns` returns `date_columns` and `numeric_columns`.

`POST /api/v1/forecast/{id}/predict`:

```json
{"date_column":"Date","target_column":"Sales","periods":7,"frequency":"D"}
```

Periods: 1–60. Frequency: `auto`, `D`, `W`, `MS`, `ME` (`M` is a compatibility alias), `QS`, `YS`. Requires at least 8 valid observations and 6 aggregated periods. Response contains historical values, forecast values, residual-spread bounds, frequency and slope. No backtested metric is returned.

## AI and conversations

`POST /api/v1/ai/chat`:

```json
{"prompt":"Summarize this dataset","dataset_id":1,"conversation_id":null}
```

Prompt: 1–10,000 characters. IDs are optional; when provided they must belong to the current user. Successful requests return prompt, response, success and conversation ID and save a message. Missing credentials/provider failures return 503 with sanitized text. `GET /api/v1/ai/test` is authenticated and returns the integration's success/response object.

`POST /api/v1/conversations/` takes `{"title":"Demo"}`. `GET` lists owned conversations. `PUT /api/v1/conversations/{id}` changes the title; `DELETE` removes it and its chats. Titles are 1–255 characters.

`GET /api/v1/ai/history/{conversation_id}?skip=0&limit=20` returns owned messages in chronological order. Skip must be nonnegative; limit is 1–100. `DELETE /api/v1/ai/history/{chat_id}` deletes one owned message. The IDs in GET and DELETE identify different resources.

## Errors

400: invalid data/task; 401: authentication; 404: absent/unowned resource; 413: upload limit; 422: request schema; 500: unexpected processing failure; 503: AI unavailable. Missing upload files are reported as a recoverable 400. Clients should display `detail` and avoid treating every failure as an authentication error.
