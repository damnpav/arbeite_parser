import asyncio
from playwright.async_api import async_playwright
import sqlite3
import pandas as pd


async def get_page_content(browser, id_link: str):
    html_link = 'https://de.indeed.com/viewjob?jk=' + id_link
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(html_link)
    page_content = await page.content()
    await context.close()
    with open(f'{id_link}.html', 'w') as html_file:
        html_file.write(page_content)
    return f'{id_link}.html'


def retrieve_link():
    conn = sqlite3.connect('mydatabase.db')
    job_id = pd.read_sql('SELECT ID from Jobs limit 10', conn)
    conn.commit()
    return job_id['ID'].to_list()


async def main():
    # list of your ids
    ids = retrieve_link()
    # run all tasks in parallel
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # headless mode
        results = await asyncio.gather(*[get_page_content(browser, id_link) for id_link in ids])
    await browser.close()
    results_df = pd.DataFrame()
    results_df['html_code'] = results
    results_df.to_csv('html_results.csv', sep=';', index=False)

asyncio.run(main())
