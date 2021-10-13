import urllib3
from selenium.webdriver.support.select import Select
from tqdm import tqdm
import pathlib
import re
import requests
from bs4 import BeautifulSoup
import selenium
import os
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool



path = "/resources/corpora/parlamentary"


def get_links(page_url):
    pages = set()
    pattern = re.compile("^(/)")
    html = requests.get(page_url).text  # fstrings require Python 3.6+
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("a", href=pattern):
        if "href" in link.attrs:
            if link.attrs["href"] not in pages:
                new_page = link.attrs["href"]
                print(new_page)
                pages.add(new_page)
                get_links(new_page)

    return pages




from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome("/home/stud_homes/s5935481/work4/parliament_crawler/src/crawling_services/chromedriver",
                          options=chrome_options)
driver.get("https://www.parlamentsdokumentation.brandenburg.de/ELVIS/index.html")

search_box_enter = driver.find_element_by_link_text("Suche ausführen, Trefferanzahl aktualisieren")
driver.find_element_by_class_name("button")

def brandenburg_crawler():
    try:
        pathlib.Path("/resources/corpora/parlamentary/brandenburg").mkdir(parents=True, exist_ok=False)
    except:
        print("/resources/corpora/parlamentary already exists...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome("/home/stud_homes/s5935481/work4/parliament_crawler/src/crawling_services/chromedriver",
                              options=chrome_options)
    driver.get("https://www.parlamentsdokumentation.brandenburg.de/ELVIS/index.html")
    select_item_electionperiods = Select(driver.find_element_by_id("LISSH_WP"))
    electionperiods = [i.text for i in select_item_electionperiods.options][:-1]
    select_document_types = Select(driver.find_element_by_id("LISSH_DART"))
    document_types = [i.text for i in select_document_types.options][1:]
    for period in tqdm(electionperiods):
        try:
            pathlib.Path("/resources/corpora/parlamentary/brandenburg" + "/" + period).mkdir(parents=True, exist_ok=False)
        except:
            print("/resources/corpora/parlamentary/brandenburg/" + "/" + period + " already exists...")
        for document_type in document_types:
            try:
                pathlib.Path("/resources/corpora/parlamentary/brandenburg" + "/" + period + "/" + document_type).mkdir(parents=True,
                                                                                                 exist_ok=False)
            except:
                print("/resources/corpora/parlamentary/brandenburg/" + "/" + period + "/" + document_type + " already exists...")
