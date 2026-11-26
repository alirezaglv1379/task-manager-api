# API Reference

Interactive OpenAPI documentation is available at `/docs`; ReDoc is available at `/redoc`.

## Authentication

| Method | Path | Description |
|---|---|---|
| POST | `/signup` | Create an account |
| POST | `/login` | OAuth2 form login; returns Access Token and sets Refresh cookie |
| POST | `/auth/refresh` | Rotate Refresh Token and issue a new Access Token |
| POST | `/auth/logout` | Revoke current refresh session and clear cookie |
| GET | `/users/me` | Return current authenticated user |

`/login` accepts `application/x-www-form-urlencoded` fields `username` and `password`.

Refresh and logout require an `Origin` included in `CSRF_TRUSTED_ORIGINS`. Refresh Token is sent automatically in the HttpOnly cookie. Do not send it in JSON or local storage.

## Tasks

| Method | Path | Description |
|---|---|---|
| GET | `/tasks` | List current user's tasks |
| POST | `/tasks` | Create a task |
| GET | `/tasks/{task_id}` | Get one owned task |
| PUT | `/tasks/{task_id}` | Replace all editable task fields |
| PATCH | `/tasks/{task_id}` | Update only supplied fields |
| DELETE | `/tasks/{task_id}` | Delete an owned task |

### Pagination and sorting

`GET /tasks` query parameters:

- `page`: integer, default `1`, minimum `1`.
- `page_size`: integer, default `20`, range `1..100`.
- `sort_by`: `created_at`, `title`, `is_completed`, or `id`; default `created_at`.
- `order`: `asc` or `desc`; default `desc`.
- `is_completed`: optional boolean filter. `false` is a valid filter and is not treated as missing.

Response:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "total_pages": 0
}
```

The list is always scoped to the authenticated user's `owner_id`.

### Task request bodies

Create:

```json
{"title": "Prepare report", "description": null}
```

PUT requires all editable fields:

```json
{"title": "Prepare report", "description": "For Monday", "is_completed": false}
```

PATCH accepts only supplied fields. `description: null` clears the description. `title: null`, `is_completed: null`, an empty object, or unknown fields return 422.

## Common status codes

- `200`: successful read/update/login/signup.
- `201`: task created.
- `204`: task deleted or logout completed.
- `401`: missing/invalid/expired authentication.
- `404`: task does not exist or is not owned by the current user.
- `409`: uniqueness or database integrity conflict.
- `422`: invalid request data or query parameter.
- `429`: login rate limit exceeded; includes `Retry-After`.
- `500`: unexpected server-side persistence error with a generic message.
