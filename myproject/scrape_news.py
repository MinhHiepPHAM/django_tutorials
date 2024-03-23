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

def scrape_stock_news(symbols):
    # driver_path = "/usr/local/bin/geckodriver"
    # Initialize WebDriver with headless mode to not open the new windown
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--blink-settings=imagesEnabled=false')

    recent_news = utils.News()
    recent_news.read_recent_news_from_db(n_day=7)
    for symbol in symbols:
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.set_window_size(1920, 1080)
        headlines, urls = get_urls(symbol, driver)
        for url, headline in zip(urls, headlines):
            if recent_news.check_new_in_db(symbol,url): continue
            news = models.NewsModel(url=url, symbol=symbol,scrapped_date=date.today(),headline=headline)
            news.save()


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
            url = home_url + article.find('a')['href']
            headlines.append(headline)
            urls.append(url)

    return headlines, urls

if __name__ == '__main__':

    df = pd.read_csv('myproject/stock_price/symbols.csv')
    # print(df['symbol'])

    scrape_stock_news(df['symbol'])