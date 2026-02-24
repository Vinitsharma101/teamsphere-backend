from fastapi import APIRouter, Depends, HTTPException

from app.schemas.taskschema import TaskCreate, taskUpdate
from app.cores.db import get_connection
from app.cores.auth import verify_token

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/new")
def create_task(task: TaskCreate, user_id: int = Depends(verify_token)):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO tasks (user_id, title, description, due_date, category)
    VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            user_id,
            task.title,
            task.description,
            task.due_date,
            task.category
        )
    )

    conn.commit()
    task_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return {
        "message": "Task created successfully",
        "task_id": task_id
    }


@router.get("/{id}")
def get_task(id: int, user_id: int = Depends(verify_token)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM tasks WHERE id = %s AND user_id = %s",
        (id, user_id)
    )
    task = cursor.fetchone()

    cursor.close()
    conn.close()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.get("")
def list_tasks(user_id: int = Depends(verify_token)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM tasks WHERE user_id = %s", (user_id,))
    tasks = cursor.fetchall()

    cursor.close()
    conn.close()

    return tasks

@router.delete("/{id}")
def delete_task(id: int, user_id: int = Depends(verify_token)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = %s AND user_id = %s",
        (id, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Task deleted successfully"}


