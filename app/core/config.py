import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", "nilla_sarres")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID_HERE")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@nillasarres.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "NillaAdmin@123")

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
