"""Run a self-contained example against the API using disposable storage."""

from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.main import create_app


def main():
    with TemporaryDirectory() as directory:
        with TestClient(create_app(Path(directory) / "demo.db")) as client:
            created = client.post("/applications", json={
                "company": "Example Ltd",
                "role": "Cloud Engineering Intern",
                "applied_on": "2026-11-09",
            })
            created.raise_for_status()
            application_id = created.json()["id"]
            updated = client.patch(
                f"/applications/{application_id}/status", json={"status": "interview"}
            )
            updated.raise_for_status()
            report = client.get("/reports/status-counts")
            report.raise_for_status()
            print(f"Application {application_id}: {updated.json()['status']}")
            print("Interviews:", report.json()["interview"])


if __name__ == "__main__":
    main()
