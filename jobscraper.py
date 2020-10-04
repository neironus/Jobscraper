# -*- coding: utf-8 -*-
"""pyxtract_v.0.3.2.4_jobs_scraper.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1-wZerXww_HrqC9Pj46NXNHhV1s7BBu8V
"""
# for Google Colab install libraries and files
# !pip install -U spacy
# !python -m spacy download en_core_web_sm
# !python -m spacy download en_core_web_md
# !python -m spacy link en_core_web_md en
# !pip install wordsegment
# !pip install tika
# !pip install -U spacy-lookups-data
# !python -m spacy download xx_ent_wiki_sm
# !pip install tika
# !pip install newspaper3k
# !curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python3
# !pip install wordcloud
# !pip install textatistic
# !pip install langdetect
# !pip install textblob
# !pip install bs4 requests lxml pandas selenium
# !apt-get update # to update ubuntu to correctly run apt install
# !apt install chromium-chromedriver
# !cp /usr/lib/chromium-browser/chromedriver/usr/bin
# !pip install stop-words

import pandas as pd
from func import create_timestamp, create_csv, url_request, cleaning_raw_text

pd.set_option('display.max_colwidth', 100)
display_settings = {
    'expand_frame_repr': True,  # Развернуть на несколько страниц
    'precision': 2,
    'show_dimensions': True
}
for op, value in display_settings.items():
    pd.set_option("display.{}".format(op), value)

from multiprocessing.dummy import Pool as ThreadPool
from newspaper import Article
from newspaper import Config
from bs4 import BeautifulSoup
# Import Selenium and driver
from selenium import webdriver

# For using selenium chromedriver with Google Colab uncomment this line
# sys.path.insert(0,'/usr/lib/chromium-browser/chromedriver')
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# Load the small English model – spaCy is already imported
# nlp = spacy.load('en_core_web_sm')
import en_core_web_md

nlp = en_core_web_md.load()

import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')
nltk.download('wordnet')
stopwords = stopwords.words('english')
# Import NLTK Lemmatizer and Stemmer
wn = nltk.WordNetLemmatizer()
ps = nltk.PorterStemmer()

from stop_words import get_stop_words

stop_words_en = get_stop_words('en')
stop_words_ru = get_stop_words('russian')
# For using ukrainian stopwords with Google Colab uncomment this line
# stopwords_ua = pd.read_csv("/content/drive/My Drive/Colab Notebooks/data/stopwords_ua.txt", header=None, names=['stopwords'])
stopwords_ua = pd.read_csv("stopwords_ua.txt", header=None, names=['stopwords'])
stop_words_ua = list(stopwords_ua.stopwords)

# Parsing websites

tag_div = "div"
tag_a = "a"
tag_class = "class"

# DOU.UA - my solution
site_dou = 'https://jobs.dou.ua'
url = site_dou + "/vacancies/?city=%D0%9A%D0%B8%D1%97%D0%B2&category=Python&exp=0-1"


def dou_jobs(url):
    # Create a request to retrieve data using urllib.request
    data_resp = url_request(url)
    soup = BeautifulSoup(data_resp, 'lxml')

    def get_url_list(soup_url_list, all_urls=[]):
        for item in soup_url_list:
            if item is not None:
                item = item['href']
                # print(item)
                all_urls.append(item)
            else:
                item = ''
                all_urls.append(item)
        return all_urls

    def get_job_list(soup_job_list, all_job=[]):
        for item in soup_job_list:
            if item is not None:
                item = item.get_text().strip()
                # print(item)
                all_job.append(item)
            else:
                item = ''
                all_job.append(item)
        return all_job

    def get_company_list(soup_company_list, all_company=[]):
        for item in soup_company_list:
            if item is not None:
                item = item.get_text().strip()
                # print(item)
                all_company.append(item)
            else:
                item = ''
                all_company.append(item)
        return all_company

    def parse_dou(soup_obj):
        for d in soup_obj.findAll(tag_div, {tag_class: "vacancy"}):
            job_url_list = d.findAll(tag_a, {tag_class: "vt"}, href=True)
            job_title_list = d.findAll(tag_a, {tag_class: "vt"})
            company_list = d.findAll(tag_a, {tag_class: "company"})

            all_urls = get_url_list(job_url_list)
            all_job = get_job_list(job_title_list)
            all_company = get_company_list(company_list)
            df_dou = pd.DataFrame(
                {'job': all_job, 'company': all_company, 'time': create_timestamp(), "site": site_dou, 'url': all_urls})
        return df_dou

    dou_df = parse_dou(soup)
    return dou_df


douua_df = dou_jobs(url)
# print(douua_df)

# create douua_jobs csv file
create_csv(douua_df, 'douua_jobs')

# Indeed - my solution

# specify driver path
driver = webdriver.Chrome('chromedriver.exe', options=chrome_options)

# Get URL
site_indeed = 'https://ua.indeed.com'
driver.get(site_indeed + '/jobs?q=Python&l=Kyiv&fromage=1&sort=date')


def indeed_jobs():
    try:
        close_popup = driver.find_element_by_id("popover-close-link")
        close_popup.click()
    except:
        pass

    # let the driver wait 3 seconds to locate the element before exiting out
    driver.implicitly_wait(3)
    titles = []
    companies = []
    links = []
    descriptions = []
    job_card_xpath = '//div[contains(@class,"clickcard")]'
    title_xpath = './/h2[@class="title"]//a'
    link_xpath = './/h2[@class="title"]//a'
    company_xpath = './/span[@class="company"]'
    descriptions_xpath = '//div[@id="jobDescriptionText"]'

    job_card = driver.find_elements_by_xpath(job_card_xpath)

    def parse_indeed(job_card):
        for job in job_card:
            title = job.find_element_by_xpath(title_xpath).text
            titles.append(title)
            company = job.find_element_by_xpath(company_xpath).text
            companies.append(company)
            link = job.find_element_by_xpath(link_xpath).get_attribute(name="href")
            links.append(link)
            # print("Title: {}, {}, {}".format(title, company, link))
        return titles, companies, links

    titles, companies, links = parse_indeed(job_card)

    def get_descriptions(links):
        for link in links:
            driver.get(link)
            jd = driver.find_element_by_xpath(descriptions_xpath).text
            descriptions.append(jd)
        return descriptions

    descriptions = get_descriptions(links)
    # create dataframe
    df_indeed = pd.DataFrame({
        'job': titles, 'company': companies, 'txt': descriptions, 'time': create_timestamp(),
        "site": site_indeed, 'url': links
    })
    return df_indeed


indeed_df = indeed_jobs()

# print(indeed_df)

# create csv file
create_csv(indeed_df, 'indeed_jobs')

# robota.ua - my solution
site_robota = 'https://rabota.ua'
url = site_robota + "/zapros/python/%D0%BA%D0%B8%D0%B5%D0%B2?period=2&lastdate="


def robota_jobs(url):
    data = url_request(url)
    soup = BeautifulSoup(data, 'lxml')
    all_job = []
    all_company = []
    all_urls = []

    def parse_indeed(soup_obj):
        for d in soup_obj.findAll(tag_div, {tag_class: "f-vacancylist-wrap fd-f-left ft-c-stretch"}):
            job_url_list = d.findAll(tag_a, {tag_class: "ga_listing"}, href=True)
            job_title_list = d.findAll(tag_a, {tag_class: "ga_listing"})
            company_list = d.findAll(tag_a, {tag_class: "company-profile-name"})

            for u, j, c in zip(job_url_list, job_title_list, company_list):
                if u and j and c is not None:
                    u = u['href']
                    # print(u)
                    all_urls.append(site_robota + u)
                    j = j.get_text().strip()
                    # print(j)
                    all_job.append(j)
                    c = c.get_text().strip()
                    # print(c)
                    all_company.append(c)
                else:
                    u = ''
                    all_urls.append(u)
                    j = ''
                    all_job.append(j)
                    c = ''
                    all_company.append(c)
            df_robota = pd.DataFrame({
                'job': all_job, 'company': all_company, 'time': create_timestamp(),
                "site": site_robota, 'url': all_urls
            })
        return df_robota

    robotaua = parse_indeed(soup)
    return robotaua


robotaua_df = robota_jobs(url)
# print(robotaua_df)

# create csv file"""
create_csv(robotaua_df, 'robotaua_jobs')

# Dataframes Vertical Stacking
jobs_df = pd.concat([douua_df, indeed_df, robotaua_df], axis=0, ignore_index=True)
jobs_df.sort_values(by='url')

# List of urls for download and parsing
jobs_url_list = list(jobs_df['url'][jobs_df['site'] != 'ua.indeed.com'])
# print(jobs_url_list)

# Parsing URLs (minimum from list or maximum from file)
my_url_list = jobs_url_list.copy()
# print(my_url_list)

# Downloading and parsing my url list

# Get text from URLs
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
# Configure Newspaper's Article class
config = Config()
config.browser_user_agent = user_agent
config.memoize_articles = False
config.fetch_images = False

# parsing URL list
articles_info_list = []


# Getting text and metadata from URLs
def getTxt(url):
    try:
        article = Article(url, config=config)
        article.download()
        article.parse()
        article.nlp()
        article_title = article.title
        article_source_url = article.source_url
        url_of_article = article.url
        txt = article.text
        txt = cleaning_raw_text(txt)
        timestamp = create_timestamp()
        tmp = [article_title, txt, article_source_url, url_of_article, timestamp]
        articles_info_list.append(tmp)
    except:
        pass
        # print('***FAILED TO DOWNLOAD***', url_of_article)
    return articles_info_list


# create multitreading: number of treads for downloading articles
pool = ThreadPool(4)
# open the urls in their own threads and return the results
# insted of my_url_list
results = pool.map(getTxt, my_url_list)
# close the pool and wait for the work to finish
pool.close()
pool.join()

# Create dataframe
article_info_df = pd.DataFrame(articles_info_list,
                               columns=['job', 'txt', 'site', 'url', 'time'])
article_info_df.sort_values(by='url')

# Merge dataframes on an "url" column
data_full = jobs_df.merge(article_info_df, how="left", left_on="url", right_on="url")
# print(data_full)

# rename columns
# print(data_full.columns)
data2 = data_full.drop(['job_y', 'site_y', 'time_y', ], axis='columns')
data2['full_txt'] = data2['txt_x'].combine_first(data2['txt_y'])
# print(data2)

# drop txt columns
data2 = data2.drop(['txt_x', 'txt_y'], axis='columns')

# rename columns
columns = ['job', 'company', 'time', 'site', 'url', 'txt']
data2.columns = columns
data = data2
create_csv(data, 'data')
print(data.info())

# for a Dataframe statistics use stat.py

# for visualization a Dataframe statistics use visual.py