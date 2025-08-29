# vscode-status-api

A companion API for my vscode-status-extension VSCode extension. [Download the extension here!](https://marketplace.visualstudio.com/items?itemName=powerpcfan.vscode-status-extension)

My public instance of the API is https://vscode-status.powerpcfan.xyz/ . I have rate limited all the endpoints on an IP basis to avoid abuse.

## API endpoints:

> [!NOTE]
> Generally, the GET endpoints only require a user ID or no form of authentication, and the POST/DELETE endpoints require a user ID and token.

#### GET
- `/` (health check endpoint, returns `{"message": "OK"}` if OK)
- `/trigger-rate-limit` (endpoint meant to test rate limiter - limited to 1 request/min - **this endpoint only exists if rate limiting is enabled in .env**)
- `/get-status` (retrieves the user's status from the API. You only need the user ID.)
- `/check-if-user-exists` (checks if a user exists. Requires user ID.)

#### POST
- `/update-status` (update's user's status. Requires token and user ID.)
- `/register-user` (registers a new user. Requires user ID and auth token.)

#### DELETE
- `/delete-user` (deletes a user. Requires user ID and auth token.)

## Expected request body for POST endpoints
didnt write this part yet

## Self-hosting instructions:

> [!WARNING]
> This API uses rate limiting through Flask-Limiter, but most proxying and tunneling services interfere with this, since it uses IP-based limiting. 
> 
> If you are using Cloudflare Tunnel, set the CLOUDFLARE_TUNNEL value to `"true"` (explained below), and if you are using a different proxying/tunneling service, disable rate limiting entirely (also explained below).

1. Clone the repository
2. Install requirements.txt
3. Set up .env file:
   1. Copy .env.example to .env
   2. Fill in the required values:
   - `LOGGER_DISCORD_WEBHOOK_URL` - Optional URL for a Discord webhook. When set, the API will capture all stdout and stderr (including logs and print statements) and forward them to the webhook in small batches.
   - `TELEMETRY_DISCORD_WEBHOOK_URL` - Optional URL for a Discord webhook to send telemetry data. Also serves as a boolean for whether telemetry is enabled or not (empty string = false, url provided = true)
   - `CLOUDFLARE_TUNNEL` - Set to `"true"` if you are using a Cloudflare tunnel, `"false"` (default) if not.
   - `RATE_LIMITING` - Set to `"true"` to enable IP-based rate limiting, `"false"` to disable it. If you choose to use rate limiting you will need Memcached running on port 11211 (use WSL or Docker if on Windows). **(!! Read warning at the top of this section !!)**
4. `cd` the `./app` directory, then run the app using `gunicorn main:app --bind 0.0.0.0:5000 --workers 4` if you need a production WSGI server, or `python3 main.py` \> follow on-screen instructions if you just want a development server.
