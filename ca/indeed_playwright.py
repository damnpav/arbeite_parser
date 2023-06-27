from playwright.sync_api import Playwright, sync_playwright, expect
from bs4 import BeautifulSoup as bs
import time
import re
import sqlite3
import pandas as pd
from datetime import datetime as dt

# TODO refactor for NL


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://ca.indeed.com/")

    time.sleep(5)
    # try:
    #     page.get_by_text("Alle cookies accepteren").click()
    # except Exception as e:
    #     print(f'No able to accept cookies: {e}')


    page.get_by_placeholder("Job title, keywords, or company").click()
    page.get_by_placeholder("Job title, keywords, or company").fill("python")
    page.get_by_role("button", name="Find jobs").click()

    flag = 0
    k = 0
    google_flag = 0
    while flag == 0:
        k += 1
        print(f'Page {k}')
        time.sleep(5)

        try:
            page_content = page.content()
            job_ids, job_titles = parse_html(page_content)
            write_to_db(job_ids, job_titles)
        except Exception as e:
            print(f'Exception: {e}')

        try:
            page.get_by_test_id("pagination-page-next").click()

            if google_flag == 0:
                try:
                    page.get_by_role("button", name="close").click()
                    google_flag = 1
                except Exception as e:
                    print(f'No able to close google page: {e}')
        except Exception as e:
            print(f'No able to open next page: {e}')
            flag = 1
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
    #print('connect to db')
    conn = sqlite3.connect('mydatabase.db')
    job_df = pd.DataFrame()
    job_df['ID'] = [job_id + '_CA' for job_id in job_ids]
    job_df['JobTitle'] = job_titles
    job_df['date'] = dt.now().strftime('%H:%M:%S %Y-%m-%d')

    existed_jobs = pd.read_sql('SELECT ID from Jobs', conn)
    job_df = job_df.loc[~job_df['ID'].isin(existed_jobs['ID'])].copy()

    if len(job_df) > 0:
        job_df.to_sql('Jobs', conn, index=False, if_exists='append')
        conn.commit()
    else:
        print('No new jobs')


with sync_playwright() as playwright:
    run(playwright)


