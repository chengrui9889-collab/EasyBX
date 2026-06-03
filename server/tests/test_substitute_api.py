class _Helpers:
    @staticmethod
    def _create_batch(client, auth_headers):
        resp = client.post(
            "/api/batches/",
            json={"department": "测试部", "reporter": "测试人"},
            headers=auth_headers,
        )
        return resp.json()["id"]

    @staticmethod
    def _add_manual_row(client, auth_headers, batch_id, expense_item, row_amount):
        resp = client.post(
            f"/api/batches/{batch_id}/manual-rows",
            json={"expense_item": expense_item, "row_amount": row_amount},
            headers=auth_headers,
        )
        return resp.json()["id"]

    @staticmethod
    def _create_invoice(db, user_id, invoice_no="12345678", amount=1000.0):
        from app.models.invoice import Invoice

        inv = Invoice(
            user_id=user_id,
            file_path="/tmp/test.pdf",
            status="confirmed",
            amount=amount,
            invoice_no=invoice_no,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        return inv

    @staticmethod
    def _create_substitution(client, auth_headers, db, user_id, batch_id, row_id, invoice_no="12345678", amount=1000.0):
        inv = _Helpers._create_invoice(db, user_id, invoice_no, amount)
        resp = client.post(
            f"/api/batches/{batch_id}/substitutions",
            json={
                "mode": "one_to_one",
                "substitute_invoice_ids": [inv.id],
                "target_row_ids": [row_id],
            },
            headers=auth_headers,
        )
        return resp


class TestAvailableSubstituteInvoicesAPI:
    def test_list_available_returns_200(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)

        resp = client.get(
            f"/api/batches/{batch_id}/available-substitute-invoices",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "items" in resp.json()
        assert "total" in resp.json()

    def test_list_available_with_filters(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)

        resp = client.get(
            f"/api/batches/{batch_id}/available-substitute-invoices?keyword=测试&page=1&page_size=10",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_list_available_batch_not_found(self, client, auth_headers):
        resp = client.get(
            "/api/batches/999/available-substitute-invoices",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_list_available_requires_auth(self, client):
        resp = client.get(
            "/api/batches/1/available-substitute-invoices",
        )
        assert resp.status_code == 401


class TestCreateSubstitutionAPI:
    def test_create_one_to_one_returns_201(self, client, auth_headers, db, test_user):
        from app.models.invoice import Invoice

        inv = Invoice(
            user_id=test_user.id,
            file_path="/tmp/test.pdf",
            status="confirmed",
            amount=1000.0,
            invoice_no="12345678",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        batch_id = _Helpers._create_batch(client, auth_headers)
        row_id = _Helpers._add_manual_row(client, auth_headers, batch_id, "奖金", 1000.0)

        resp = client.post(
            f"/api/batches/{batch_id}/substitutions",
            json={
                "mode": "one_to_one",
                "substitute_invoice_ids": [inv.id],
                "target_row_ids": [row_id],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "relations" in data
        assert "updated_target_rows" in data

    def test_create_substitution_batch_not_found(self, client, auth_headers):
        resp = client.post(
            "/api/batches/999/substitutions",
            json={
                "mode": "one_to_one",
                "substitute_invoice_ids": [1],
                "target_row_ids": [1],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_create_substitution_requires_auth(self, client):
        resp = client.post(
            "/api/batches/1/substitutions",
            json={
                "mode": "one_to_one",
                "substitute_invoice_ids": [1],
                "target_row_ids": [1],
            },
        )
        assert resp.status_code == 401


class TestListSubstitutionsAPI:
    def test_list_empty_returns_200(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)

        resp = client.get(
            f"/api/batches/{batch_id}/substitutions",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "relations" in data
        assert data["relations"] == []

    def test_list_after_create_returns_relations(self, client, auth_headers, db, test_user):
        batch_id = _Helpers._create_batch(client, auth_headers)
        row_id = _Helpers._add_manual_row(client, auth_headers, batch_id, "奖金", 1000.0)
        _Helpers._create_substitution(client, auth_headers, db, test_user.id, batch_id, row_id)

        resp = client.get(
            f"/api/batches/{batch_id}/substitutions",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["relations"]) == 1
        rel = data["relations"][0]
        assert rel["batch_id"] == batch_id
        assert rel["mode"] == "one_to_one"
        assert rel["substitute_invoice"] is not None
        assert rel["target_row"] is not None

    def test_list_batch_not_found(self, client, auth_headers):
        resp = client.get(
            "/api/batches/999/substitutions",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_list_requires_auth(self, client):
        resp = client.get("/api/batches/1/substitutions")
        assert resp.status_code == 401


class TestRemoveSubstitutionAPI:
    def test_remove_returns_200(self, client, auth_headers, db, test_user):
        batch_id = _Helpers._create_batch(client, auth_headers)
        row_id = _Helpers._add_manual_row(client, auth_headers, batch_id, "奖金", 1000.0)
        create_resp = _Helpers._create_substitution(client, auth_headers, db, test_user.id, batch_id, row_id)
        sub_id = create_resp.json()["relations"][0]["id"]

        resp = client.delete(
            f"/api/batches/{batch_id}/substitutions/{sub_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == {"removed": True}

    def test_remove_clears_relation(self, client, auth_headers, db, test_user):
        batch_id = _Helpers._create_batch(client, auth_headers)
        row_id = _Helpers._add_manual_row(client, auth_headers, batch_id, "奖金", 1000.0)
        create_resp = _Helpers._create_substitution(client, auth_headers, db, test_user.id, batch_id, row_id)
        sub_id = create_resp.json()["relations"][0]["id"]

        client.delete(
            f"/api/batches/{batch_id}/substitutions/{sub_id}",
            headers=auth_headers,
        )
        list_resp = client.get(
            f"/api/batches/{batch_id}/substitutions",
            headers=auth_headers,
        )
        assert list_resp.json()["relations"] == []

    def test_remove_nonexistent_returns_404(self, client, auth_headers):
        batch_id = _Helpers._create_batch(client, auth_headers)
        resp = client.delete(
            f"/api/batches/{batch_id}/substitutions/999",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_remove_requires_auth(self, client):
        resp = client.delete("/api/batches/1/substitutions/1")
        assert resp.status_code == 401