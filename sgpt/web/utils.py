import json
import typer
from sgpt.web.config import WEB_CONFIG_DIR

CONSENT_FILE = WEB_CONFIG_DIR / "consent.json"

def check_consent() -> bool:
    if CONSENT_FILE.exists():
        try:
            with open(CONSENT_FILE, "r") as f:
                data = json.load(f)
                if data.get("consented"):
                    return True
        except Exception:
            pass
            
    # Prompt
    typer.echo("")
    typer.secho("⚠️  Web Automation Enabled", fg="yellow", bold=True)
    typer.echo("This experimental feature uses your real browser session via Playwright.")
    typer.echo("It will launch a visible browser window, use your logged-in session, and perform actions.")
    typer.echo("This may violate provider Terms of Service.")
    
    confirm = typer.confirm("Do you validly consent to use this feature?", default=False)
    
    if confirm:
        WEB_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONSENT_FILE, "w") as f:
            json.dump({"consented": True}, f)
        return True
    
    return False
