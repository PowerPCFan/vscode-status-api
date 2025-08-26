from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, Integer, String, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .logger import logger


class Base(DeclarativeBase):
    pass


class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[int] = mapped_column(
        Integer, 
        default=lambda: int(datetime.now(timezone.utc).timestamp()),
        index=True
    )

    __table_args__ = (
        Index("ix_telemetry_timestamp", "timestamp"),
    )


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
            if "index ix_telemetry_timestamp already exists" in str(e):
                # this is just a race condition for creating the index which can happen when using multiple workers
                pass
            else:
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
