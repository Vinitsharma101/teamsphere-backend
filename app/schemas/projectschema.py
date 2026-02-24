from typing import Optional
from pydantic import BaseModel 

from datetime import date

class ProjectCreate(BaseModel):
    name:str
    description: Optional[str] = None
    due_date:Optional[date] = None
    status:str
    
# class projectUpdate(BaseModel):
    