from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.db.base import NAMING_CONVENTION


def test_constraint_naming_convention():
    """Verify constraint naming convention compiles correctly for PostgreSQL dialect."""
    # Check that the pk entry ends with )s
    assert NAMING_CONVENTION["pk"].endswith(")s")
    assert NAMING_CONVENTION["pk"] == "pk_%(table_name)s"

    # Build a throwaway table structure on a copy of metadata using the convention
    meta = MetaData(naming_convention=NAMING_CONVENTION)

    parent = Table(
        "parent",
        meta,
        Column("id", Integer, primary_key=True),
        Column("code", String, unique=True),
    )

    child = Table(
        "child",
        meta,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer, ForeignKey("parent.id")),
    )

    parent_ddl = str(CreateTable(parent).compile(dialect=postgresql.dialect()))
    child_ddl = str(CreateTable(child).compile(dialect=postgresql.dialect()))

    # Verify primary key constraints follow pk_%(table_name)s
    assert "CONSTRAINT pk_parent PRIMARY KEY (id)" in parent_ddl
    assert "CONSTRAINT pk_child PRIMARY KEY (id)" in child_ddl

    # Verify unique constraint follows uq_%(table_name)s_%(column_0_name)s
    assert "CONSTRAINT uq_parent_code UNIQUE (code)" in parent_ddl

    # Verify foreign key follows fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s
    assert "CONSTRAINT fk_child_parent_id_parent FOREIGN KEY(parent_id) REFERENCES parent (id)" in child_ddl


def test_db_session_executes_select_one_and_closes(db_session):
    """Database session can execute SELECT 1 and is closed after use."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1

    result2 = db_session.execute(text("SELECT 2")).scalar()
    assert result2 == 2
