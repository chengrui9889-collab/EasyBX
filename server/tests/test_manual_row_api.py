from datetime import date


class _Helpers:
    @staticmethod
    def _create_batch(client, auth_headers):
        resp = client.post(
            "/api/batches/",
            json={"department": "测试部", "reporter": "测试人"},
            headers=auth_headers,
        )
        return resp.json()["id"]


class TestCreateManualRowAPI:
    def test_create_manual_row_returns_201(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)

        resp = client.post(
            f"/api/batches/{batch_id}/manual-rows",
            json={"expense_item": "奖金", "row_amount": 1000.0},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] is not None
        assert data["source_type"] == "manual"
        assert data["expense_item"] == "奖金"
        assert data["row_amount"] == 1000.0
        assert data["quantity"] == 1.0
        assert data["unit_price"] == 1000.0

    def test_create_manual_row_with_all_fields(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)

        resp = client.post(
            f"/api/batches/{batch_id}/manual-rows",
            json={
                "row_date": "2025-12-01",
                "expense_item": "团建费",
                "row_amount": 500.0,
                "quantity": 2.0,
                "advance_amount": 300.0,
                "remark": "测试",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["row_date"] == "2025-12-01"
        assert data["expense_item"] == "团建费"
        assert data["row_amount"] == 500.0
        assert data["unit_price"] == 250.0

    def test_create_manual_row_amount_zero_returns_422(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)

        resp = client.post(
            f"/api/batches/{batch_id}/manual-rows",
            json={"expense_item": "奖金", "row_amount": 0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_manual_row_missing_expense_item_returns_422(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)

        resp = client.post(
            f"/api/batches/{batch_id}/manual-rows",
            json={"row_amount": 1000.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_manual_row_batch_not_found(self, client, auth_headers):
        resp = client.post(
            "/api/batches/999/manual-rows",
            json={"expense_item": "奖金", "row_amount": 1000.0},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_create_manual_row_without_token_returns_401(self, client):
        resp = client.post(
            "/api/batches/1/manual-rows",
            json={"expense_item": "奖金", "row_amount": 1000.0},
        )
        assert resp.status_code == 401


class TestUpdateManualRowAPI:
    def test_update_manual_row_returns_200(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)
        row_id = client.post(
            f"/api/batches/{batch_id}/manual-rows",
            json={"expense_item": "奖金", "row_amount": 1000.0},
            headers=auth_headers,
        ).json()["id"]

        resp = client.put(
            f"/api/batches/{batch_id}/manual-rows/{row_id}",
            json={"row_amount": 1200.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["row_amount"] == 1200.0
        assert data["unit_price"] == 1200.0

    def test_update_manual_row_partial(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)
        row_id = client.post(
            f"/api/batches/{batch_id}/manual-rows",
            json={"expense_item": "奖金", "row_amount": 1000.0},
            headers=auth_headers,
        ).json()["id"]

        resp = client.put(
            f"/api/batches/{batch_id}/manual-rows/{row_id}",
            json={"remark": "新备注"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["remark"] == "新备注"

    def test_update_manual_row_not_found(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)

        resp = client.put(
            f"/api/batches/{batch_id}/manual-rows/9999",
            json={"row_amount": 999.0},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_manual_row_cannot_edit_invoice_row(self, client, auth_headers):
        from app.models.batch import ReimbursementBatch

        batch_id = _Helpers._create_batch(client, auth_headers)

        resp = client.put(
            f"/api/batches/{batch_id}/manual-rows/9999",
            json={"row_amount": 999.0},
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestDeleteManualRowAPI:
    def test_delete_manual_row_returns_200(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)
        row_id = client.post(
            f"/api/batches/{batch_id}/manual-rows",
            json={"expense_item": "奖金", "row_amount": 1000.0},
            headers=auth_headers,
        ).json()["id"]

        resp = client.delete(
            f"/api/batches/{batch_id}/manual-rows/{row_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] is True
        assert data["released_substitute_count"] == 0

    def test_delete_manual_row_not_found(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)

        resp = client.delete(
            f"/api/batches/{batch_id}/manual-rows/9999",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_delete_manual_row_without_token_returns_401(self, client):
        resp = client.delete(
            "/api/batches/1/manual-rows/1",
        )
        assert resp.status_code == 401