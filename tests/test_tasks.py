from tests.conftest import login


def _project(client, name="P"):
    return client.post(
        "/api/v1/projects",
        json={"name": name, "description": "", "status": "active"},
    ).json()


def _add_member(client, project_id, email, role="member"):
    return client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"email": email, "role": role},
    )


def test_create_task_in_project(auth_client):
    p = _project(auth_client)
    r = auth_client.post(
        f"/api/v1/projects/{p['id']}/tasks",
        json={"title": "T1", "priority": "high"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "T1"
    assert body["project_id"] == p["id"]
    assert body["status"] == "todo"
    assert body["priority"] == "high"


def test_viewer_cannot_create_task(auth_client, make_user):
    p = _project(auth_client)
    make_user("liam@example.com")
    _add_member(auth_client, p["id"], "liam@example.com", role="viewer")

    auth_client.cookies.clear()
    login(auth_client, "liam@example.com")
    r = auth_client.post(
        f"/api/v1/projects/{p['id']}/tasks", json={"title": "X"}
    )
    assert r.status_code == 403


def test_non_member_gets_403_listing_tasks(auth_client, make_user):
    p = _project(auth_client)
    make_user("mia@example.com")
    auth_client.cookies.clear()
    login(auth_client, "mia@example.com")
    r = auth_client.get(f"/api/v1/projects/{p['id']}/tasks")
    assert r.status_code == 403


def test_list_tasks_paginated_and_filtered(auth_client):
    p = _project(auth_client)
    for i in range(5):
        auth_client.post(
            f"/api/v1/projects/{p['id']}/tasks",
            json={"title": f"T{i}", "priority": "high" if i % 2 else "low"},
        )

    r = auth_client.get(
        f"/api/v1/projects/{p['id']}/tasks?page=1&page_size=2"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 5
    assert body["pages"] == 3
    assert len(body["items"]) == 2

    r2 = auth_client.get(
        f"/api/v1/projects/{p['id']}/tasks?priority=high"
    )
    assert r2.status_code == 200
    assert all(t["priority"] == "high" for t in r2.json()["items"])


def test_update_task_status(auth_client):
    p = _project(auth_client)
    task = auth_client.post(
        f"/api/v1/projects/{p['id']}/tasks", json={"title": "T"}
    ).json()

    r = auth_client.patch(
        f"/api/v1/tasks/{task['id']}", json={"status": "in_progress"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"


def test_assignee_must_be_project_member(auth_client, make_user):
    p = _project(auth_client)
    outsider = make_user("nate@example.com")

    r = auth_client.post(
        f"/api/v1/projects/{p['id']}/tasks",
        json={"title": "X", "assigned_to": outsider.id},
    )
    assert r.status_code == 422


def test_assign_to_member(auth_client, make_user):
    p = _project(auth_client)
    member = make_user("olive@example.com")
    _add_member(auth_client, p["id"], "olive@example.com")

    r = auth_client.post(
        f"/api/v1/projects/{p['id']}/tasks",
        json={"title": "X", "assigned_to": member.id},
    )
    assert r.status_code == 201
    assert r.json()["assigned_to"] == member.id


def test_creator_can_delete_own_task(auth_client, make_user):
    p = _project(auth_client)
    make_user("pete@example.com")
    _add_member(auth_client, p["id"], "pete@example.com")

    auth_client.cookies.clear()
    login(auth_client, "pete@example.com")
    task = auth_client.post(
        f"/api/v1/projects/{p['id']}/tasks", json={"title": "Mine"}
    ).json()
    r = auth_client.delete(f"/api/v1/tasks/{task['id']}")
    assert r.status_code == 200


def test_member_cannot_delete_others_task(auth_client, make_user):
    p = _project(auth_client)
    make_user("quinn@example.com")
    _add_member(auth_client, p["id"], "quinn@example.com")

    owner_task = auth_client.post(
        f"/api/v1/projects/{p['id']}/tasks", json={"title": "Owner"}
    ).json()

    auth_client.cookies.clear()
    login(auth_client, "quinn@example.com")
    r = auth_client.delete(f"/api/v1/tasks/{owner_task['id']}")
    assert r.status_code == 403


def test_admin_can_delete_any_task(auth_client, make_user):
    p = _project(auth_client)
    make_user("rita@example.com")
    _add_member(auth_client, p["id"], "rita@example.com")

    auth_client.cookies.clear()
    login(auth_client, "rita@example.com")
    rita_task = auth_client.post(
        f"/api/v1/projects/{p['id']}/tasks", json={"title": "Rita"}
    ).json()

    auth_client.cookies.clear()
    login(auth_client, "alice@example.com")
    r = auth_client.delete(f"/api/v1/tasks/{rita_task['id']}")
    assert r.status_code == 200
