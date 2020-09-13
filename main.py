import lxml # noqa
import requests
import os
import re
import sqlite3

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
from multiprocessing.dummy import Pool as ThreadPool


routs = [
    'https://iwilltravelagain.com/canada/?page=1',
    'https://iwilltravelagain.com/australia-new-zealand-asia/?page=1',
    'https://iwilltravelagain.com/europe/?page=1',
    'https://iwilltravelagain.com/usa/?page=1',
]


base_url = 'https://iwilltravelagain.com'


def html_from_requests(url):
    r = requests.get(url)
    return r.text


def get_html(url):
    options = Options()
    options.add_argument("--headless")  # Runs Chrome in headless mode.
    options.add_argument('--no-sandbox')  # Bypass OS security model
    options.add_argument('--disable-gpu')  # applicable to windows os only
    options.add_argument('start-maximized')
    options.add_argument('disable-infobars')
    options.add_argument("--disable-extensions")
    executable_path = os.getcwd() + '\chromedriver.exe' # noqa
    driver = webdriver.Chrome(options=options, executable_path=executable_path)
    driver.get(url)
    sleep(10)
    html = driver.page_source

    return html


def get_page_data(html, url):
    soup = BeautifulSoup(html, 'lxml')
    title = soup.find('div', class_='block heading prose text-left').find('h1').text
    category = soup.find_all('div', class_='quick-details-content')[0].find_all('span')[1].text
    location = soup.find_all('div', class_='quick-details-content')[1].find_all('span')[1].text
    link = soup.find_all('div', class_='block button-block')[1].find('a').get('href')
    data = title, category, location, link,
    print(data)
    return data


def get_urls_on_page(html):
    base_url = 'https://iwilltravelagain.com'
    soup = BeautifulSoup(html, 'lxml')
    items = soup.find_all('div', class_='col col--width-1-3 valign-top col-grid--row js-grid-activity')
    links_list = []
    for item in items:
        link = item.find('article', class_='activity-single__inner activity-single--card').find('a').get('href')
        links_list.append(base_url + link)
    return links_list


def get_total_pages(html):
    soup = BeautifulSoup(html, 'lxml')
    total_pages = soup.find('div', class_='activity-pagination').find_all('button', class_='pagination-button')[-2].text
    total_pages = int(re.sub("\D", "", total_pages)) # noqa
    return total_pages


def get_urls(rout):
    urls_list = []
    for i in range(1, get_total_pages(get_html(rout)) + 1):
        url = rout[:-1] + str(i)
        urls_list.append(url)
        print(url)
    return urls_list


def get_all_urls_list():
    all_urls_list = []
    for rout in routs:
        try:
            urls = get_urls(rout)

            pool = ThreadPool(8)
            htmls = pool.map(get_html, urls)
            pool.close()
            pool.join()

            pool1 = ThreadPool(8)
            result = pool1.map(get_urls_on_page, htmls)
            pool1.close()
            pool1.join()

            for res in result:
                for r in res:
                    all_urls_list.append(r)

        except Exception: pass

    return all_urls_list


def get_sqlite(data):
    conn = sqlite3.connect('res.db')
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS items
                  (title text, category text, location text, link text)""")
    cursor.execute("INSERT INTO items (title, category, location, link) VALUES (?, ?, ?, ?)", data)
    conn.commit()


if __name__ == '__main__':
    for url in get_all_urls_list():
        get_sqlite(get_page_data(html_from_requests(url), url))
