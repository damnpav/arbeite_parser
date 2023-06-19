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


def run(playwright: Playwright) -> None:
    """
    Run playwright to get actual cookies
    :param playwright:
    :return:
    """
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://de.indeed.com/")
    cookies = context.cookies()
    context.close()
    browser.close()
    return cookies


def parse_html(cookies, id_link):
    try:
        html_link = 'https://de.indeed.com/viewjob?jk=' + id_link
        headers = Headers(headers=True, browser="chrome",  # Generate only Chrome UA
                          os="mac", ).generate()
        cookie_string = cookies
        print(cookie_string)
        # Decode the string
        decoded_string = urllib.parse.unquote(cookie_string)

        # Split into key-value pairs
        key_value_pairs = decoded_string.split('&')

        # Convert to dictionary
        optanon_consent_dict = {pair.split('=')[0]: pair.split('=')[1] for pair in key_value_pairs}

        html_page = requests.get(html_link, headers=headers, cookies=optanon_consent_dict)
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





