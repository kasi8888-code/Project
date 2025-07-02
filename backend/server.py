from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Models
class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    project_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    project_id: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    color: str = "#8B5CF6"  # Purple default
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    color: str = "#8B5CF6"

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

class TaskStats(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    high_priority_tasks: int

class ProjectStats(BaseModel):
    total_projects: int
    active_projects: int

# Routes

@api_router.get("/")
async def root():
    return {"message": "Todo List API is running!"}

# Dashboard Stats
@api_router.get("/stats", response_model=dict)
async def get_dashboard_stats():
    try:
        # Task stats
        total_tasks = await db.tasks.count_documents({})
        completed_tasks = await db.tasks.count_documents({"status": TaskStatus.DONE})
        pending_tasks = total_tasks - completed_tasks
        high_priority_tasks = await db.tasks.count_documents({"priority": TaskPriority.HIGH, "status": {"$ne": TaskStatus.DONE}})
        
        # Project stats
        total_projects = await db.projects.count_documents({})
        projects_with_tasks = await db.tasks.distinct("project_id", {"project_id": {"$ne": None}})
        active_projects = len([p for p in projects_with_tasks if p is not None])
        
        return {
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "pending": pending_tasks,
                "high_priority": high_priority_tasks
            },
            "projects": {
                "total": total_projects,
                "active": active_projects
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Task Routes
@api_router.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate):
    try:
        task_dict = task_data.dict()
        task = Task(**task_dict)
        await db.tasks.insert_one(task.dict())
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(project_id: Optional[str] = None, status: Optional[TaskStatus] = None):
    try:
        filter_dict = {}
        if project_id:
            filter_dict["project_id"] = project_id
        if status:
            filter_dict["status"] = status
            
        tasks = await db.tasks.find(filter_dict).sort("created_at", -1).to_list(1000)
        return [Task(**task) for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    try:
        task = await db.tasks.find_one({"id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return Task(**task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskUpdate):
    try:
        task = await db.tasks.find_one({"id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        update_data = {k: v for k, v in task_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        await db.tasks.update_one({"id": task_id}, {"$set": update_data})
        
        updated_task = await db.tasks.find_one({"id": task_id})
        return Task(**updated_task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    try:
        result = await db.tasks.delete_one({"id": task_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Project Routes
@api_router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate):
    try:
        project_dict = project_data.dict()
        project = Project(**project_dict)
        await db.projects.insert_one(project.dict())
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/projects", response_model=List[Project])
async def get_projects():
    try:
        projects = await db.projects.find().sort("created_at", -1).to_list(1000)
        return [Project(**project) for project in projects]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    try:
        project = await db.projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return Project(**project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, project_update: ProjectUpdate):
    try:
        project = await db.projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        update_data = {k: v for k, v in project_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        await db.projects.update_one({"id": project_id}, {"$set": update_data})
        
        updated_project = await db.projects.find_one({"id": project_id})
        return Project(**updated_project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    try:
        # Delete all tasks in the project first
        await db.tasks.delete_many({"project_id": project_id})
        
        # Delete the project
        result = await db.projects.delete_one({"id": project_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project and all its tasks deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get tasks for a specific project (Kanban view)
@api_router.get("/projects/{project_id}/tasks", response_model=List[Task])
async def get_project_tasks(project_id: str):
    try:
        tasks = await db.tasks.find({"project_id": project_id}).sort("created_at", -1).to_list(1000)
        return [Task(**task) for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()