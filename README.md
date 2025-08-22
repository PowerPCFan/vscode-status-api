# vscode-status-api

A companion API for my vscode-status-extension VSCode extension.

## API endpoints:

> [!TIP]
> Use the /get-status endpoint along with ?userId=YOUR_USER_ID (found in settings of the extension) to retrieve your VSCode status to be displayed on your website!

- GET `https://vscode-status.powerpcfan.xyz/` - health check endpoint, returns `{"message": "OK"}` if OK
- POST `https://vscode-status.powerpcfan.xyz/update-status` - update's user's status. Requires token and user ID. 
- GET `https://vscode-status.powerpcfan.xyz/get-status` - retrieves the user's status from the API. You only need the user ID.
- POST `https://vscode-status.powerpcfan.xyz/register-user` - registers a new user in the database.

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
      - `DISCORD_WEBHOOK_URL` - Optional URL for a Discord webhook to send API logs to.
      - `CLOUDFLARE_TUNNEL` - Set to `"true"` if you are using a Cloudflare tunnel, `"false"` (default) if not.
      - `RATE_LIMITING` - Set to `"true"` to enable IP-based rate limiting, `"false"` to disable it. If you choose to use rate limiting you will need Memcached running on port 11211 (use WSL or Docker if on Windows). **(!! Read warning at the top of this section !!)**
4. `cd` the `./app` directory, then run the app using `gunicorn main:app --bind 0.0.0.0:5000 --workers 4` if you need a production WSGI server, or `python3 main.py` \> follow on-screen instructions if you just want a development server.
