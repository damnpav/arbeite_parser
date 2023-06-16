from playwright.sync_api import Playwright, sync_playwright, expect
from bs4 import BeautifulSoup as bs
import time
import re
import sqlite3
import pandas as pd
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
    job_ids, job_titles = parse_html(page_content)
    write_to_db(job_id, job_title)

    context.close()
    browser.close()


def parse_html(html_content):
    # %%
    soup = bs(html_content, 'html.parser')
    span_tags = soup.find_all('span', attrs={'title': True})

    job_ids = []
    job_titles = []
    for span in span_tags:
        job_ids.append(re.findall('jobTitle.*" ', str(span))[0].replace('"', "").replace('jobTitle-', '').replace(' ', ''))
        job_titles.append(re.findall('title=".*">', str(span))[0].replace('title=', '').replace('"', '').replace('>', ''))
    return job_ids, job_titles


def write_to_db(job_ids, job_titles):
    conn = sqlite3.connect('mydatabase.db')
    job_df = pd.DataFrame()
    job_df['ID'] = job_ids
    job_df['JobTitle'] = job_titles
    job_df['date'] = dt.now().strftime('%H:%M:%S %Y-%m-%d')
    job_df.to_sql('Jobs', conn, if_exists='append')
    conn.commit()


with sync_playwright() as playwright:
    run(playwright)

