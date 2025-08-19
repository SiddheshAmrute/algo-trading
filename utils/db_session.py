from contextlib import contextmanager
from db.init_db import SessionLocal


@contextmanager
def get_db_session():
    """
    Provides a transactional scope for SQLAlchemy session.

    Example:
        with get_db_session() as session:
            users = session.query(User).all()
            session.add(new_trade)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()  # ✅ commit if all went well
    except Exception:
        session.rollback()  # ✅ rollback on error
        raise
    finally:
        session.close()  # ✅ always close to free resources
