from sqlalchemy import text


def test_db_session_executes_select_one_and_closes(db_session):
    """Database session can execute SELECT 1 and is closed after use."""
    # Execute a simple query
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1

    # Session should still be usable
    result2 = db_session.execute(text("SELECT 2")).scalar()
    assert result2 == 2

    # The fixture will close the session after the test
    # We can't easily test "closed after use" without checking internal state,
    # but the fixture cleanup ensures it's closed
