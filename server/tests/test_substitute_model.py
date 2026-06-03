import pytest

from sqlalchemy import text


class TestSubstituteRelationModel:
    def test_create_one_to_one(self, db):
        from app.models.substitute import SubstituteRelation

        rel = SubstituteRelation(
            batch_id=1,
            substitute_invoice_id=10,
            target_row_id=1,
            mode="one_to_one",
        )
        db.add(rel)
        db.commit()
        db.refresh(rel)

        assert rel.id is not None
        assert rel.batch_id == 1
        assert rel.substitute_invoice_id == 10
        assert rel.target_row_id == 1
        assert rel.mode == "one_to_one"
        assert rel.created_at is not None

    def test_create_all_modes(self, db):
        from app.models.substitute import SubstituteRelation

        for mode in ["one_to_one", "one_to_many", "many_to_one"]:
            rel = SubstituteRelation(
                batch_id=1,
                substitute_invoice_id=10,
                target_row_id=1,
                mode=mode,
            )
            db.add(rel)
            db.commit()
            db.refresh(rel)
            assert rel.mode == mode

    def test_cascade_on_target_row_delete(self, db):
        from app.models.batch import BatchInvoice
        from app.models.substitute import SubstituteRelation

        bi = BatchInvoice(
            batch_id=1,
            source_type="manual",
            row_amount=1000.0,
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)

        rel = SubstituteRelation(
            batch_id=1,
            substitute_invoice_id=10,
            target_row_id=bi.id,
            mode="one_to_one",
        )
        db.add(rel)
        db.commit()

        db.execute(text("PRAGMA foreign_keys = ON"))
        db.delete(bi)
        db.commit()

        rels = db.query(SubstituteRelation).filter(
            SubstituteRelation.target_row_id == bi.id
        ).all()
        assert len(rels) == 0

    def test_indexes_exist(self, db):
        from sqlalchemy import inspect
        from app.models.substitute import SubstituteRelation

        inspector = inspect(db.bind)
        indexes = inspector.get_indexes("substitute_relations")
        index_names = [idx["name"] for idx in indexes]

        assert "ix_substitute_relations_batch_id" in index_names
        assert "ix_substitute_relations_substitute_invoice_id" in index_names
        assert "ix_substitute_relations_target_row_id" in index_names