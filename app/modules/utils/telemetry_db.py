from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, sessionmaker
from .logger import logger


class Base(DeclarativeBase):
    pass


class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True)
    ip: Mapped[str] = MappedColumn(String(45), nullable=False)
    endpoint: Mapped[str] = MappedColumn(String(255), nullable=False)
    method: Mapped[str] = MappedColumn(String(10), nullable=False)
    status: Mapped[int] = MappedColumn(Integer, nullable=False)
    timestamp: Mapped[int] = MappedColumn(Integer, default=lambda: int(datetime.now(timezone.utc).timestamp()), index=True)


class WebhookTracker(Base):
    __tablename__ = "webhook_tracker"

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = MappedColumn(String(20), nullable=False)
    period: Mapped[str] = MappedColumn(String(20), nullable=False)
    last_sent: Mapped[int] = MappedColumn(Integer, default=0, index=True)


class Database:
    def __init__(self, db_file: str = "telemetry.db"):
        self.db_file = f"sqlite:///{Path(__file__).resolve().parent.parent.parent.parent / 'data' / db_file}"
        self.engine = create_engine(self.db_file, echo=False, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self._init_database()

    def _init_database(self):
        try:
            Base.metadata.create_all(bind=self.engine, checkfirst=True)
            logger.info("Telemetry database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize telemetry database: {e}")

    def get_session(self):
        return self.SessionLocal()

    def log_request(self, ip: str, endpoint: str, method: str, status: int):
        with self.SessionLocal() as session:
            try:
                session.add(Telemetry(
                    ip=ip,
                    endpoint=endpoint,
                    method=method,
                    status=status,
                    timestamp=int(datetime.now(timezone.utc).timestamp())
                ))
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to log telemetry: {e}")


# global instance
db = Database()
