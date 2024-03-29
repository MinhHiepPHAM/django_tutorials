import django
from django.conf import settings
settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'my_database',
            'USER': 'minh_hiep',
            'HOST': 'localhost',
            'PASSWORD': 'minh-hiep123',
            'port': 5432
        },
    },
    TIME_ZONE='Europe/Paris',
)
django.setup()
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import TimeoutException
from datetime import date
from stock_price import utils
from stock_price import models
import pandas as pd
import multiprocessing
import time
import requests
import re
from pathlib import Path
import os

def scape_each_symbol(symbol, options, recent_news):
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
    driver.set_window_size(1920, 1080)
    headlines, urls = get_urls(symbol, driver)
    for url, headline in zip(urls, headlines):
        if recent_news.check_new_in_db(symbol,url): continue
        news = models.NewsModel(url=url, symbol=symbol,scrapped_date=date.today(),headline=headline)
        news.save()

def scrape_stock_news(symbols):
    # driver_path = "/usr/local/bin/geckodriver"
    # Initialize WebDriver with headless mode to not open the new windown
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--blink-settings=imagesEnabled=false')

    recent_news = utils.News()
    recent_news.read_recent_news_from_db(n_day=7)

    args = ((symbol, options, recent_news) for symbol in symbols)

    starttime = time.time()
    pool = multiprocessing.Pool()
    pool.starmap(scape_each_symbol, args)
    pool.close()

    print('That tooks {} minutes'.format((time.time() - starttime)/60))

def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def get_urls(symbol, driver):
    # Navigate to the URL
    url = f'https://finance.yahoo.com/quote/{symbol}/news/'
    driver.get(url)
    try:
        # wait up to 3 seconds for the consent modal to show up
        consent_overlay = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.consent-overlay')))

        # click the "Accept all" button
        accept_all_button = consent_overlay.find_element(By.CSS_SELECTOR, '.accept-all')
        accept_all_button.click()
    except TimeoutException:
        print('Cookie consent overlay missing')

    # Get the HTML content after JavaScript execution
    html_content = driver.page_source

    # Close the browser
    driver.quit()

    headlines = []
    urls = []
    home_url = 'https://finance.yahoo.com'
    if html_content:
        # Parse the HTML content of the page
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all news articles
        news_articles = soup.find_all('h3', class_='Mb(5px)')

        # Extract news headlines and URLs     
        for article in news_articles:
            headline = article.text
            url = article.find('a')['href']
            if is_valid_url(url): url = home_url + url
            headlines.append(headline)
            urls.append(url)

    return headlines, urls

def is_active_url(url):
    try:
        code = requests.get(url).status_code
        return code == 200
    except Exception as e:
        print('UNACTIVE URL OR INVALID URL', url)
        return False

def delete_invalid_url(obj):
    if not is_active_url(obj.url): models.NewsModel.delete(obj)

def check_all_url():
    # all_urls = models.NewsModel.objects.values_list('url',flat=True)
    all_objects = models.NewsModel.objects.all()

    for obj in all_objects:
        delete_invalid_url(obj)

if __name__ == '__main__':

    current_path = Path(__file__).parent
    path_to_symbols = os.path.join(current_path,'stock_price/symbols.csv')
    df = pd.read_csv(path_to_symbols)
    # all_urls = models.NewsModel.objects.values_list('url',flat=True)
    start = time.time()
    # check_all_url()
    # print(f'That tooks: {(time.time()-start)/60} minutes to check if url is active or not')

    scrape_stock_news(df['symbol'])
    print(f'That tooks: {(time.time()-start)/60} minutes to scrap the news')