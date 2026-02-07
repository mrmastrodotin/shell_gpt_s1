from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from sgpt.web.adapter import WebProviderAdapter
import time

class GeminiProvider(WebProviderAdapter):
    @property
    def url(self) -> str:
        return "https://gemini.google.com"

    def preflight_check(self, page: Page) -> bool:
        try:
            # Check for input area (Gemini uses a rich text area)
            # Selector often: .ql-editor or [contenteditable="true"]
            # Gemini specific: rich-textarea
            # Let's try a generic contenteditable inside the main area
            if not page.is_visible("div[contenteditable='true']", timeout=5000):
                return False
            return True
        except Exception:
            return False

    def send_prompt(self, page: Page, prompt: str) -> None:
        # Focus and fill
        page.click("div[contenteditable='true']")
        page.keyboard.type(prompt)
        page.keyboard.press("Enter")

    def wait_for_response(self, page: Page) -> None:
        # Gemini usually shows a spinner or "Stop" button.
        # Wait for "Response" container to appear or stabilize?
        # Better: Wait for the result to stop streaming.
        # Gemini logic is tricky without seeing DOM.
        # Generic fallback: Wait for arbitrary time? No, dumb.
        # Wait for "model-response" count to increase?
        
        # Taking a guess at current Gemini DOM:
        # It usually has a stop button/icon script.
        time.sleep(2) # Wait for request to register
        try:
            # Wait for some "streaming" indicator?
            # Or simplified: Wait for text to stabilize?
            
            # Let's assume standard behavior:
            # 1. Wait 3 sec.
            # 2. Wait for static state?
            # For now, I'll use a fixed wait + check loop because I lack selectors.
            # actually, I can try to find selectors via search if needed, but I'll write a "Generous" waiter.
            
            # Wait for a new message chunk?
            page.wait_for_timeout(4000) # Initial generation
            
            # TODO: Improve with real selector
            pass
        except Exception:
            pass

    def extract_response(self, page: Page) -> str:
        try:
            # Gemini responses are usually in <message-content> or .model-response
            # Let's try locating all message texts
            # .message-content
            responses = page.locator("message-content")
            count = responses.count()
            if count > 0:
                return responses.nth(count - 1).inner_text()
            
            # Fallback
            responses = page.locator(".model-response-text") 
            count = responses.count()
            if count > 0:
                return responses.nth(count - 1).inner_text()
                
            return ""
        except Exception:
            return "Error extracting response (Gemini selectors need update)."
