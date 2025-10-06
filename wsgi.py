import os
from dotenv import load_dotenv

# Load .env only when present (useful for local dev)
if os.path.exists(".env"):
    load_dotenv(".env")

from app import create_app

app = create_app()

# Health check endpoint for Cloud Run (fast, no DB work)
@app.get("/healthz")
def health():
    return {"status": "ok"}, 200

# Local dev entrypoint (Cloud Run uses gunicorn, not this block)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

