from fastapi import status


class TestGetMe:
    def test_returns_user_with_defaults(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "id" in data
        assert "username" in data
        assert "default_department" in data
        assert "default_reporter" in data
        assert "default_payee" in data
        assert "default_bank_account" in data
        assert "default_bank_name" in data

    def test_requires_auth(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_default_fields_are_none_when_unset(self, client, test_user, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        data = resp.json()
        assert data["default_department"] is None
        assert data["default_reporter"] is None
        assert data["default_payee"] is None
        assert data["default_bank_account"] is None
        assert data["default_bank_name"] is None


class TestUpdateMe:
    def test_update_default_department(self, client, test_user, auth_headers):
        resp = client.put(
            "/api/auth/me",
            json={"default_department": "产教融合"},
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["default_department"] == "产教融合"

    def test_update_persists(self, client, auth_headers):
        client.put(
            "/api/auth/me",
            json={"default_department": "研发部"},
            headers=auth_headers,
        )
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.json()["default_department"] == "研发部"

    def test_partial_update_other_fields_unchanged(self, client, test_user, auth_headers):
        client.put(
            "/api/auth/me",
            json={"default_department": "产教融合", "default_reporter": "程瑞"},
            headers=auth_headers,
        )
        client.put(
            "/api/auth/me",
            json={"default_department": "研发部"},
            headers=auth_headers,
        )
        resp = client.get("/api/auth/me", headers=auth_headers)
        data = resp.json()
        assert data["default_department"] == "研发部"
        assert data["default_reporter"] == "程瑞"

    def test_update_all_fields(self, client, auth_headers):
        resp = client.put(
            "/api/auth/me",
            json={
                "default_department": "产教融合",
                "default_reporter": "程瑞",
                "default_payee": "程瑞",
                "default_bank_account": "6222000012345678",
                "default_bank_name": "中国工商银行",
            },
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["default_department"] == "产教融合"
        assert data["default_reporter"] == "程瑞"
        assert data["default_payee"] == "程瑞"
        assert data["default_bank_account"] == "6222000012345678"
        assert data["default_bank_name"] == "中国工商银行"

    def test_updating_affects_new_batch_defaults(self, client, db, test_user, auth_headers):
        client.put(
            "/api/auth/me",
            json={
                "default_department": "产教融合",
                "default_reporter": "程瑞",
                "default_payee": "收款人",
                "default_bank_account": "6222000012345678",
                "default_bank_name": "工商银行",
            },
            headers=auth_headers,
        )

        resp = client.post(
            "/api/batches/",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["department"] == "产教融合"
        assert data["reporter"] == "程瑞"
        assert data["payee"] == "收款人"

    def test_requires_auth(self, client):
        resp = client.put(
            "/api/auth/me",
            json={"default_department": "产教融合"},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
