import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import models, crud, schemas
from backend.database import Base


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_create_material_and_po(db_session):
    mat_in = schemas.MaterialCreate(name="TestMat", description="t", unit_price=2.5)
    mat = crud.create_material(db_session, mat_in)
    assert mat.id is not None
    assert mat.name == "TestMat"

    po_in = schemas.PurchaseOrderCreate(material_id=mat.id, quantity=4)
    po = crud.create_purchase_order(db_session, po_in)
    assert po.id is not None
    assert po.total_price == pytest.approx(2.5 * 4)


def test_update_po_recalculates_total(db_session):
    mat = crud.create_material(db_session, schemas.MaterialCreate(name="M2", description=None, unit_price=3.0))
    po = crud.create_purchase_order(db_session, schemas.PurchaseOrderCreate(material_id=mat.id, quantity=2))
    updated = crud.update_purchase_order(db_session, po.id, {"quantity": 5})
    assert updated.quantity == 5
    assert updated.total_price == pytest.approx(3.0 * 5)
