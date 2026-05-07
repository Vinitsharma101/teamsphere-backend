from tests.conftest import login, signup


def _create_project(client, name="Project A"):
    r = client.post(
        "/api/v1/projects",
        json={"name": name, "description": "desc", "status": "active"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_create_project_makes_creator_an_admin(auth_client):
    project = _create_project(auth_client)
    assert project["name"] == "Project A"
    assert project["created_by"] > 0

    members = auth_client.get(f"/api/v1/projects/{project['id']}/members").json()
    assert len(members) == 1
    assert members[0]["role"] == "admin"


def test_list_projects_returns_only_projects_user_belongs_to(auth_client, make_user):
    _create_project(auth_client, "Mine")

    make_user("bob@example.com")
    auth_client.cookies.clear()
    login(auth_client, "bob@example.com")
    r = auth_client.get("/api/v1/projects")
    assert r.status_code == 200
    assert r.json() == []


def test_get_project_requires_membership(auth_client, make_user):
    project = _create_project(auth_client)

    make_user("eve@example.com")
    auth_client.cookies.clear()
    login(auth_client, "eve@example.com")

    r = auth_client.get(f"/api/v1/projects/{project['id']}")
    assert r.status_code == 403


def test_update_project_requires_admin(auth_client, make_user):
    project = _create_project(auth_client)
    make_user("ben@example.com")
    auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "ben@example.com", "role": "member"},
    )

    auth_client.cookies.clear()
    login(auth_client, "ben@example.com")
    r = auth_client.patch(
        f"/api/v1/projects/{project['id']}", json={"name": "Hacked"}
    )
    assert r.status_code == 403


def test_admin_can_update_project(auth_client):
    project = _create_project(auth_client)
    r = auth_client.patch(
        f"/api/v1/projects/{project['id']}", json={"name": "Renamed"}
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"


def test_only_owner_can_delete_project(auth_client, make_user):
    project = _create_project(auth_client)
    make_user("carol@example.com")
    auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "carol@example.com", "role": "admin"},
    )

    auth_client.cookies.clear()
    login(auth_client, "carol@example.com")
    r = auth_client.delete(f"/api/v1/projects/{project['id']}")
    assert r.status_code == 403


def test_owner_can_delete_project(auth_client):
    project = _create_project(auth_client)
    r = auth_client.delete(f"/api/v1/projects/{project['id']}")
    assert r.status_code == 200

    r2 = auth_client.get(f"/api/v1/projects/{project['id']}")
    assert r2.status_code == 404


def test_project_returns_404_when_not_found(auth_client):
    r = auth_client.get("/api/v1/projects/9999")
    assert r.status_code == 404
