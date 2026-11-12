import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / 'test.db')) as client:
        yield client


def record(**changes):
    return {'company': 'Example Ltd', 'role': 'Python Intern',
            'applied_on': '2026-11-09', **changes}


def test_create_and_list(client):
    assert client.get('/applications').json() == []
    response = client.post('/applications', json=record(company=' Example Ltd '))
    assert response.status_code == 201
    assert response.json() == {'id': 1, **record(), 'status': 'applied'}
    assert client.get('/applications').json() == [response.json()]


def test_update_and_filter(client):
    client.post('/applications', json=record())
    client.post('/applications', json=record(company='Other Ltd'))
    response = client.patch('/applications/1/status', json={'status': 'interview'})
    assert response.status_code == 200
    assert response.json()['company'] == 'Example Ltd'
    assert response.json()['status'] == 'interview'
    assert [r['id'] for r in client.get('/applications?status=interview').json()] == [1]
    assert [r['id'] for r in client.get('/applications?status=applied').json()] == [2]


@pytest.mark.parametrize('changes', [
    {'company': '   '}, {'role': ''}, {'company': 'a' * 121},
    {'applied_on': '2026-02-30'}, {'status': 'unknown'}, {'unexpected': True},
])
def test_invalid_creation_does_not_write(client, changes):
    assert client.post('/applications', json=record(**changes)).status_code == 422
    assert client.get('/applications').json() == []


def test_invalid_updates_leave_record_unchanged(client):
    original = client.post('/applications', json=record()).json()
    for body in [{'status': 'unknown'}, {'status': None}, {}, {'status': 'offer', 'role': 'CEO'}]:
        assert client.patch('/applications/1/status', json=body).status_code == 422
    assert client.get('/applications').json() == [original]


def test_missing_and_invalid_ids(client):
    assert client.patch('/applications/999/status', json={'status': 'offer'}).status_code == 404
    for identity in ['0', '-1', 'abc']:
        assert client.patch(f'/applications/{identity}/status', json={'status': 'offer'}).status_code == 422
    assert client.get('/applications?status=unknown').status_code == 422


def test_persistence_across_app_restarts(tmp_path):
    database = tmp_path / 'nested' / 'persistent.db'
    with TestClient(create_app(database)) as first:
        first.post('/applications', json=record())
    with TestClient(create_app(database)) as second:
        assert second.get('/applications').json()[0]['company'] == 'Example Ltd'


def test_sql_looking_text_is_data_and_results_are_ordered(client):
    suspicious = "Company'); DROP TABLE applications;--"
    client.post('/applications', json=record(company=suspicious, applied_on='2026-01-01'))
    client.post('/applications', json=record())
    rows = client.get('/applications').json()
    assert [row['id'] for row in rows] == [2, 1]
    assert rows[1]['company'] == suspicious


def test_openapi_documents_endpoints(client):
    schema = client.get('/openapi.json').json()
    assert 'post' in schema['paths']['/applications']
    assert 'patch' in schema['paths']['/applications/{application_id}/status']


def test_get_one_application(client):
    created = client.post('/applications', json=record()).json()
    assert client.get(f"/applications/{created['id']}").json() == created
    assert client.get('/applications/999').status_code == 404
    assert client.get('/applications/0').status_code == 422


def test_status_counts(client):
    assert client.get('/reports/status-counts').json() == {}
    for status in ['applied', 'offer', 'applied']:
        client.post('/applications', json=record(status=status))
    assert client.get('/reports/status-counts').json() == {'applied': 2, 'offer': 1}


def test_report_after_last_application_leaves_status(client):
    created = client.post('/applications', json=record()).json()
    response = client.patch(f"/applications/{created['id']}/status", json={'status': 'interview'})
    assert response.status_code == 200
    assert client.get('/reports/status-counts').json() == {'interview': 1}
