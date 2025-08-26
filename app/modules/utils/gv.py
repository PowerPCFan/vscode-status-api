# global vars
import dotenv
import os

dotenv.load_dotenv()

LOGGER_DISCORD_WEBHOOK_URL: str | None = os.getenv("LOGGER_DISCORD_WEBHOOK_URL", None)
TELEMETRY_DISCORD_WEBHOOK_URL: str | None = os.getenv("TELEMETRY_DISCORD_WEBHOOK_URL", None)
CLOUDFLARE_TUNNEL: bool = (os.getenv("CLOUDFLARE_TUNNEL", "false").lower()) == "true"
RATE_LIMITING: bool = (os.getenv("RATE_LIMITING", "true").lower()) == "true"
