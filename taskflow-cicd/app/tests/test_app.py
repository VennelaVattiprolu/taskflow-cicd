import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_create_and_list_task(client):
    resp = client.post("/tasks", json={"title": "Write README"})
    assert resp.status_code == 201
    task = resp.get_json()
    assert task["title"] == "Write README"
    assert task["done"] is False

    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1


def test_create_task_without_title(client):
    resp = client.post("/tasks", json={})
    assert resp.status_code == 400


def test_update_task(client):
    create = client.post("/tasks", json={"title": "Deploy pipeline"})
    task_id = create.get_json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"done": True})
    assert resp.status_code == 200
    assert resp.get_json()["done"] is True


def test_delete_task(client):
    create = client.post("/tasks", json={"title": "Temp task"})
    task_id = create.get_json()["id"]

    resp = client.delete(f"/tasks/{task_id}")
    assert resp.status_code == 204

    resp = client.get(f"/tasks/{task_id}")
    # PATCH on a deleted task should 404
    resp = client.patch(f"/tasks/{task_id}", json={"done": True})
    assert resp.status_code == 404
