from playwright.sync_api import Playwright, sync_playwright, expect
from bs4 import BeautifulSoup as bs
import time
import re
import sqlite3
from datetime import datetime as dt


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
    job_id, job_title = parse_html(page_content)
    write_to_db(job_id, job_title)

    context.close()
    browser.close()


def parse_html(html_content):
    # %%
    soup = bs(html_content, 'html.parser')
    span_tags = soup.find_all('span', attrs={'title': True})
    job_id = re.findall('jobTitle.*" ', str(span_tags[2]))[0].replace('"', "").replace('jobTitle-', '').replace(' ', '')
    job_title = re.findall('title=".*">', str(span_tags[2]))[0].replace('title=', '').replace('"', '').replace('>', '')
    return job_id, job_title


def write_to_db(job_id, job_title):
    conn = sqlite3.connect('mydatabase.db')
    query = f'''INSERT INTO Jobs (
                        ID,
                        JobTitle,
                        date)
            VALUES ({job_id}, {job_title}, {dt.now().timestamp()})
            '''
    conn.execute(query)


with sync_playwright() as playwright:
    run(playwright)

