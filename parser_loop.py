from playwright.sync_api import Playwright, sync_playwright
import sqlite3
import pandas as pd
from datetime import datetime as dt
from tqdm import tqdm


def run(playwright: Playwright, id_links) -> None:
    """
    Run playwright to get actual cookies
    :param playwright:
    :return:
    """
    conn = sqlite3.connect('mydatabase.db')
    cur = conn.cursor()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    for id_link in tqdm(id_links):
        html_link = 'https://de.indeed.com/viewjob?jk=' + id_link
        page.goto(html_link)
        page_content = page.content()
        write_content(id_link, page_content, cur)
        conn.commit()
    context.close()
    browser.close()


def retrieve_link():
    conn = sqlite3.connect('mydatabase.db')
    job_id = pd.read_sql("""                        
                        SELECT ID FROM Jobs 
                        WHERE ('https://de.indeed.com/viewjob?jk=' || ID) NOT IN 
                        (SELECT link FROM POSTS)
                        LIMIT 10;
                        """, conn)
    conn.commit()
    return job_id['ID'].to_list()


def write_content(link, page_content, cur):
    cur.execute("""
                INSERT INTO posts (link, content, date) VALUES (?, ?, ?)
                """, (link, page_content, dt.now().strftime('%H:%M:%S %Y-%m-%d')))

with sync_playwright() as playwright:
    run(playwright, retrieve_link())


# TODO prepare for prod
# TODO make server with GUI


