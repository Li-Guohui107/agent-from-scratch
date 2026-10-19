import pytest
from fastapi.testclient import TestClient

from main import app, tasks

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_in_memory_tasks():
    tasks.clear()
    yield
    tasks.clear()


def test_root_and_health_check():
    root_response = client.get("/")
    assert root_response.status_code == 200
    assert root_response.json()["docs"] == "/docs"

    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200
    assert health_response.json() == {
        "status": "ok",
        "service": "fastapi-agent-api",
    }


def test_task_crud_flow():
    create_response = client.post(
        "/api/v1/tasks",
        json={"title": "完成第六课", "description": "学习 FastAPI"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    task_id = created["id"]
    assert created["title"] == "完成第六课"
    assert created["completed"] is False

    list_response = client.get("/api/v1/tasks")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == task_id

    patch_response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"completed": True},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["completed"] is True

    delete_response = client.delete(f"/api/v1/tasks/{task_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/tasks/{task_id}")
    assert missing_response.status_code == 404


def test_invalid_task_title_returns_422():
    response = client.post("/api/v1/tasks", json={"title": "   "})
    assert response.status_code == 422


def test_chat_uses_demo_mode_without_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    response = client.post(
        "/api/v1/chat",
        json={"message": "请解释 RESTful API"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "demo"
    assert "请解释 RESTful API" in body["reply"]


def test_empty_chat_message_returns_422():
    response = client.post("/api/v1/chat", json={"message": "   "})
    assert response.status_code == 422


def test_patch_rejects_null_for_required_fields():
    created = client.post("/api/v1/tasks", json={"title": "检查字段"}).json()
    response = client.patch(f"/api/v1/tasks/{created['id']}", json={"completed": None})
    assert response.status_code == 422
