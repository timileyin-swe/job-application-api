"""HTTP routes and validation for a local, single-user learning project."""
import os
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path as PathParameter
from pydantic import BaseModel, ConfigDict, Field

Status = Literal['applied', 'interview', 'offer', 'rejected', 'withdrawn']


class NewApplication(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=120)
    applied_on: date
    status: Status = 'applied'


class Application(NewApplication):
    id: int


class StatusUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Status


def create_app(database_path=None):
    """Allow tests to use disposable databases instead of personal records."""
    database = Path(database_path or os.getenv('APPLICATIONS_DB', 'applications.db'))

    @contextmanager
    def connect():
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @asynccontextmanager
    async def lifespan(api):
        database.parent.mkdir(parents=True, exist_ok=True)
        with connect() as connection:
            connection.execute('''CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                applied_on TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN
                    ('applied','interview','offer','rejected','withdrawn'))
            )''')
        yield

    api = FastAPI(title='Job Application API', version='0.1.0', lifespan=lifespan)

    @api.post('/applications', response_model=Application, status_code=201)
    def add_application(application: NewApplication):
        with connect() as connection:
            cursor = connection.execute(
                'INSERT INTO applications(company,role,applied_on,status) VALUES(?,?,?,?)',
                (application.company, application.role,
                 application.applied_on.isoformat(), application.status),
            )
            return {'id': cursor.lastrowid, **application.model_dump()}

    @api.get('/applications', response_model=list[Application])
    def list_applications(status: Status | None = None):
        query = 'SELECT * FROM applications'
        parameters = ()
        if status is not None:
            query += ' WHERE status=?'
            parameters = (status,)
        query += ' ORDER BY applied_on DESC, id DESC'
        with connect() as connection:
            return [dict(row) for row in connection.execute(query, parameters)]

    @api.patch('/applications/{application_id}/status', response_model=Application)
    def update_status(application_id: Annotated[int, PathParameter(gt=0)], update: StatusUpdate):
        with connect() as connection:
            cursor = connection.execute(
                'UPDATE applications SET status=? WHERE id=?',
                (update.status, application_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail='Application not found')
            return dict(connection.execute(
                'SELECT * FROM applications WHERE id=?', (application_id,)
            ).fetchone())

    @api.get('/applications/{application_id}', response_model=Application)
    def get_application(application_id: Annotated[int, PathParameter(gt=0)]):
        with connect() as connection:
            row = connection.execute(
                'SELECT * FROM applications WHERE id=?', (application_id,)
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail='Application not found')
        return dict(row)

    return api


app = create_app()
