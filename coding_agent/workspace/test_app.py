import pytest
from fastapi.testclient import TestClient
from app import app, reset_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    reset_db()
    yield
    reset_db()

def test_list_todos_empty():
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []

def test_create_todo():
    response = client.post("/todos", json={"title": "Buy milk", "description": "2% milk"})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Buy milk"
    assert data["description"] == "2% milk"
    assert data["completed"] is False

def test_get_todo_by_id():
    client.post("/todos", json={"title": "Task 1"})
    response = client.get("/todos/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Task 1"

def test_get_todo_not_found():
    response = client.get("/todos/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo not found"

def test_update_todo():
    client.post("/todos", json={"title": "Task 1", "completed": False})
    response = client.put("/todos/1", json={"completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Task 1"
    assert data["completed"] is True

def test_update_todo_not_found():
    response = client.put("/todos/999", json={"title": "Updated"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo not found"

def test_delete_todo():
    client.post("/todos", json={"title": "Task to delete"})
    del_response = client.delete("/todos/1")
    assert del_response.status_code == 204

    get_response = client.get("/todos/1")
    assert get_response.status_code == 404

    list_response = client.get("/todos")
    assert list_response.json() == []

def test_delete_todo_not_found():
    response = client.delete("/todos/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo not found"

def test_read_root(client):
    response = client.get('/')
    assert response.status_code == 200
    assert "Todo List" in response.text
    client.post("/todos", json={"title": "Task toggle", "completed": False})
    
    # Toggle from False to True
    res1 = client.patch("/todos/1/toggle")
    assert res1.status_code == 200
    assert res1.json()["completed"] is True

    # Toggle from True back to False
    res2 = client.patch("/todos/1/toggle")
    assert res2.status_code == 200
    assert res2.json()["completed"] is False

def test_toggle_todo_not_found():
    response = client.patch("/todos/999/toggle")
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo not found"

