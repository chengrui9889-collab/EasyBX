class TestCreateBatchAPI:
    def test_create_batch_returns_201(self, client, auth_headers):
        resp = client.post(
            "/api/batches/",
            json={"department": "研发部", "reporter": "张三"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["department"] == "研发部"
        assert data["reporter"] == "张三"
        assert data["id"] is not None

    def test_create_batch_without_token_returns_401(self, client):
        resp = client.post(
            "/api/batches/",
            json={"department": "研发部", "reporter": "张三"},
        )
        assert resp.status_code == 401

    def test_create_batch_with_report_date(self, client, auth_headers):
        resp = client.post(
            "/api/batches/",
            json={
                "department": "研发部",
                "reporter": "张三",
                "report_date": "2026-01-15",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["report_date"] == "2026-01-15"


class TestListBatchesAPI:
    def test_list_batches_returns_200(self, client, auth_headers):
        client.post(
            "/api/batches/",
            json={"department": "A", "reporter": "A"},
            headers=auth_headers,
        )
        resp = client.get("/api/batches/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 1

    def test_list_batches_empty(self, client, auth_headers):
        resp = client.get("/api/batches/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_batches_without_token_returns_401(self, client):
        resp = client.get("/api/batches/")
        assert resp.status_code == 401

    def test_list_batches_has_invoice_count(self, client, auth_headers):
        client.post(
            "/api/batches/",
            json={"department": "A", "reporter": "A"},
            headers=auth_headers,
        )
        resp = client.get("/api/batches/", headers=auth_headers)
        items = resp.json()["items"]
        assert items[0]["invoice_count"] == 0