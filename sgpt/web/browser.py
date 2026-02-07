from playwright.sync_api import sync_playwright
import typer
from sgpt.web.config import get_profile_dir
from sgpt.web.providers.chatgpt import ChatGPTProvider
from sgpt.web.providers.gemini import GeminiProvider
from sgpt.web.providers.claude import ClaudeProvider

class BrowserSession:
    def __init__(self, provider_name: str = "chatgpt"):
        # Normalize provider name
        provider_name = provider_name.lower()
        self.provider_name = provider_name
        self.profile_path = get_profile_dir(provider_name)
        
        if provider_name == "chatgpt":
            self.adapter = ChatGPTProvider()
        elif provider_name == "gemini":
            self.adapter = GeminiProvider()
        elif provider_name == "claude":
            self.adapter = ClaudeProvider()
        else:
            raise ValueError(f"Provider {provider_name} not implemented yet.")
        self.browser = None
        self.page = None
        self.playwright_context = None

    def start(self):
        """Launches the persistent browser session."""
        if self.browser:
            return

        self.playwright_context = sync_playwright()
        self.playwright = self.playwright_context.start()

        # Try to launch branded browsers first to avoid Cloudflare detection
        # Priority: Chrome -> Edge -> Bundled Chromium
        channels = ["chrome", "msedge", None]
        
        for channel in channels:
            try:
                typer.echo(f"Attempting to launch browser ({channel or 'bundled chromium'})...")
                self.browser = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=self.profile_path,
                    headless=False,
                    channel=channel,
                    args=[
                        "--start-maximized", 
                        "--no-sandbox", 
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars"
                    ],
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                break 
            except Exception as e:
                typer.echo(f"  Failed: {e}")
                continue
        
        if not self.browser:
            raise RuntimeError("Could not launch any browser (Chrome, Edge, or Chromium).")
        
        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
        
        # Navigate & Preflight
        typer.echo(f"Opening {self.adapter.url}...")
        self.page.goto(self.adapter.url)
        
        while not self.adapter.preflight_check(self.page):
            typer.secho("Preflight check failed.", fg="red")
            typer.echo("Please ensure you are logged in and the chat interface is visible.")
            
            try:
                # Wait for user confirmation
                choice = typer.prompt("Login manually then press Enter to retry (or type 'exit' to abort)", default="")
                if choice.lower() in ("exit", "quit"):
                    raise RuntimeError("Aborted by user.")
            except typer.Abort:
                 raise RuntimeError("Aborted by user.")
                 
            # After Enter, loop continues and checks again checking


    def send_prompt(self, prompt: str) -> str:
        """Sends a prompt and returns the response."""
        if not self.browser or not self.page:
            raise RuntimeError("Session not started.")
            
        typer.echo("Sending prompt...")
        self.adapter.send_prompt(self.page, prompt)
        
        typer.echo("Waiting for response...")
        self.adapter.wait_for_response(self.page)
        
        return self.adapter.extract_response(self.page)

    def close(self):
        """Closes the browser session."""
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

    def run(self, prompt: str) -> str:
        """Wrapper for one-off execution."""
        try:
            self.start()
            return self.send_prompt(prompt)
        finally:
            self.close()

