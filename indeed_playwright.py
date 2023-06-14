from playwright.sync_api import Playwright, sync_playwright, expect
import time


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://de.indeed.com/")
    page.get_by_placeholder("Stichwörter, Jobtitel oder Unternehmen").click()
    page.get_by_placeholder("Stichwörter, Jobtitel oder Unternehmen").fill("python")
    page.get_by_role("button", name="Jobs finden").click()

    time.sleep(5)

    page_content = page.content()

    # strategy - download html pages and then parse it out with bs4

    # Save the page content in an HTML file
    with open("page.html", "w", encoding="utf-8") as file:
        file.write(page_content)

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)

