import time
from threading import Thread
from tzlocal import get_localzone
from zoneinfo import ZoneInfo
from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import select, func, desc
from .telemetry_db import Telemetry, WebhookTracker, db
from .webhook_sender import send
from .logger import logger


EVERY_3_MINUTES_ENABLED = False  # enable for debug only

try:
    LOCAL_TIMEZONE = ZoneInfo(get_localzone().key)
except Exception:
    LOCAL_TIMEZONE = timezone.utc


class ReportType(Enum):
    IPS = "ips"
    ENDPOINTS = "endpoints"
    ENDPOINTS_BY_IPS = "endpoints-by-ips"


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


def send_list(type_: ReportType, period: str, url: str, start_ts: int, end_ts: int):
    with db.SessionLocal() as session:
        if type_ == ReportType.IPS:
            results = session.execute(
                select(Telemetry.ip, func.count(Telemetry.id).label("hits"))
                .where(Telemetry.timestamp >= start_ts)
                .where(Telemetry.timestamp <= end_ts)
                .group_by(Telemetry.ip)
                .order_by(desc(func.count(Telemetry.id)))
            ).all()
            title = "IPs"
            lines = [f"- `{str(r.ip)}`: {str(r.hits)} request{'' if int(r.hits) == 1 else 's'}" for r in results]

        elif type_ == ReportType.ENDPOINTS:
            results = session.execute(
                select(Telemetry.endpoint, func.count(Telemetry.id).label("hits"))
                .where(Telemetry.timestamp >= start_ts)
                .where(Telemetry.timestamp <= end_ts)
                .group_by(Telemetry.endpoint)
                .order_by(desc(func.count(Telemetry.id)))
            ).all()

            title = "Endpoints"
            lines = [f"- `{r.endpoint}`: {str(r.hits)} request{'' if int(r.hits) == 1 else 's'}" for r in results]

        elif type_ == ReportType.ENDPOINTS_BY_IPS:
            results = session.execute(
                select(
                    Telemetry.ip,
                    Telemetry.endpoint,
                    func.count(Telemetry.id).label("hits"),
                )
                .where(Telemetry.timestamp >= start_ts)
                .where(Telemetry.timestamp <= end_ts)
                .group_by(Telemetry.ip, Telemetry.endpoint)
            ).all()

            by_ip: dict[str, dict[str, int]] = {}
            totals: dict[str, int] = {}

            for r in results:
                by_ip.setdefault(r.ip, {})[r.endpoint] = int(r.hits)
                totals[r.ip] = totals.get(r.ip, 0) + int(r.hits)

            sorted_ips = sorted(totals.keys(), key=lambda ip: (-totals[ip], ip))

            title = "Endpoints by IPs"
            lines = []
            for ip in sorted_ips:
                lines.append(f"- `{ip}`")
                for endpoint, hits in sorted(by_ip[ip].items(), key=lambda kv: (-kv[1], kv[0])):
                    lines.append(f"  - `{endpoint}`: {str(hits)} request{'' if int(hits) == 1 else 's'}")

    date_str = datetime.fromtimestamp(end_ts, tz=LOCAL_TIMEZONE).strftime(f"%m/%d/%Y, %H:%M Local Time")
    header = f"# Telemetry: {title} ({date_str})\n"
    content = header + "\n".join(lines)
    chunks = chunk_text(content)

    for chunk in chunks:
        send(url, chunk)
        time.sleep(1)  # rate limit avoidance

    now_ts = int(datetime.now(timezone.utc).timestamp())
    with db.SessionLocal() as session:
        tracker = session.execute(
            select(WebhookTracker)
            .where(WebhookTracker.type == type_.value)
            .where(WebhookTracker.period == period)
        ).scalars().first()

        if tracker:
            tracker.last_sent = now_ts
            session.commit()
            logger.info(f"Updated {period} {type_.value} tracker - last sent: {tracker.last_sent}")
        else:
            new_tracker = WebhookTracker(type=type_.value, period=period, last_sent=now_ts)
            session.add(new_tracker)
            session.commit()
            logger.info(f"Created new {period} {type_.value} tracker")

def check_and_send_report(period: str, type_: ReportType, url: str):
    now = datetime.now(timezone.utc)
    now_ts = int(now.timestamp())

    with db.SessionLocal() as session:
        tracker = session.execute(
            select(WebhookTracker)
            .where(WebhookTracker.type == type_.value)
            .where(WebhookTracker.period == period)
        ).scalars().first()

        last_sent = tracker.last_sent if tracker else 0

        if now_ts - last_sent >= (3 * 60 if period == "every-3-minutes" else 4 * 60 * 60):
            logger.info(f"Sending {period} {type_.value} report...")
            send_list(type_, period, url, start_ts=last_sent, end_ts=now_ts)

def _start_telemetry(url: str):
    CHECK_INTERVAL = 5 * 60

    while True:
        try:
            for type_ in ReportType:
                check_and_send_report("6-intervals", type_, url)

                if EVERY_3_MINUTES_ENABLED:
                    check_and_send_report("every-3-minutes", type_, url)

            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Error in telemetry loop: {e}")
            time.sleep(10)

def start_telemetry(url: str | None = None):
    try:
        if url:
            telemetry_thread = Thread(target=_start_telemetry, args=(url,), daemon=True)
            telemetry_thread.start()
            logger.info("Telemetry system started successfully!")
    except Exception as e:
        logger.error(f"Error starting telemetry system: {e}")


if __name__ == "__main__":
    print("This file is not meant to be run directly. Please import it and use start_telemetry().")
