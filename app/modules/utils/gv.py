# global vars
import dotenv
import os

dotenv.load_dotenv()

DISCORD_WEBHOOK_URL: str | None = os.getenv("DISCORD_WEBHOOK_URL", None)
CLOUDFLARE_TUNNEL: bool = (os.getenv("CLOUDFLARE_TUNNEL", "false").lower()) == "true"
RATE_LIMITING: bool = (os.getenv("RATE_LIMITING", "true").lower()) == "true"
