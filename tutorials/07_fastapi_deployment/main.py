from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response, status

from agent import run_agent
from schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)

app = FastAPI(
    title="Agent API - Lesson 06",
    version="1.0.0",
    description="第 06 课：RESTful API、接口测试与服务部署示例。",
)

# 教学用内存存储：进程重启后数据会丢失。生产环境请替换为数据库。
tasks: dict[str, TaskOut] = {}


@app.get("/", tags=["基础"])
def root() -> dict[str, str]:
    return {"message": "FastAPI Agent API is running", "docs": "/docs"}


@app.get("/api/v1/health", response_model=HealthResponse, tags=["基础"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="fastapi-agent-api")


@app.post(
    "/api/v1/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    tags=["任务管理"],
)
def create_task(payload: TaskCreate) -> TaskOut:
    task = TaskOut(
        id=str(uuid4()),
        title=payload.title,
        description=payload.description,
        completed=False,
    )
    tasks[task.id] = task
    return task


@app.get("/api/v1/tasks", response_model=list[TaskOut], tags=["任务管理"])
def list_tasks() -> list[TaskOut]:
    return list(tasks.values())


@app.get("/api/v1/tasks/{task_id}", response_model=TaskOut, tags=["任务管理"])
def get_task(task_id: str) -> TaskOut:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


@app.patch("/api/v1/tasks/{task_id}", response_model=TaskOut, tags=["任务管理"])
def update_task(task_id: str, payload: TaskUpdate) -> TaskOut:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    update_data = payload.model_dump(exclude_unset=True)
    if "title" in update_data and update_data["title"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="title 不能为 null",
        )
    if "completed" in update_data and update_data["completed"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="completed 不能为 null",
        )

    updated_task = task.model_copy(update=update_data)
    tasks[task_id] = updated_task
    return updated_task


@app.delete(
    "/api/v1/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["任务管理"],
)
def delete_task(task_id: str) -> Response:
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    del tasks[task_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Agent"])
def chat(payload: ChatRequest) -> ChatResponse:
    try:
        reply, mode = run_agent(payload.message)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return ChatResponse(reply=reply, mode=mode)
