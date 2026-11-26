from tests.conftest import auth_headers, signup


def _create(client, headers, title, description=None):
    return client.post(
        "/tasks",
        headers=headers,
        json={"title": title, "description": description},
    )


def test_task_crud_and_pagination(client):
    signup(client)
    headers = auth_headers(client)
    for index in range(23):
        response = _create(client, headers, f"Task {index:02d}")
        assert response.status_code == 201

    first_page = client.get("/tasks?page=1&page_size=20", headers=headers)
    assert first_page.status_code == 200
    data = first_page.json()
    assert len(data["items"]) == 20
    assert data["total"] == 23
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total_pages"] == 2

    second_page = client.get("/tasks?page=2&page_size=20", headers=headers)
    assert len(second_page.json()["items"]) == 3
    ids = {item["id"] for item in data["items"]}
    assert not ids.intersection({item["id"] for item in second_page.json()["items"]})


def test_is_completed_false_filter_is_applied(client):
    signup(client)
    headers = auth_headers(client)
    task = _create(client, headers, "To complete").json()
    client.patch(f"/tasks/{task['id']}", headers=headers, json={"is_completed": True})

    incomplete = client.get("/tasks?is_completed=false", headers=headers).json()
    complete = client.get("/tasks?is_completed=true", headers=headers).json()
    assert incomplete["total"] == 0
    assert complete["total"] == 1


def test_put_requires_all_editable_fields_and_replaces_them(client):
    signup(client)
    headers = auth_headers(client)
    task = _create(client, headers, "Original", "old description").json()

    incomplete_put = client.put(f"/tasks/{task['id']}", headers=headers, json={"title": "new"})
    assert incomplete_put.status_code == 422

    response = client.put(
        f"/tasks/{task['id']}",
        headers=headers,
        json={"title": "Replaced", "description": None, "is_completed": True},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Replaced"
    assert response.json()["description"] is None
    assert response.json()["is_completed"] is True


def test_patch_is_partial_and_rejects_nulls_and_empty_body(client):
    signup(client)
    headers = auth_headers(client)
    task = _create(client, headers, "Keep title", "description").json()

    response = client.patch(f"/tasks/{task['id']}", headers=headers, json={"is_completed": True})
    assert response.status_code == 200
    assert response.json()["title"] == "Keep title"
    assert response.json()["description"] == "description"

    assert client.patch(f"/tasks/{task['id']}", headers=headers, json={}).status_code == 422
    assert client.patch(
        f"/tasks/{task['id']}", headers=headers, json={"title": None}
    ).status_code == 422
    assert client.patch(
        f"/tasks/{task['id']}", headers=headers, json={"is_completed": None}
    ).status_code == 422
    assert client.patch(
        f"/tasks/{task['id']}", headers=headers, json={"owner_id": 99}
    ).status_code == 422

    clear = client.patch(f"/tasks/{task['id']}", headers=headers, json={"description": None})
    assert clear.status_code == 200
    assert clear.json()["description"] is None


def test_task_owner_isolation_returns_404(client):
    signup(client, "firstuser")
    first_headers = auth_headers(client, "firstuser")
    task = _create(client, first_headers, "Private task").json()

    signup(client, "seconduser")
    second_headers = auth_headers(client, "seconduser")
    assert client.get(f"/tasks/{task['id']}", headers=second_headers).status_code == 404
    assert client.patch(
        f"/tasks/{task['id']}", headers=second_headers, json={"title": "hack"}
    ).status_code == 404


def test_sorting_and_invalid_pagination(client):
    signup(client)
    headers = auth_headers(client)
    _create(client, headers, "Zebra")
    _create(client, headers, "Alpha")

    sorted_tasks = client.get("/tasks?sort_by=title&order=asc", headers=headers).json()
    assert [item["title"] for item in sorted_tasks["items"]] == ["Alpha", "Zebra"]
    assert client.get("/tasks?page=0", headers=headers).status_code == 422
    assert client.get("/tasks?page_size=101", headers=headers).status_code == 422
    assert client.get("/tasks?sort_by=owner_id", headers=headers).status_code == 422


def test_task_input_validation(client):
    signup(client)
    headers = auth_headers(client)
    assert _create(client, headers, "   ").status_code == 422
    assert _create(client, headers, "x" * 201).status_code == 422
    assert client.post(
        "/tasks", headers=headers, json={"title": "valid", "extra": 1}
    ).status_code == 422
