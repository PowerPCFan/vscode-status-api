from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy import String, JSON, create_engine, select
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, MappedColumn, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from modules.utils.logger import logger


#* notice to anyone reading this code:
#* this is my first time ever using SQL and SQLAlchemy, 
#* and I'm pretty sure I used some outdated functions
#* and mixed SQLAlchemy 1.0 and 2.0 stuff,
#* and "core" and ORM stuff


def DATETIME_NOW() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    # user id and auth token can be changed by the user in the extension so i dont want to enforce a strict limit,
    # but i figured 32 chars for user id and 128 chars for token are reasonable limits regardless of what the user inputs
    user_id: Mapped[str] = MappedColumn(String(32), primary_key=True)
    auth_token: Mapped[str] = MappedColumn(String(128), nullable=False)

    created_at: Mapped[str] = MappedColumn(String, default=DATETIME_NOW)
    last_updated: Mapped[str | None] = MappedColumn(String, nullable=True)
    status_data: Mapped[dict[str, Any]] = MappedColumn(JSON, default="{}")


class Database:
    def __init__(self, db_file: str = "user_statuses.db"):
        self.db_file = f"sqlite:///{Path(__file__).resolve().parent.parent.parent.parent / "data" / db_file}"

        self.engine = create_engine(self.db_file, echo=False, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

        self._init_database()

    def _init_database(self):
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def _select_user_by_user_id(self, session: Session, user_id: str) -> User | None:
        user = session.execute(select(User).where(User.user_id == user_id)).scalar_one_or_none()
        return user

    def _create_user(self, session: Session, user_id: str, auth_token: str, status_data: Optional[Dict[str, Any]] = None, set_last_updated: bool = False) -> None:
        now: str = DATETIME_NOW()

        user = User(
            user_id=user_id,
            auth_token=auth_token,
            created_at=now,
            status_data=status_data if status_data is not None else "{}"
        )

        if set_last_updated and status_data is not None:
            user.last_updated = now

        try:
            session.add(user)
            session.flush() # apparently im supposed to flush here instead of commit 
        except Exception as e:
            logger.error(f"Failed to create user {user_id}: {e}")
            raise

    def _update_user_status(self, session: Session, user_id: str, status_data: Dict[str, Any]) -> None:
        user = self._select_user_by_user_id(session, user_id)
        if user:
            user.status_data = status_data
            user.last_updated = DATETIME_NOW()
            session.commit()

    def authenticate_user(self, session: Session, user_id: str, auth_token: str) -> bool:
        try:
            user = self._select_user_by_user_id(session, user_id)
            if not user:
                return False
            return user.auth_token == auth_token
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def update_status(self, user_id: str, auth_token: str, status_data: Dict[str, Any]) -> tuple[bool, str, bool]:
        try:
            with self.SessionLocal() as session:
                if self._user_exists(session, user_id):
                    if not self.authenticate_user(session, user_id, auth_token):
                        return False, "Authentication failed: Invalid user ID or token", False

                    self._update_user_status(session, user_id, status_data)
                    session.commit()
                    return True, "Status updated successfully", False
                else:
                    # User doesn't exist - return error instead of creating new user
                    return False, "User not found: Please register first before updating status", False

        except SQLAlchemyError as e:
            logger.error(f"Failed to update status for user {user_id}: {e}")
            return False, "Database error: Failed to save status", False

    def register_user(self, user_id: str, auth_token: str) -> tuple[bool, str]:
        try:
            with self.SessionLocal() as session:
                if self._user_exists(session, user_id):
                    return False, "User already exists"

                try:
                    self._create_user(session, user_id, auth_token)
                except IntegrityError:
                    return False, "User already exists"

                session.commit()
                return True, "User registered successfully"
        except SQLAlchemyError as e:
            logger.error(f"Failed to register user {user_id}: {e}")
            return False, "Database error: Failed to register user"

    def get_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            self.cleanup_old_status(user_id)

            with self.SessionLocal() as session:
                user = self._select_user_by_user_id(session, user_id)

                if user is None:
                    return None

                try:
                    status = user.status_data
                except Exception:
                    status = {}

                if not status or user.last_updated is None:
                    return {
                        'user_id': user.user_id,
                        'status': {}
                    }

                return {
                    'user_id': user.user_id,
                    'status': status,
                    'last_updated': user.last_updated,
                    'created_at': user.created_at
                }

        except SQLAlchemyError as e:
            logger.error(f"Failed to get status for user {user_id}: {e}")
            return None

    def _user_exists(self, session: Session, user_id: str) -> bool:
        try:
            return self._select_user_by_user_id(session, user_id) is not None
        except SQLAlchemyError as e:
            logger.error(f"Failed to check if user exists {user_id}: {e}")
            return False

    def cleanup_old_status(self, user_id: str, max_age_minutes: int = 10) -> bool:
        try:
            with self.SessionLocal() as session:
                user = self._select_user_by_user_id(session, user_id)

                if user is None:
                    return False

                last_updated = user.last_updated

                if last_updated is None:
                    user.status_data = {}
                    user.last_updated = None

                    session.commit()
                    logger.info(f"Cleared status data for user {user_id} with NULL last_updated timestamp")
                    return True
                
                # Parse the timestamp and check if it's older than the cutoff
                last_updated_time = datetime.fromisoformat(last_updated)
                cutoff_time = datetime.now(tz=timezone.utc) - timedelta(minutes=max_age_minutes)

                if last_updated_time < cutoff_time:
                    user.status_data = {}
                    user.last_updated = None

                    session.commit()
                    logger.info(f"Cleared status data for inactive user {user_id} (last updated: {last_updated}, older than {max_age_minutes} minutes)")
                    return True
                else:
                    return False

        except SQLAlchemyError as e:
            logger.error(f"Failed to cleanup old status for user {user_id}: {e}")
            return False


db = Database()
