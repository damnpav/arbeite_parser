import pandas as pd
from bs4 import BeautifulSoup
import sqlite3
from tqdm import tqdm
import json
import ast
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
import numpy as np
from nltk.corpus import stopwords
from string import punctuation
import spacy
from tqdm import tqdm


tqdm.pandas()

db_path = r'data_dumps/ка_mydatabase.db'
link_to_replace = 'https://ca.indeed.com/viewjob?jk='


class HtmlParser:
    """
    Class to parse htmls from db and insert content in new table of db
    """
    def __init__(self, db_path, link_to_replace):
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
        posts_df = pd.read_sql(f"""
                            SELECT a.link, a.content, b.JobTitle FROM posts a
                            LEFT JOIN Jobs b on REPLACE(b.ID, '_CA', '') = REPLACE(a.link, '{self.link_to_replace}', '')
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


class TextPrepare:
    """
    Class with function for preparing text for clusterization
    And clusterization itself
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cur = self.conn.cursor()
        self.gender_labels = ['mfx', 'mfd', 'wmd', 'mwd', 'fmd', 'fmx', 'dfm']
        self.nlp_en = spacy.load('en_core_web_sm')
        self.nlp_de = spacy.load('de_core_news_sm')
        self.nlp_nl = spacy.load('de_core_news_sm')
        pass

    def read_content(self):
        content_df = pd.read_sql("""
                            SELECT * FROM job_content
                            """, self.conn)
        return content_df

    def retrieve_company(self, row):
        """
        Function to retrieve dict like objects
        :param row:
        :return:
        """
        if 'name' in str(row):
            try:
                job_dict = ast.literal_eval(row)
                return job_dict['name']
            except:
                pass
        return 'Not found'

    def clean_content(self, content_df):
        content_df['company'] = content_df['hiring_organization'].apply(self.retrieve_company)
        content_df['titles'] = content_df['titles'].str.replace("['", '').replace("]", '')
        content_df['descr_list'] = content_df['descr_list'].str.replace("['", '').replace("]", '')
        content_df['descr_list'] = content_df['descr_list'].str.replace("', '", '')
        content_df_cleaned = content_df[['job_id', 'job_title', 'titles', 'descr_list', 'city', 'company']]
        return content_df_cleaned.drop_duplicates()

    def company_grouping(self, jobs_df):
        grouped_df = jobs_df[['company', 'job_id']].groupby('company').agg({'job_id': 'count'}).sort_values(by='job_id',
                                                                                               ascending=False)
        return grouped_df

    def text_prepare(self, jobs_df):
        text_columns = ['job_title', 'titles', 'descr_list']
        for col in tqdm(text_columns):
            jobs_df[col] = jobs_df[col].str.lower()
            jobs_df[col] = jobs_df[col].str.replace('[', '').replace(']', '')
            jobs_df[col] = jobs_df[col].str.replace('[^a-zA-Z ]', '', regex=True)  # replace all non Latin symbols
        job_title_df = jobs_df[['job_id', 'job_title']].copy()
        job_title_df.to_excel('debug_excel.xlsx')
        job_title_df['cleaned_text'] = job_title_df['job_title'].progress_apply(self.token_processing)
        return jobs_df, job_title_df

    def set_stop_words(self, languages):
        """
        Setting list with stopwords from required languages
        :param languages: list with required languages
        :return:
        """
        self.stop_words = []
        for language in languages:
            self.stop_words += stopwords.words(language)

    def token_processing(self, text):
        tokens = text.split()
        tokens = [token for token in tokens if token not in self.stop_words
                  and token != " " and token.strip() not in punctuation
                  and token not in self.gender_labels]

        text = " ".join(tokens)
        return text

    def make_bow(self, job_title_df):
        vect = CountVectorizer(stop_words=self.stop_words)
        X = vect.fit_transform(job_title_df['cleaned_text'])
        bow_df = pd.DataFrame(data=X.toarray(), columns=vect.get_feature_names_out())
        bow_df['job_id'] = job_title_df['job_id']
        token_freq = pd.DataFrame(bow_df[bow_df.columns[:-1]].sum(), columns=['freq'])
        selected_tokens = token_freq.loc[(token_freq['freq'] > token_freq['freq'].quantile(0.9))].reset_index()[
            'index'].to_list()

        nlp = spacy.load('en_core_web_sm')
        lemmatized_tokens = [self.nlp_en(token)[0].lemma_ for token in selected_tokens]
        lemmatized_tokens = [self.nlp_de(token)[0].lemma_ for token in selected_tokens]
        lemmatized_tokens = [self.nlp_nl(token)[0].lemma_ for token in selected_tokens]
        lemmatized_tokens = [token.lower() for token in lemmatized_tokens]
        rename_dict = dict(zip(selected_tokens, lemmatized_tokens))
        unique_tokens = list(set(lemmatized_tokens))

        tokens_df = pd.DataFrame()
        tokens_df['token'] = unique_tokens
        tokens_df.to_excel('unique_tokens.xlsx', index=False)

        bow_df1 = bow_df.rename(columns=rename_dict).copy()

        # for el in ['--', 'dwm', 'on']:
        #     try:
        #         del bow_df1[el]
        #     except Exception:
        #         pass

        return bow_df1[unique_tokens + ['job_id']]

    def clustering(self, bow_df):
        n_clusters = 4  # replace with the number of clusters you want

        # Prepare the data for clustering
        X = bow_df.drop('job_id', axis=1)

        # Initialize the KMeans object
        kmeans = KMeans(n_clusters=n_clusters, random_state=0)

        # Perform clustering
        bow_df['cluster'] = kmeans.fit_predict(X)

        # Get the centroids
        centroids = kmeans.cluster_centers_

        # Create a DataFrame from the centroids array
        centroids_df = pd.DataFrame(centroids, columns=X.columns)

        return bow_df, centroids_df


# print(f'Retrieving htmls..')
# html_parse = HtmlParser(db_path, link_to_replace)
# html_parse.create_content_table()
# html_parse.db_extraction(html_parse.retrieve_all_html())
# print(f'Finished')

print(f'Text preparing and clustering')
text_prepare = TextPrepare(db_path)
content_df = text_prepare.read_content()
text_prepare.set_stop_words(['english', 'dutch', 'german'])
content_df_cleaned = text_prepare.clean_content(content_df)
grouped_by_company_df = text_prepare.company_grouping(content_df_cleaned)
grouped_by_company_df.to_excel('ka_company_grouped.xlsx')
jobs_df, job_title_df = text_prepare.text_prepare(content_df_cleaned.dropna())
jobs_df.to_excel(f'ka_jobs_cleaned.xlsx')
job_title_df = job_title_df.loc[job_title_df['job_id'].str.len() > 3]
bow_df = text_prepare.make_bow(job_title_df.dropna())
clustered_bow_df, centroids_df = text_prepare.clustering(bow_df)
clustered_bow_df = clustered_bow_df[['job_id', 'cluster']].merge(job_title_df[['job_id', 'job_title']], how='left', on='job_id')
clustered_bow_df.to_excel('ka_jobs_clustered.xlsx')
centroids_df.to_excel('ka_centroids.xlsx')
print('finish')






















