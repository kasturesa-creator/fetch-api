from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import Response


app = FastAPI(
	title="Fetch API Classroom Server",
	description=(
		"A small teaching API for browser fetch(): query parameters, JSON request "
		"bodies, CRUD methods, and multipart image uploads. Try the endpoints here "
		"or use the interactive Swagger UI."
	),
	version="1.0.0",
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
)

# This JSON-like in-memory store resets whenever the server restarts.
database: dict[str, Any] = {"todos": [], "next_todo_id": 1}
MAX_IMAGE_SIZE = 5 * 1024 * 1024


class GreetingResponse(BaseModel):
	greeting: str
	sender: str
	message: str


class CalculationRequest(BaseModel):
	first_number: float = Field(examples=[12])
	second_number: float = Field(examples=[4])
	operator: str = Field(description="One of: +, -, *, /", examples=["+"])


class CalculationResponse(BaseModel):
	first_number: float
	second_number: float
	operator: str
	result: float


class TodoCreate(BaseModel):
	title: str = Field(min_length=1, max_length=200, examples=["Prepare fetch lesson"])
	completed: bool = False


class TodoUpdate(BaseModel):
	title: str = Field(min_length=1, max_length=200, examples=["Teach fetch basics"])
	completed: bool = Field(examples=[True])


class TodoItem(TodoUpdate):
	id: int

    
@app.head("/", tags=["Basics"], summary="Root endpoint with a welcome message")
@app.get("/", tags=["Basics"], summary="Root endpoint with a welcome message")
async def root() -> dict[str, str]:
	return {"message": "Welcome to the Fetch API Classroom Server!"}


@app.get("/api/v1/health", tags=["Basics"], summary="Check that the API is running")
async def health_check() -> dict[str, str]:
	"""A GET request with no inputs; useful as a first fetch example."""
	return {"status": "ok", "message": "The API is running."}


@app.get(
	"/api/v1/greetings",
	response_model=GreetingResponse,
	tags=["Query parameters"],
	summary="Build a greeting from query parameters",
	description="Try /api/v1/greetings?greeting=Welcome&sender=Ada.",
)
async def get_greeting(
	greeting: str = Query(default="Hello", min_length=1, max_length=40),
	sender: str = Query(default="World", min_length=1, max_length=80),
) -> GreetingResponse:
	return GreetingResponse(
		greeting=greeting,
		sender=sender,
		message=f"{greeting}, {sender}!",
	)


@app.post(
	"/api/v1/calculate",
	response_model=CalculationResponse,
	tags=["JSON request body"],
	summary="Calculate with two numbers from a JSON body",
	description="Send JSON with first_number, second_number, and operator (+, -, *, or /).",
)
async def calculate(request: CalculationRequest) -> CalculationResponse:
	operations = {
		"+": lambda first, second: first + second,
		"-": lambda first, second: first - second,
		"*": lambda first, second: first * second,
		"/": lambda first, second: first / second,
	}
	if request.operator not in operations:
		raise HTTPException(status_code=400, detail="Operator must be one of +, -, *, or /.")
	if request.operator == "/" and request.second_number == 0:
		raise HTTPException(status_code=400, detail="Cannot divide by zero.")

	result = operations[request.operator](request.first_number, request.second_number)
	return CalculationResponse(
		first_number=request.first_number,
		second_number=request.second_number,
		operator=request.operator,
		result=result,
	)


@app.get(
	"/api/v1/to-do",
	response_model=list[TodoItem],
	tags=["To-do CRUD"],
	summary="Read all to-do items",
)
async def list_todos() -> list[TodoItem]:
	return database["todos"]


@app.post(
	"/api/v1/to-do/add",
	response_model=TodoItem,
	status_code=201,
	tags=["To-do CRUD"],
	summary="Create a to-do item",
	description="Send a JSON body containing a title and, optionally, completed.",
)
async def add_todo(todo: TodoCreate) -> TodoItem:
	new_todo = TodoItem(
		id=database["next_todo_id"],
		title=todo.title,
		completed=todo.completed,
	)
	database["next_todo_id"] += 1
	database["todos"].append(new_todo.model_dump())
	return new_todo


@app.put(
	"/api/v1/to-do/{todo_id}",
	response_model=TodoItem,
	tags=["To-do CRUD"],
	summary="Replace a to-do item's editable fields",
	description="PUT replaces both title and completed; include both fields in the JSON body.",
)
async def replace_todo(todo_id: int, todo: TodoUpdate) -> TodoItem:
	for index, item in enumerate(database["todos"]):
		if item["id"] == todo_id:
			updated_todo = TodoItem(id=todo_id, title=todo.title, completed=todo.completed)
			database["todos"][index] = updated_todo.model_dump()
			return updated_todo
	raise HTTPException(status_code=404, detail=f"To-do item {todo_id} was not found.")


@app.delete(
	"/api/v1/to-do/{todo_id}",
	tags=["To-do CRUD"],
	summary="Delete a to-do item",
	description="A successful delete returns 204 No Content (an empty response).",
	status_code=204,
)
async def delete_todo(todo_id: int) -> Response:
	for index, item in enumerate(database["todos"]):
		if item["id"] == todo_id:
			database["todos"].pop(index)
			return Response(status_code=204)
	raise HTTPException(status_code=404, detail=f"To-do item {todo_id} was not found.")


@app.post(
	"/api/v1/images/echo",
	tags=["Multipart and binary responses"],
	summary="Upload an image and receive the same bytes",
	description=(
		"Choose an image file. This endpoint accepts multipart/form-data and returns "
		"the uploaded bytes unchanged. The submitted MIME type is not deep content validation."
	),
	response_class=Response,
	responses={200: {"content": {"image/*": {"schema": {"type": "string", "format": "binary"}}}}},
)
async def echo_image(image: UploadFile = File(..., description="An image to echo back")) -> Response:
	if not image.content_type or not image.content_type.startswith("image/"):
		raise HTTPException(status_code=415, detail="Upload a file with an image/* content type.")

	image_bytes = await image.read(MAX_IMAGE_SIZE + 1)
	if len(image_bytes) > MAX_IMAGE_SIZE:
		raise HTTPException(status_code=413, detail="Image must be 5 MiB or smaller.")

	return Response(content=image_bytes, media_type=image.content_type)