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


def run(playwright: Playwright, id_link) -> None:
    """
    Run playwright to get actual cookies
    :param playwright:
    :return:
    """
    html_link = 'https://de.indeed.com/viewjob?jk=' + id_link
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(html_link)
    page_content = page.content()
    context.close()
    browser.close()
    with open(f'{id_link}.html', 'wb') as html_file:
        html_file.write(page_content)
    return f'{id_link}.html'




def parse_html(cookies, id_link):
    try:
        html_link = 'https://de.indeed.com/viewjob?jk=' + id_link
        headers = Headers(headers=True, browser="chrome",  # Generate only Chrome UA
                          os="mac", ).generate()
        cookie_string = cookies
        print(cookie_string)
        # Decode the string
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookie_string}

        html_page = requests.get(html_link, headers=headers, cookies=cookie_dict)
        with open(f'{id_link}.html', 'wb') as html_file:
            html_file.write(html_page.content)
        return f'{id_link}.html'
    except Exception as e:
        return e


def retrieve_link():
    conn = sqlite3.connect('mydatabase.db')
    job_id = pd.read_sql('SELECT ID from Jobs limit 1', conn)
    conn.commit()
    return job_id['ID'][0]


with sync_playwright() as playwright:
    cookies = run(playwright)

job_id = retrieve_link()
status = parse_html(cookies, job_id)
print(status)

# no possible, need to parse with playwright anyway





