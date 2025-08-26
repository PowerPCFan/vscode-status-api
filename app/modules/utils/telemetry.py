# this is mostly chatgpt since i couldnt figure it out for the life of me

import time
from threading import Thread
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, desc, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .telemetry_db import Telemetry, Base, db
from .webhook_sender import send
from .logger import logger

# Toggle for debugging
EVERY_3_MINUTES_ENABLED = False

# Add index for timestamp
Index("ix_telemetry_timestamp", Telemetry.timestamp)


class WebhookTracker(Base):
    __tablename__ = "webhook_tracker"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    last_sent: Mapped[int] = mapped_column(Integer, default=0, index=True)  # store as UNIX timestamp


def chunk_text(text: str, max_len: int = 1800) -> list[str]:
    lines = text.split("\n")
    chunks, current = [], ""

    for line in lines:
        if len(line) > max_len:
            if current:
                chunks.append(current.rstrip("\n"))
                current = ""
            for i in range(0, len(line), max_len):
                chunks.append(line[i:i + max_len])
        else:
            if len(current) + len(line) + 1 > max_len:
                chunks.append(current.rstrip("\n"))
                current = line + "\n"
            else:
                current += line + "\n"

    if current:
        chunks.append(current.rstrip("\n"))
    return chunks


def get_period_range(period: str):
    now = datetime.now(tz=timezone.utc)
    now_ts = int(now.timestamp())

    if period == "daily":
        start_ts = int((now - timedelta(days=1)).timestamp())
    elif period == "weekly":
        days_since_monday = now.weekday()
        start_ts = int((now - timedelta(days=days_since_monday + 7)).timestamp())
    elif period == "monthly":
        if now.month == 1:
            start = datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
        else:
            start = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)
        start_ts = int(start.timestamp())
    elif period == "6-intervals":
        start_ts = int((now - timedelta(hours=4)).timestamp())  # just last 4 hours window
        now_ts += 5  # small buffer for latest data
    elif period == "every-3-minutes":
        start_ts = int((now - timedelta(minutes=3)).timestamp())
        now_ts += 2  # tiny buffer
    else:
        raise ValueError(f"Unknown period: {period}")

    return start_ts, now_ts


def send_top_list(type_: str, period: str, url: str):
    start_ts, end_ts = get_period_range(period)

    with db.SessionLocal() as session:
        if type_ == "IPs":
            stmt = (
                select(Telemetry.ip, func.count(Telemetry.id).label("hits"))
                .where(Telemetry.timestamp >= start_ts)
                .where(Telemetry.timestamp <= end_ts)
                .group_by(Telemetry.ip)
                .order_by(desc(func.count(Telemetry.id)))
            )
            results = session.execute(stmt).all()
            title = "Top IPs"
            lines = [f"- {r.ip}: {r.hits} requests" for r in results]

        elif type_ == "Endpoints":
            stmt = (
                select(Telemetry.endpoint, func.count(Telemetry.id).label("hits"))
                .where(Telemetry.timestamp >= start_ts)
                .where(Telemetry.timestamp <= end_ts)
                .group_by(Telemetry.endpoint)
                .order_by(desc(func.count(Telemetry.id)))
            )
            results = session.execute(stmt).all()
            title = "Top Endpoints"
            lines = [f"- `{r.endpoint}`: {r.hits} requests" for r in results]

        else:
            raise ValueError(f"Unknown type: {type_}")

    date_str = datetime.fromtimestamp(end_ts, tz=timezone.utc).strftime("%m/%d/%Y")
    header = f"# {period.capitalize()} {title} ({date_str})\n"
    content = header + "\n".join(lines)
    chunks = chunk_text(content)

    for chunk in chunks:
        send(url, chunk)

    now_ts = int(datetime.now(timezone.utc).timestamp())
    with db.SessionLocal() as session:
        tracker = (
            session.execute(
                select(WebhookTracker)
                .where(WebhookTracker.type == type_)
                .where(WebhookTracker.period == period)
            )
            .scalars()
            .first()
        )

        if tracker:
            tracker.last_sent = now_ts
            session.commit()
            logger.info(f"Updated {period} {type_} tracker - last sent: {tracker.last_sent}")
        else:
            new_tracker = WebhookTracker(type=type_, period=period, last_sent=now_ts)
            session.add(new_tracker)
            session.commit()
            logger.info(f"Created new {period} {type_} tracker")


def check_and_send_report(period: str, type_: str, url: str):
    start_ts, _ = get_period_range(period)

    with db.SessionLocal() as session:
        tracker = (
            session.execute(
                select(WebhookTracker)
                .where(WebhookTracker.type == type_)
                .where(WebhookTracker.period == period)
            )
            .scalars()
            .first()
        )

        if not tracker:
            now = datetime.now(timezone.utc)
            if period == "6-intervals":
                interval_hours = 24 // 6
                last_interval_hour = (now.hour // interval_hours) * interval_hours
                last_ts = int(now.replace(hour=last_interval_hour, minute=0, second=0, microsecond=0).timestamp())
            elif period == "every-3-minutes":
                last_ts = int((now - timedelta(minutes=3)).timestamp())
            else:
                last_ts = 0

            tracker = WebhookTracker(type=type_, period=period, last_sent=last_ts)
            session.add(tracker)
            session.commit()

        if tracker.last_sent < start_ts:
            logger.info(f"Sending {period} {type_} report...")
            send_top_list(type_, period, url)

def _start_telemetry(url: str):
    CHECK_INTERVAL = 2 * 60  # 2 minutes
    TARGET_HOUR = 17
    logger.info(f"Telemetry system started - reports will be sent daily at {TARGET_HOUR}:00 UTC")

    while True:
        try:
            now = datetime.now(timezone.utc)

            # 6 intervals
            for type_ in ["IPs", "Endpoints"]:
                check_and_send_report("6-intervals", type_, url)

            # every 3 minutes (debug)
            if EVERY_3_MINUTES_ENABLED:
                for type_ in ["IPs", "Endpoints"]:
                    check_and_send_report("every-3-minutes", type_, url)

            # daily/weekly/monthly reports
            if now.hour == TARGET_HOUR and 0 <= now.minute < 5:
                logger.info(f"Target time reached ({TARGET_HOUR}:00 UTC), checking for reports to send...")
                for period in ["daily", "weekly", "monthly"]:
                    for type_ in ["IPs", "Endpoints"]:
                        check_and_send_report(period, type_, url)
                time.sleep(10 * 60)  # avoid duplicates in same window
            else:
                time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logger.error(f"Error in telemetry loop: {e}")
            time.sleep(10)


def start_telemetry(url: str | None = None):
    if url:
        Base.metadata.create_all(db.engine)
        telemetry_thread = Thread(target=_start_telemetry, args=(url,), daemon=True)
        telemetry_thread.start()


if __name__ == "__main__":
    print("This file is not meant to be run directly. Please import it and use start_telemetry().")
