import sqlite3
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI(title="Todo API")

DB_FILE = "todos.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def reset_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS todos")
    conn.commit()
    conn.close()
    init_db()

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class TodoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool = False

@app.get("/todos", response_model=List[TodoResponse])
def list_todos(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, title, description, completed FROM todos")
    rows = cursor.fetchall()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "completed": bool(row["completed"])
        }
        for row in rows
    ]

@app.post("/todos", response_model=TodoResponse, status_code=201)
def create_todo(todo: TodoCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO todos (title, description, completed) VALUES (?, ?, ?)",
        (todo.title, todo.description, int(todo.completed))
    )
    db.commit()
    todo_id = cursor.lastrowid
    cursor.execute("SELECT id, title, description, completed FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "completed": bool(row["completed"])
    }

@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, title, description, completed FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "completed": bool(row["completed"])
    }

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoUpdate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, title, description, completed FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")

    update_data = todo_update.model_dump(exclude_unset=True) if hasattr(todo_update, "model_dump") else todo_update.dict(exclude_unset=True)
    if not update_data:
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "completed": bool(row["completed"])
        }

    fields = []
    values = []
    for key, val in update_data.items():
        if key == "completed":
            val = int(val)
        fields.append(f"{key} = ?")
        values.append(val)

    values.append(todo_id)
    cursor.execute(f"UPDATE todos SET {', '.join(fields)} WHERE id = ?", tuple(values))
    db.commit()

    cursor.execute("SELECT id, title, description, completed FROM todos WHERE id = ?", (todo_id,))
    updated_row = cursor.fetchone()
    return {
        "id": updated_row["id"],
        "title": updated_row["title"],
        "description": updated_row["description"],
        "completed": bool(updated_row["completed"])
    }

@app.patch("/todos/{todo_id}/toggle", response_model=TodoResponse)
def toggle_todo(todo_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, title, description, completed FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    new_completed = 0 if row["completed"] else 1
    cursor.execute("UPDATE todos SET completed = ? WHERE id = ?", (new_completed, todo_id))
    db.commit()

    cursor.execute("SELECT id, title, description, completed FROM todos WHERE id = ?", (todo_id,))
    updated_row = cursor.fetchone()
    return {
        "id": updated_row["id"],
        "title": updated_row["title"],
        "description": updated_row["description"],
        "completed": bool(updated_row["completed"])
    }

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    return
