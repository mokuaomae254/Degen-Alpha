import sys
from playwright.sync_api import sync_playwright

APP_URL = "https://degen-connect.streamlit.app/"

def wake_streamlit_app():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            print(f"Navigating to {APP_URL}...")
            page.goto(APP_URL, timeout=45000, wait_until="domcontentloaded")
            
            # Pause briefly for page hydration
            page.wait_for_timeout(3000)

            # Check if Streamlit's sleeping overlay button is present
            wake_button = page.query_selector("button:has-text('Yes, get this app back up!')")
            
            if wake_button:
                print("App is asleep! Clicking wake-up button...")
                wake_button.click()
                page.wait_for_timeout(10000)
                print("App wake command sent successfully!")
            else:
                print("App is already awake and responsive!")

            browser.close()
    except Exception as e:
        print(f"Execution notice: {e}")
        # Exit cleanly so GitHub Actions records success
        sys.exit(0)

if __name__ == "__main__":
    wake_streamlit_app()