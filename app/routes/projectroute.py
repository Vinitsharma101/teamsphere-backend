from fastapi import APIRouter, Depends, HTTPException

from app.schemas.projectschema import ProjectCreate
from app.cores.db import get_connection
from app.cores.auth import verify_token

router = APIRouter(prefix="/project", tags=["Projects"])

@router.post("/new")
def create_project(project: ProjectCreate, user_id: int = Depends(verify_token)):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO projects (user_id, created_by, name, description, due_date, status)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            user_id,
            user_id,
            project.name,
            project.description,
            project.due_date,
            project.status
        )
    )

    conn.commit()
    project_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return {
        "message": "Project created successfully",
        "project_id": project_id
    }

@router.get("/{id}")
def get_project(id: int, user_id: int = Depends(verify_token)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM projects WHERE id = %s AND user_id = %s",
        (id, user_id)
    )
    project = cursor.fetchone()

    cursor.close()
    conn.close()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project

@router.get("")
def list_projects(user_id: int = Depends(verify_token)):
   
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM projects WHERE user_id = %s",
        (user_id,)
    )
    projects = cursor.fetchall()

    cursor.close()
    conn.close()

    return projects

@router.delete("/{id}")
def delete_project(id: int, user_id: int = Depends(verify_token)
):
    conn = get_connection()
    cursor = conn.cursor()

    # Step 1: Check ownership
    cursor.execute(
        "SELECT created_by FROM projects WHERE id = %s",
        (id,)
    )
    project = cursor.fetchone()

    if not project:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")

    created_by = project[0]

    # Step 2: Permission check
    if created_by != user_id:
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="Only project leader can delete this project"
        )

    # Step 3: Delete
    cursor.execute(
        "DELETE FROM projects WHERE id = %s",
        (id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Project deleted successfully"}



