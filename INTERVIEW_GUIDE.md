# InsightForge AI: interview guide

## A short introduction

“InsightForge AI is my Python analytics project. A user signs in, uploads a spreadsheet, checks its quality and statistics, compares basic ML models, and generates a trend forecast. A React dashboard calls FastAPI endpoints, while PostgreSQL stores users and dataset metadata. Gemini chat is an optional integration. I focused on understanding the complete workflow and testing failures as well as successful requests.”

Use your own words and discuss only code you understand. The original project subtitle includes “Enterprise”; the implementation is a student demonstration, not evidence of enterprise deployment.

## What problem it solves

It combines early data exploration, model comparison, and optional natural-language questions in one interface. It helps a learner inspect a dataset before making modelling decisions. It does not replace a data scientist's domain judgement or a governed analytics system.

## Input to output

1. Register via Swagger, then sign in through React. The API verifies a bcrypt password hash and issues an expiring JWT.
2. The browser includes that token in authenticated requests. A dependency finds the current user.
3. A CSV/Excel upload receives a UUID filename, a size check, and a parsing check. Bad uploads are removed.
4. SQLAlchemy stores metadata and owner ID in PostgreSQL. The data itself stays in `backend/uploads`.
5. Analytics services load the file with pandas and return JSON-safe statistics, grouped aggregates, and quality checks. Recharts displays comparisons.
6. ML requests prepare features, split rows, fit four independent pipelines, evaluate predictions, and calculate permutation importance.
7. Forecast requests aggregate regular periods and fit a linear trend to period indices.
8. Optional chat sends dataset summaries, a preview, and history to Gemini. Successful replies are saved in a conversation.

## Backend and database

Routers handle HTTP and ownership checks. Pydantic schemas validate requests. Services perform analysis. Repositories hold SQLAlchemy queries. `get_db` gives one request a session and closes it afterward. Both auth and data routes share that dependency.

The four tables are `users`, `datasets`, `conversations`, and `chat_history`. Datasets and conversations belong to users; each chat belongs to a user and a conversation. Conversation deletion cascades to its chats through ORM relationships. Dataset deletion removes its metadata and file. Tables are initialized with `create_all`; there is no migration workflow.

Most data queries filter by both resource ID and current-user ID. A valid token alone does not grant access to another user's dataset. Automated tests cover this distinction.

## Important APIs

- `POST /register`, `POST /login`, `GET /me`: account creation, token issuance, and profile.
- `POST /api/v1/datasets/`: multipart upload; `GET` lists owned datasets.
- `GET /api/v1/analytics/{id}/summary`, `/quality`, `/statistics`, `/advanced`: descriptive results.
- `POST /api/v1/ml/{id}/train`: target and explicit/automatic task choice.
- `POST /api/v1/forecast/{id}/predict`: date, target, horizon, frequency.
- `POST /api/v1/ai/chat`: prompt with optional dataset and conversation IDs.
- `/api/v1/conversations/`: conversation creation, listing, renaming, deletion.

See [API details](docs/API.md) for payload examples.

## Preprocessing and algorithms

Non-finite numeric values become missing. Missing-target rows are excluded. Named dates become calendar and ordinal features. Constant columns and almost-unique text columns are excluded. Median imputation handles numeric gaps; most-frequent imputation and one-hot encoding handle categories. Encoders ignore previously unseen categories.

Classification uses logistic regression, decision tree, random forest, and gradient boosting. Regression substitutes linear regression for logistic regression and uses regressor versions of the tree models. Random forests average many trees; boosting builds trees sequentially to correct errors. Linear/logistic models provide simpler baselines.

The numeric pipeline currently does not standardize features. This can affect logistic regression convergence and is a possible improvement. Do not claim advanced hyperparameter optimization, deep learning, SHAP, model deployment, or persisted predictions: they are not implemented.

## Evaluation and explanation

The split is 80% training and 20% holdout with seed 42. Classification uses stratification after validating class support. Classification reports accuracy and weighted precision/recall/F1; the highest rounded weighted F1 wins. Regression reports MAE, MSE, RMSE, and R²; the highest rounded R² wins.

Permutation importance shuffles one feature and measures the reduction in holdout score over five repeats. It indicates model reliance under this evaluation, not causation. Correlated features can share or obscure importance.

The same holdout selects and evaluates the winner. Feature-selection decisions also inspect the full dataset before splitting. These limitations can make estimates optimistic. Cross-validation, fitted feature selection, and a separate final test partition would improve evaluation. Synthetic sample scores are not evidence of real-world accuracy.

## Generative AI

The Google Gen AI SDK calls the model configured by `GEMINI_MODEL`. The backend builds textual context from summaries, numeric statistics, grouped results, preview rows, and conversation history. This is prompt context, not an embedding/vector database retrieval system. The key stays on the backend.

The SDK client is created only when chat is requested. Missing keys do not prevent local analytics from starting. Requests have a timeout; provider exception text is replaced with a generic message. Mocked success/failure paths are tested. Live provider responses were not verified in this review. Dataset context can contain sensitive values, so use synthetic data for demonstrations.

## Challenges and solutions from the review

- Startup depended on an AI key: lazy client construction made the integration optional.
- Root and backend environment files differed: deterministic loading preserves the legacy backend file while preferring root values.
- Upload extensions were checked without parsing: parsing, byte limits, and cleanup now happen before metadata is saved.
- pandas 3 string columns were omitted: categorical selection now includes string dtype.
- Candidate pipelines shared preprocessing state: each pipeline now clones its transformer.
- Ordinary numbers were interpreted as timestamps: numeric epoch handling now requires an explicitly named timestamp column and selects seconds/milliseconds by magnitude.
- Frontend called a fixed hosted API: `VITE_API_URL` now configures it, with a localhost default.
- Statistical insights were labelled AI-generated: labels now distinguish local computations from optional Gemini chat.
- Empty repository documentation: setup steps, APIs, limitations, tests, and synthetic examples now explain the actual implementation.

## Known limitations to discuss honestly

Small-data, synchronous requests; local upload storage; no trained-model persistence; no cross-validation; heuristic task detection; simple forecasting without seasonality or backtesting; bounded Gemini context; no password reset, refresh tokens, rate limiting, RBAC, migrations, or deployment hardening. Docker and live Gemini verification require services unavailable or deliberately not exercised during review.

## Twenty likely interview questions

1. **Why FastAPI?** It supports typed request validation, dependency injection, and generated OpenAPI documentation, which make APIs easier to test and demonstrate.
2. **What is a REST API here?** HTTP routes expose resources and operations. For example, POST uploads a dataset and GET lists the current user's datasets.
3. **What does Pydantic do?** It validates request fields and serializes responses. Invalid shapes or constrained values return 422 before business logic runs.
4. **Why PostgreSQL?** Users, ownership, and chat relationships fit relational tables. Uploaded rows remain in files rather than being inserted into SQL.
5. **What is SQLAlchemy?** An ORM and database toolkit. Models describe tables, sessions manage database work, and repositories construct queries.
6. **How are passwords protected?** The application stores bcrypt hashes rather than plaintext. Registration limits password size to bcrypt's byte limit.
7. **How does JWT authentication work?** Login signs an expiring token. The server verifies its signature and expiry, then looks up its subject before handling protected requests.
8. **Authentication versus authorization?** Authentication identifies the user; authorization checks whether that user owns the requested dataset or conversation.
9. **How do you handle missing values?** Missing targets are dropped; numeric feature gaps use a training median and categorical gaps use a training mode. Analytics reports missing values rather than hiding them.
10. **Why use pipelines?** Preprocessing and the estimator are fitted together. Each candidate gets independent transformer state and applies the same fitted transformation during prediction.
11. **What is one-hot encoding?** It creates indicator columns for categories. Unknown test categories are ignored rather than raising an exception.
12. **Classification versus regression?** Classification predicts labels; regression predicts a continuous value. This project lets users select the task because automatic inference is only a heuristic.
13. **Why split the data?** Training performance alone can hide overfitting. A holdout estimates behaviour on unseen rows, though a separate final test set is still needed after model selection.
14. **Why weighted F1?** It combines precision and recall per class and weights by class support. It can still hide poor minority-class performance, so a confusion matrix and per-class scores are useful future additions.
15. **MAE versus RMSE versus R²?** MAE is average absolute error; RMSE penalizes large errors more strongly; R² compares squared error with predicting the mean and can be negative.
16. **Random forest versus gradient boosting?** Forests combine independently randomized trees. Boosting adds learners sequentially to reduce remaining error.
17. **What does feature importance prove?** It measures model reliance under the chosen data/metric; it does not establish that a feature causes the outcome.
18. **How does forecasting work?** It sums values into regular periods and fits a line against the period index. It does not model seasonality, and its residual bands are not calibrated intervals.
19. **How did you test the project?** API and service tests exercise auth, ownership, upload errors, analytics, mixed-data ML, forecasting, and mocked AI responses. The API suite also runs in isolated PostgreSQL schemas. Build/lint and browser smoke checks provide additional evidence; consult the verification report for counts.
20. **What would you improve first?** Add realistic datasets and evaluation discipline, workload limits, migrations, and broader browser tests before claiming production suitability.

## Resume statements supported by verification

- Developed an authenticated FastAPI and React analytics application with PostgreSQL metadata and per-user resource access.
- Implemented CSV/Excel ingestion, pandas-based descriptive analytics, quality checks, grouped charts, and HTML report generation.
- Compared four scikit-learn classifiers/regressors using holdout metrics and permutation feature importance.
- Added API and service regression tests, including ownership and invalid-input checks, and exercised the API suite against PostgreSQL.
- Implemented configurable Gemini context-based chat with missing-key and provider-failure handling; live provider responses remain unverified in this review.

Do not attach invented accuracy, speed, user counts, deployment scale, cost savings, or business impact. Describe the forecasting method as a linear baseline and the model comparison as exploratory. Be prepared to run the documented demonstration and explain one router, repository, and service function.
