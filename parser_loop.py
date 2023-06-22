from playwright.sync_api import Playwright, sync_playwright, expect
import urllib.parse
from fake_headers import Headers
from bs4 import BeautifulSoup as bs
import time
import re
import requests
import sqlite3
import pandas as pd
from datetime import datetime as dt
from playwright.async_api import async_playwright
from tqdm import tqdm


def run(playwright: Playwright, id_links) -> None:
    """
    Run playwright to get actual cookies
    :param playwright:
    :return:
    """
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    for id_link in tqdm(id_links):
        html_link = 'https://de.indeed.com/viewjob?jk=' + id_link
        page.goto(html_link)
        page_content = page.content()
        with open(f'{id_link}.html', 'w') as html_file:
            html_file.write(page_content)
    context.close()
    browser.close()


def retrieve_link():
    conn = sqlite3.connect('mydatabase.db')
    job_id = pd.read_sql('SELECT ID from Jobs limit 100', conn)
    conn.commit()
    return job_id['ID'].to_list()


with sync_playwright() as playwright:
    run(playwright, retrieve_link())





