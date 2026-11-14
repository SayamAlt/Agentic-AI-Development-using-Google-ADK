from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# In-memory storage for todos

class Todo(BaseModel):
    id: int
    text: str
    completed: bool = False

class TodoCreate(BaseModel):
    text: str
    completed: bool = False

todos_db: List[Todo] = []
next_id = 1

# Serve static files from the 'static' directory, but not at the root
app.mount("/static", StaticFiles(directory="static"), name="static")

# Explicitly serve index.html for the root path
@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.get("/todos", response_model=List[Todo])
def get_todos():
    return todos_db

@app.post("/todos", response_model=Todo, status_code=201)
async def create_todo(todo: TodoCreate):
    global next_id
    new_todo = Todo(id=next_id, text=todo.text, completed=todo.completed)
    todos_db.append(new_todo)
    next_id += 1
    return new_todo

@app.patch("/todos/{id}", response_model=Todo)
async def update_todo(id: int, updated_todo: TodoCreate):
    for i, todo in enumerate(todos_db):
        if todo.id == id:
            todos_db[i].text = updated_todo.text
            todos_db[i].completed = updated_todo.completed
            return todos_db[i]
    raise HTTPException(status_code=404, detail="Todo not found")

@app.delete("/todos/{id}", status_code=204)
async def delete_todo(id: int):
    global todos_db
    initial_len = len(todos_db)
    todos_db = [todo for todo in todos_db if todo.id != id]
    if len(todos_db) == initial_len:
        raise HTTPException(status_code=404, detail="Todo not found")
    return
