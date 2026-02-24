from fastapi import APIRouter, HTTPException
import bcrypt

from app.schemas.userschema import SignupRequest, LoginRequest
from app.cores.db import get_connection
from app.cores.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup")
def signup(user: SignupRequest):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
        (user.name, user.email, hashed_password)
    )
    conn.commit()
    user_id = cursor.lastrowid

    cursor.close()
    conn.close()

    token = create_access_token({"user_id": user_id})

    return {
        "message": "User registered successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": user.name,
            "email": user.email
        }
    }


@router.post("/login")
def login(user: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, name, email, password FROM users WHERE email = %s",
        (user.email,)
    )
    db_user = cursor.fetchone()

    if not db_user or not bcrypt.checkpw(
        user.password.encode("utf-8"),
        db_user["password"].encode("utf-8")
    ):
        cursor.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    cursor.close()
    conn.close()

    token = create_access_token({"user_id": db_user["id"]})

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_user["id"],
            "name": db_user["name"],
            "email": db_user["email"]
        }
    }
