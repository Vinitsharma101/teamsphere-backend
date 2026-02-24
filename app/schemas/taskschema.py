from typing import Optional
from pydantic import BaseModel 

from datetime import date

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    category: str

class taskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    category: Optional[str] = None