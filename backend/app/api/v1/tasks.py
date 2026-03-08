"""
Task API Routes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import asyncio

from app.models.task import Task, TaskStatus, task_store
from app.llm.client import get_llm_client
from app.cad.executor import CADExecutor, CADExecutionError
from app.schema.models import CADModelPlan

router = APIRouter()

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)


# Request/Response Models
class CreateTaskRequest(BaseModel):
    user_description: str


class TaskResponse(BaseModel):
    id: str
    user_description: str
    status: str
    volume: Optional[float] = None
    bounding_box: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: str


class TaskDetailResponse(TaskResponse):
    cad_plan: Optional[dict] = None
    step_file_url: Optional[str] = None
    stl_file_url: Optional[str] = None


@router.post("/create", response_model=TaskResponse)
async def create_task(
    request: CreateTaskRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new CAD generation task
    
    The task will be processed asynchronously in the background
    """
    # Create task record
    task = task_store.create(user_description=request.user_description)
    task.status = TaskStatus.PENDING
    task_store.update(task)
    
    # Start background processing
    background_tasks.add_task(process_cad_task, task.id)
    
    return TaskResponse(**task.to_dict())


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: str):
    """Get task details by ID"""
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response_data = task.to_dict()
    
    # Add file URLs if available
    if task.step_file_path and os.path.exists(task.step_file_path):
        response_data["step_file_url"] = f"/api/v1/tasks/{task_id}/download/step"
    if task.stl_file_path and os.path.exists(task.stl_file_path):
        response_data["stl_file_url"] = f"/api/v1/tasks/{task_id}/download/stl"
    
    return TaskDetailResponse(**response_data)


@router.get("/{task_id}/download/step")
async def download_step(task_id: str):
    """Download the generated STEP file"""
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not task.step_file_path or not os.path.exists(task.step_file_path):
        raise HTTPException(status_code=404, detail="STEP file not found")
    
    return FileResponse(
        task.step_file_path,
        media_type="application/step",
        filename=f"{task_id}.step"
    )


@router.get("/{task_id}/download/stl")
async def download_stl(task_id: str):
    """Download the generated STL file (for preview)"""
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not task.stl_file_path or not os.path.exists(task.stl_file_path):
        raise HTTPException(status_code=404, detail="STL file not found")
    
    return FileResponse(
        task.stl_file_path,
        media_type="model/stl",
        filename=f"{task_id}.stl"
    )


@router.get("/", response_model=list[TaskResponse])
async def list_tasks():
    """List all tasks"""
    tasks = task_store.list_all()
    return [TaskResponse(**task.to_dict()) for task in tasks]


# Background task processing
async def process_cad_task(task_id: str):
    """Process CAD generation task in background"""
    task = task_store.get(task_id)
    if not task:
        return
    
    try:
        # Update status to parsing
        task.status = TaskStatus.PARSING
        task_store.update(task)
        
        # Get LLM client
        llm_client = get_llm_client("anthropic")  # Default to Anthropic
        
        # Generate CAD plan
        task.status = TaskStatus.GENERATING
        task_store.update(task)
        
        cad_plan = await llm_client.generate_cad_plan(task.user_description)
        task.cad_plan = cad_plan.model_dump()
        task_store.update(task)
        
        # Validate the plan (basic validation already done by Pydantic)
        task.status = TaskStatus.VALIDATING
        task_store.update(task)
        
        # Execute CAD generation
        task.status = TaskStatus.EXECUTING
        task_store.update(task)
        
        executor = CADExecutor()
        result = executor.execute_plan(cad_plan)
        
        # Get model info
        task.volume = executor.get_volume()
        task.bounding_box = executor.get_bounding_box()
        
        # Export files
        task.status = TaskStatus.EXPORTING
        task_store.update(task)
        
        # Export STEP
        step_path = os.path.join(STORAGE_DIR, f"{task_id}.step")
        executor.export_step(step_path)
        task.step_file_path = step_path
        
        # Export STL for preview
        stl_path = os.path.join(STORAGE_DIR, f"{task_id}.stl")
        executor.export_stl(stl_path, tolerance=0.1)
        task.stl_file_path = stl_path
        
        # Mark as completed
        task.status = TaskStatus.COMPLETED
        task_store.update(task)
        
    except Exception as e:
        # Handle errors
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        task_store.update(task)
        print(f"Task {task_id} failed: {e}")
