from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from sgpt.web.adapter import WebProviderAdapter
import time

class ClaudeProvider(WebProviderAdapter):
    @property
    def url(self) -> str:
        return "https://claude.ai"

    def preflight_check(self, page: Page) -> bool:
        try:
            # Check for input
            if not page.is_visible("div[contenteditable='true']", timeout=5000):
                return False
             # Claude often has a specific new chat button or login gate
            if "login" in page.url:
                return False
            return True
        except Exception:
            return False

    def send_prompt(self, page: Page, prompt: str) -> None:
        page.click("div[contenteditable='true']")
        page.keyboard.type(prompt)
        page.keyboard.press("Enter")
        
        # Check if we hit message limit? (Future)

    def wait_for_response(self, page: Page) -> None:
        # Claude shows a typing indicator or "Stop" button.
        # Often has a specific class for the "Generating" state.
        
        try:
             # Wait for response text to appear
             page.wait_for_timeout(2000)
             # Wait for cursor to stop blinking?
             # Simple wait for now.
             page.wait_for_timeout(5000)
        except Exception:
            pass

    def extract_response(self, page: Page) -> str:
        try:
            # Select messages.
            # Usually .font-claude-message or similar.
            # Look for specific container: .ChatMessage_content__...
            # This is hard to guess.
            
            # Use specific hierarchy if possible.
            responses = page.locator(".font-claude-message")
            count = responses.count()
            if count > 0:
                # The last one might be empty if streaming? 
                # Or the last one is the assistant.
                # Claude alternates User / Assistant.
                return responses.nth(count - 1).inner_text()
            return ""
        except Exception:
            return "Error extracting response (Claude selectors need update)."
