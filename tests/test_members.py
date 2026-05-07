from tests.conftest import login


def _new_project(client):
    r = client.post(
        "/api/v1/projects", json={"name": "P", "description": "", "status": "active"}
    )
    return r.json()


def test_add_member_by_email(auth_client, make_user):
    project = _new_project(auth_client)
    make_user("dan@example.com")

    r = auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "dan@example.com", "role": "viewer"},
    )
    assert r.status_code == 201
    assert r.json()["role"] == "viewer"


def test_add_unknown_email_404(auth_client):
    project = _new_project(auth_client)
    r = auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "nobody@example.com", "role": "member"},
    )
    assert r.status_code == 404


def test_cannot_add_same_user_twice(auth_client, make_user):
    project = _new_project(auth_client)
    make_user("eve@example.com")

    r1 = auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "eve@example.com", "role": "member"},
    )
    assert r1.status_code == 201

    r2 = auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "eve@example.com", "role": "member"},
    )
    assert r2.status_code == 409


def test_only_admin_can_add_members(auth_client, make_user):
    project = _new_project(auth_client)
    make_user("frank@example.com")
    auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "frank@example.com", "role": "viewer"},
    )

    make_user("grace@example.com")
    auth_client.cookies.clear()
    login(auth_client, "frank@example.com")
    r = auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "grace@example.com", "role": "member"},
    )
    assert r.status_code == 403


def test_update_member_role(auth_client, make_user):
    project = _new_project(auth_client)
    make_user("hank@example.com")
    add = auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "hank@example.com", "role": "viewer"},
    ).json()

    r = auth_client.patch(
        f"/api/v1/projects/{project['id']}/members/{add['user_id']}",
        json={"role": "member"},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "member"


def test_cannot_demote_last_admin(auth_client):
    project = _new_project(auth_client)
    me = auth_client.get("/api/v1/auth/me").json()
    r = auth_client.patch(
        f"/api/v1/projects/{project['id']}/members/{me['id']}",
        json={"role": "viewer"},
    )
    assert r.status_code in (403, 409)


def test_remove_member(auth_client, make_user):
    project = _new_project(auth_client)
    make_user("ivy@example.com")
    add = auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "ivy@example.com", "role": "member"},
    ).json()

    r = auth_client.delete(
        f"/api/v1/projects/{project['id']}/members/{add['user_id']}"
    )
    assert r.status_code == 200


def test_cannot_remove_owner(auth_client):
    project = _new_project(auth_client)
    me = auth_client.get("/api/v1/auth/me").json()
    r = auth_client.delete(
        f"/api/v1/projects/{project['id']}/members/{me['id']}"
    )
    assert r.status_code == 403


def test_member_can_leave_project(auth_client, make_user):
    project = _new_project(auth_client)
    make_user("jack@example.com")
    auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "jack@example.com", "role": "member"},
    )

    auth_client.cookies.clear()
    login(auth_client, "jack@example.com")
    r = auth_client.post(f"/api/v1/projects/{project['id']}/leave")
    assert r.status_code == 200


def test_owner_cannot_leave(auth_client):
    project = _new_project(auth_client)
    r = auth_client.post(f"/api/v1/projects/{project['id']}/leave")
    assert r.status_code == 403


def test_transfer_ownership(auth_client, make_user):
    project = _new_project(auth_client)
    make_user("kate@example.com")
    auth_client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "kate@example.com", "role": "admin"},
    )

    r = auth_client.post(
        f"/api/v1/projects/{project['id']}/transfer",
        json={"new_owner_email": "kate@example.com"},
    )
    assert r.status_code == 200

    auth_client.cookies.clear()
    login(auth_client, "kate@example.com")
    r2 = auth_client.delete(f"/api/v1/projects/{project['id']}")
    assert r2.status_code == 200
