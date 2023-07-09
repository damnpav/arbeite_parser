import pandas as pd
from bs4 import BeautifulSoup
import sqlite3
from tqdm import tqdm
import json


db_path = 'data_dumps/nl_jobs_mydatabase.db'
link_to_replace = 'https://nl.indeed.com/viewjob?jk='


class HtmlParser(db_path, link_to_replace):
    """
    Class to parse htmls from db and insert content in new table of db
    """
    def __init__(self):
        self.db_path = db_path
        self.link_to_replace = link_to_replace
        self.conn = sqlite3.connect(self.db_path)
        self.cur = self.conn.cursor()

    def create_content_table(self):
        """
        Function to create new content table in db
        :return:
        """
        create_table = """
                       CREATE TABLE "job_content" (
                        "job_id"	TEXT,
                        "job_title"	TEXT,
                        "titles"	TEXT,
                        "descr_list"	TEXT,
                        "hiring_organization"	TEXT,
                        "city"	TEXT)
                       """
        self.cur.execute(create_table)
        self.conn.commit()

    def write_content(self, link, job_title, titles, descr_list, hiring_organization, city):
        self.cur.execute("""
                    INSERT INTO job_content (job_id, job_title, titles, descr_list, hiring_organization, city)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (link, job_title, titles, descr_list, hiring_organization, city))

    def retrieve_all_html(self):
        posts_df = pd.read_sql("""
                            SELECT a.link, a.content, b.JobTitle FROM posts a
                            LEFT JOIN Jobs b on b.ID = REPLACE(a.link, self.link_to_replace, '')
                            """, self.conn)
        return posts_df

    def extract_text(self, html_text):
        """
        Function to parse html code from db and parse out with BS4 for inserting in content table
        :param html_text: html_text from db
        :return:
        """
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

    def db_extraction(self, big_posts_df):
        for index, row in tqdm(big_posts_df.iterrows()):
            link = row['link']
            job_title = row['JobTitle']
            titles, descr_list, hiring_organization, city = self.extract_text(row['content'])
            self.write_content(link, job_title, str(titles), str(descr_list), str(hiring_organization), str(city))
            self.conn.commit()


class t



















