from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from sgpt.web.adapter import WebProviderAdapter
import time

class ChatGPTProvider(WebProviderAdapter):
    @property
    def url(self) -> str:
        return "https://chatgpt.com"

    def preflight_check(self, page: Page) -> bool:
        try:
            # Check for input area
            if not page.is_visible("#prompt-textarea", timeout=10000):
                return False
            # Check if we are logged in (if login button is visible, we are NOT ready)
            if page.is_visible("button[data-testid='login-button']"):
                return False
            return True
        except Exception:
            return False

    def send_prompt(self, page: Page, prompt: str) -> None:
        page.fill("#prompt-textarea", prompt)
        # Using Enter to send is often more reliable than finding the button which might change
        page.keyboard.press("Enter")

    def wait_for_response(self, page: Page) -> None:
        # Strategy: Wait for "Stop generating" button to appear, then disappear.
        # This confirms generation started and finished.
        # Fallback: Wait for send button to be enabled? ChatGPT send button isn't always distinct.
        # Better: Wait for the streaming class/attribute to vanish.
        # ChatGPT adds `.result-streaming` to the message div? No.
        
        # Robust strategy:
        # 1. Wait for something new to appear (assistant message).
        # 2. Wait for "Stop generating" (data-testid="stop-button") to appear (generation active).
        # 3. Wait for "Stop generating" to disappear.
        
        try:
            # Wait for generation to start (stop button appears)
            page.wait_for_selector("[data-testid='stop-button']", timeout=8000)
            # Wait for generation to finish (stop button disappears)
            page.wait_for_selector("[data-testid='stop-button']", state="hidden", timeout=120000) # 2 min timeout
        except PlaywrightTimeoutError:
            # If we missed the start (fast response), check if input is enabled/ready?
            pass

    def extract_response(self, page: Page) -> str:
        # Get the last assistant message
        # ChatGPT structure: user message, assistant message...
        # Selector for assistant response: .markdown (usually)
        # Be careful not to get user message (which might also be markdown in some UI versions, but usually distinct)
        # Typical selector: [data-message-author-role="assistant"] .markdown
        
        try:
            responses = page.locator('[data-message-author-role="assistant"] .markdown')
            count = responses.count()
            if count > 0:
                return responses.nth(count - 1).inner_text()
            return ""
        except Exception:
            return "Error extracting response."
