import pandas as pd
from bs4 import BeautifulSoup
import sqlite3
from tqdm import tqdm
import json


db_path = 'data_dumps/de_jobs_mydatabase.db'


def extract_text(html_text):
    soup = BeautifulSoup(html_text)
    titles = [tag.get_text() for tag in soup.find_all('title')]
    descr_list = [tag.get_text() for tag in soup.find_all('p')]

    try:
        script_tag = soup.find('script', {'type': 'application/ld+json'})
        data = json.loads(script_tag.string)
        hiring_organization = data['hiringOrganization']
    except:
        hiring_organization = 'Not found'

    try:
        script_tag = soup.find('script', {'type': 'application/ld+json'})
        data = json.loads(script_tag.string)
        description_html = data['description']
        description_soup = BeautifulSoup(description_html, 'html.parser')
        address = description_soup.find_all('b')[-1].find_next_siblings(text=True)
        city = address[-1].strip()
    except:
        city = 'Not found'

    return titles, descr_list, hiring_organization, city


def retrieve_all_html():
    conn = sqlite3.connect(db_path)
    posts_df = pd.read_sql("""
                        SELECT a.link, a.content, b.JobTitle FROM posts a
                        LEFT JOIN Jobs b on b.ID = REPLACE(a.link, 'https://de.indeed.com/viewjob?jk=', '')
                        """, conn)
    return posts_df


def write_content(link, job_title, titles, descr_list, hiring_organization, city, cur):
    cur.execute("""
                INSERT INTO job_content (job_id, job_title, titles, descr_list, hiring_orgnization, city)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (link, job_title, titles, descr_list, hiring_organization, city))


def db_extraction(big_posts_df):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for index, row in tqdm(big_posts_df.iterrows()):
        link = row['link']
        job_title = row['JobTitle']
        titles, descr_list, hiring_organization, city = extract_text(row['content'])
        write_content(link, job_title, str(titles), str(descr_list), str(hiring_organization), str(city), cur)
        conn.commit()


db_extraction(retrieve_all_html())






