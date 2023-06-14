from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://de.indeed.com/")
    page.get_by_placeholder("Stichwörter, Jobtitel oder Unternehmen").click()
    page.get_by_placeholder("Stichwörter, Jobtitel oder Unternehmen").fill("python")
    page.get_by_role("button", name="Jobs finden").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)

