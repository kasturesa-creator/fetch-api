# Fetch API Classroom Server

A small FastAPI server for learning browser `fetch()`, HTTP methods, query parameters, JSON request bodies, and multipart/binary data. To-do items are kept in a global in-memory JSON-like object and are cleared when the server restarts.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open the interactive API guide at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The OpenAPI document is at [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json).

## Deploy on Render

Create a Render Web Service from this repository. Use the following commands:

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Render sets `PORT` for the service. After deployment, Swagger is available at `<your-service-url>/docs`.

CORS is configured to allow requests from any origin, with any method and headers. Credentialed cross-origin requests are not enabled.

## Endpoints

| Method | Endpoint | What it demonstrates |
| --- | --- | --- |
| `GET` | `/api/v1/health` | A request with no input |
| `GET` | `/api/v1/greetings?greeting=Welcome&sender=Ada` | Query parameters |
| `GET` | `/api/v1/promise?seconds=2` | Async endpoint that waits before responding |
| `POST` | `/api/v1/calculate` | JSON body and validation |
| `GET` | `/api/v1/to-do` | Read all to-do items |
| `POST` | `/api/v1/to-do/add` | Create an item with JSON |
| `PUT` | `/api/v1/to-do/{todo_id}` | Replace an item's fields with JSON |
| `DELETE` | `/api/v1/to-do/{todo_id}` | Delete an item |
| `POST` | `/api/v1/images/echo` | Multipart upload and binary response |

## `fetch()` examples

### Query parameters

```js
const params = new URLSearchParams({ greeting: "Welcome", sender: "Ada" });
const response = await fetch(`http://127.0.0.1:8000/api/v1/greetings?${params}`);
const greeting = await response.json();
console.log(greeting.message);
```

### Async response

The browser's `fetch()` returns a promise. This endpoint also waits asynchronously on the server using `asyncio.sleep()` before it responds.

```js
const response = await fetch("http://127.0.0.1:8000/api/v1/promise?seconds=2");
const result = await response.json();
console.log(result.message); // "Promise resolved after 2.0 seconds."
```

### JSON request body

```js
const response = await fetch("http://127.0.0.1:8000/api/v1/calculate", {
	method: "POST",
	headers: { "Content-Type": "application/json" },
	body: JSON.stringify({ first_number: 12, second_number: 4, operator: "/" }),
});
const calculation = await response.json();
console.log(calculation.result);
```

### To-do CRUD

```js
const baseUrl = "http://127.0.0.1:8000/api/v1/to-do";

// Create
const createdResponse = await fetch(`${baseUrl}/add`, {
	method: "POST",
	headers: { "Content-Type": "application/json" },
	body: JSON.stringify({ title: "Teach fetch", completed: false }),
});
const todo = await createdResponse.json();

// Read all
const listResponse = await fetch(baseUrl);
const todos = await listResponse.json();

// Replace both editable fields (PUT)
await fetch(`${baseUrl}/${todo.id}`, {
	method: "PUT",
	headers: { "Content-Type": "application/json" },
	body: JSON.stringify({ title: "Teach fetch basics", completed: true }),
});

// Delete; 204 means the response has no body
await fetch(`${baseUrl}/${todo.id}`, { method: "DELETE" });
```

### Upload an image with `FormData`

```js
const formData = new FormData();
formData.append("image", fileInput.files[0]);

const response = await fetch("http://127.0.0.1:8000/api/v1/images/echo", {
	method: "POST",
	body: formData, // Let the browser set the multipart Content-Type and boundary.
});
const imageBlob = await response.blob();
const imageUrl = URL.createObjectURL(imageBlob);
imageElement.src = imageUrl;
// Revoke imageUrl when the displayed image is no longer needed.
```

The image route returns the uploaded bytes unchanged and limits uploads to 5 MiB. It checks the submitted `image/*` MIME type, not the actual file contents.
