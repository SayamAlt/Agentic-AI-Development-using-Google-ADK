from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "Todo App" in response.text

def test_get_todos_empty():
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_create_todo():
    # Send only 'text' and 'completed' as per the TodoCreate model
    response = client.post("/todos", json={"text": "New Todo Item", "completed": False})
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "New Todo Item"
    assert data["completed"] == False
    assert "id" in data

    # Verify it's in the list
    get_response = client.get("/todos")
    assert len(get_response.json()) == 1
    assert get_response.json()[0]["text"] == "New Todo Item"

@pytest.mark.asyncio
async def test_update_todo():
    # First, create a todo
    create_response = client.post("/todos", json={"text": "Todo to update", "completed": False})
    todo_id = create_response.json()["id"]

    # Then, update it, sending only fields to be updated
    update_response = client.patch(f"/todos/{todo_id}", json={"text": "Updated Todo", "completed": True})
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["text"] == "Updated Todo"
    assert data["completed"] == True
    assert data["id"] == todo_id

    # Verify the update
    get_response = client.get("/todos")
    assert len(get_response.json()) == 1
    assert get_response.json()[0]["text"] == "Updated Todo"
    assert get_response.json()[0]["completed"] == True

@pytest.mark.asyncio
async def test_delete_todo():
    # First, create a todo
    create_response = client.post("/todos", json={"text": "Todo to delete", "completed": False})
    todo_id = create_response.json()["id"]

    # Then, delete it
    delete_response = client.delete(f"/todos/{todo_id}")
    assert delete_response.status_code == 204

    # Verify it's deleted
    get_response = client.get("/todos")
    assert len(get_response.json()) == 0

def test_delete_nonexistent_todo():
    response = client.delete("/todos/999") # Assuming 999 does not exist
    assert response.status_code == 404
