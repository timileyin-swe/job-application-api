# Job Application API

A small, local FastAPI learning project for recording internship applications.
Python 3.12 is the development baseline. It follows the Python Expense Tracker:
SQLite and validation remain familiar while HTTP requests replace CLI commands.

## Run on Windows

Open PowerShell in this folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1
```

Open http://127.0.0.1:8000/docs to try the API. Stop the server with Ctrl+C.
The database is `applications.db` in the working directory. Set `APPLICATIONS_DB`
to use another path. Personal databases and environment files are ignored by Git.

| Request | Purpose | Success |
| --- | --- | --- |
| `POST /applications` | Add an application | 201 |
| `GET /applications` | List newest application dates first | 200 |
| `GET /applications?status=interview` | Filter by status | 200 |
| `PATCH /applications/1/status` | Update only the status | 200 |

Example creation body:

```json
{"company":"Example Ltd","role":"Python Intern","applied_on":"2026-11-09"}
```

Example update body: `{"status":"interview"}`.
Statuses: `applied`, `interview`, `offer`, `rejected`, `withdrawn`.
Invalid input returns 422; updating a missing application returns 404.
Company and role are trimmed, required, and limited to 120 characters.
Unknown body fields are rejected to catch misspelled inputs.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use disposable databases and cover creation, listing, filters, status
updates, invalid requests, persistence, SQL-looking text, and API documentation.

## Understand the files

- `app/__init__.py`: marks the application package.
- `app/main.py`: request models, routes, and small SQLite persistence functions.
- `tests/test_api.py`: sends HTTP-like requests through FastAPI's test client.
- `requirements.txt`: exact versions from the tested environment.
- `.gitignore`: excludes personal records and generated environment files.

Trace: JSON request -> Pydantic validation -> route function -> parameterized
SQLite statement -> response model -> JSON response. A connection context
commits successful writes, rolls back errors, and always closes the connection.
The app factory lets each test choose its own database. Startup creates the table;
merely importing the module does not create a database file.

## Practice

1. Add two fictional applications using `/docs`, then filter by status.
2. Update one to `interview`. Explain why its company name stays unchanged.
3. Submit an empty company. Explain why the response is 422 and no row is saved.
4. Find the SQL `?` placeholders and explain why user input is passed separately.
5. Read `test_persistence_across_app_restarts` and explain what it proves.

## Deliberate limits

Single-user local demo: no authentication, public hosting, PostgreSQL, deletion,
pagination, frontend, or status history. Statuses can be changed freely, including
backwards; no hiring-process transition rules are imposed. Do not expose this
unauthenticated app publicly or enter real applicant information in demonstrations.
Later work should follow understanding of this version, not add technology for its
own sake. Development used AI assistance; personal mastery requires the exercises.

Sources: [FastAPI request bodies](https://fastapi.tiangolo.com/tutorial/body/)
and [testing](https://fastapi.tiangolo.com/tutorial/testing/).
