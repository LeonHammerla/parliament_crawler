import argparse


import urllib3
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm
import pathlib
import re
import requests
from bs4 import BeautifulSoup
import selenium
import os
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import textract
import codecs
import time
from selenium.webdriver.support import expected_conditions as EC






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
                #get_links(new_page)

    return pages

def test():
    pages = set()
    from selenium import webdriver
    import time
    from bs4 import BeautifulSoup
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome("/home/stud_homes/s5935481/work4/parliament_crawler/src/crawling_services/chromedriver",
                              options=chrome_options)


    url = "https://www.buergerschaft-hh.de/parldok/neuedokumente/1"
    browser.get(url)
    time.sleep(3)
    source = browser.page_source
    soup = BeautifulSoup(source, 'html.parser')
    pattern = re.compile("pdf")
    for link in soup.find_all("a", href=pattern):
        if "href" in link.attrs:
            if link.attrs["href"] not in pages:
                new_page = link.attrs["href"]
                print(new_page)
                pages.add(new_page)
    return pages

def brandenburg_proc_mp(config: list, make_directories: bool = True):
    """
    Function for downloading and saving (as pdf and txt) all "Plenumprotokolle" for brandenburg.
    But depricated--multiprocessing doesnt work, but single process version works fine and takes not long...
    :param config:
    :param make_directories:
    :return:
    """
    period, document_type, save_path = config
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome("/home/stud_homes/s5935481/work4/parliament_crawler/src/crawling_services/chromedriver",
                              options=chrome_options)

    driver.get("https://www.parlamentsdokumentation.brandenburg.de/ELVIS/index.html")
    time.sleep(10)
    select_item_electionperiods = Select(driver.find_element_by_id("LISSH_WP"))
    select_document_types = Select(driver.find_element_by_id("LISSH_DART"))
    select_item_electionperiods.select_by_visible_text(period)
    select_document_types.select_by_visible_text(document_type)
    button_items = driver.find_elements_by_class_name("button")
    for i in reversed(range(0, len(button_items))):
        if button_items[i].get_property("type") != "submit":
            del button_items[i]
    button_item = button_items[0]
    button_item.click()
    time.sleep(10)
    document_types_dropdown_menu = Select(driver.find_element_by_name("LISSH_Browse_ReportFormatList"))
    document_types_dropdown_menu.select_by_visible_text("Dokumente")
    time.sleep(10)
    items_per_page_dropdown = Select(driver.find_element_by_name("NumPerSegment"))
    items_per_page_dropdown.select_by_visible_text("alle")
    time.sleep(10)
    all_links = driver.find_elements_by_css_selector("[title^='Gesamtdokument']")
    all_links = list(set([item.get_property("href") for item in all_links]))
    driver.quit()
    if make_directories:
        try:
            pathlib.Path(save_path + "/pdf").mkdir(parents=True, exist_ok=False)
            pathlib.Path(save_path + "/txt").mkdir(parents=True, exist_ok=False)
        except:
            print("one of the directories already exists")
    file_names = []
    file_names_failed = []
    for link in tqdm(all_links, desc="Process: {}".format(period)):
        response = requests.get(link)
        file_name = save_path + "/pdf" + "/" + "_".join(link.split("/")[6:])

        try:
            with open(file_name, 'wb') as f:
                f.write(response.content)
            file_names.append((link, file_name))
        except:
            file_names_failed.append((link, file_name))

    file_names_failed_2 = []
    for file_name in file_names:
        try:
            text = textract.process(file_name[-1])
            text = text.decode("utf-8").split("\n")
            with codecs.open(save_path + "/txt/" + file_name[-1].split("/")[-1], "w", "utf-8") as f:
                for line in text:
                    text.write(line + "\n")
        except:
            file_names_failed_2.append(file_name)

    for failed in file_names_failed_2:
        file_names.remove(failed)
    file_names_failed = file_names_failed + file_names_failed_2
    return [file_names, file_names_failed]

def brandenburg_crawler_mp(make_directories: bool = True,
                        save_path: str = "/vol/s5935481/parlamentary/brandenburg"):
    """
    Function for downloading and saving (as pdf and txt) all "Plenumprotokolle" for brandenburg.
    But depricated--multiprocessing doesnt work, but single process version works fine and takes not long...
    :param make_directories:
    :param save_path:
    :return:
    """

    if make_directories:
        try:
            pathlib.Path(save_path).mkdir(parents=True, exist_ok=False)
        except:
            print(save_path + " already exists...")
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
    configs = []
    for period in tqdm(electionperiods):
        if make_directories:
            try:
                pathlib.Path(save_path + "/" + period).mkdir(parents=True, exist_ok=False)
            except:
                print(save_path + "/" + period + " already exists...")

        configs.append([period, "Plenarprotokoll", save_path + "/" + period])

    driver.quit()
    del driver

    print("Start Downloading")
    pool = Pool(len(electionperiods))
    results = pool.map(brandenburg_proc_mp, configs)
    pool.close()
    pool.join()

    with open(save_path + "/stats.txt", "w") as f:
        correct = []
        failed = []
        for result in results:
            correct.extend([res[0] for res in result[0]])
            failed.extend([res[0] for res in result[1]])
        f.write("completed requests + conversions : {}".format(len(correct)) + "\n")
        f.write("failed requests + conversions    : {}".format(len(failed)) + "\n")
        f.write("total requests                   : {}".format(len(correct) + len(failed)) + "\n")
        f.write("==========completed requests==========" + "\n")
        for com in correct:
            f.write(com + "\n")
        f.write("==========failed requests==========" + "\n")
        for fail in failed:
            f.write(fail + "\n")
    return


def brandenburg_proc_sp(config: list, make_directories: bool = True):
    """
     Function for downloading and saving (as pdf and txt) all "Plenumprotokolle" for brandenburg.

    :param config:
    :param make_directories:
    :return:
    """
    period, document_type, save_path = config
    print(period, document_type)
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome("/home/stud_homes/s5935481/work4/parliament_crawler/src/crawling_services/chromedriver",
                              options=chrome_options)
    driver.get("https://www.parlamentsdokumentation.brandenburg.de/ELVIS/index.html")
    time.sleep(5)
    select_item_electionperiods = Select(driver.find_element_by_id("LISSH_WP"))
    select_document_types = Select(driver.find_element_by_id("LISSH_DART"))
    select_item_electionperiods.select_by_visible_text(period)
    select_document_types.select_by_visible_text(document_type)
    button_items = driver.find_elements_by_class_name("button")
    for i in reversed(range(0, len(button_items))):
        if button_items[i].get_property("type") != "submit":
            del button_items[i]
    button_item = button_items[0]
    button_item.click()
    time.sleep(5)
    document_types_dropdown_menu = Select(driver.find_element_by_name("LISSH_Browse_ReportFormatList"))
    document_types_dropdown_menu.select_by_visible_text("Dokumente")
    time.sleep(5)
    items_per_page_dropdown = Select(driver.find_element_by_name("NumPerSegment"))
    items_per_page_dropdown.select_by_visible_text("alle")
    time.sleep(5)
    all_links = driver.find_elements_by_css_selector("[title^='Gesamtdokument']")
    all_links = list(set([item.get_property("href") for item in all_links]))
    if make_directories:
        try:
            pathlib.Path(save_path + "/pdf").mkdir(parents=True, exist_ok=False)
            pathlib.Path(save_path + "/txt").mkdir(parents=True, exist_ok=False)
        except:
            print("one of the directories already exists")
    driver.quit()
    file_names = []
    file_names_failed = []
    good, bad = 0, 0
    exceptions = []
    for link in tqdm(all_links, desc="Downloading and Saving: {}".format(period)):
        response = requests.get(link)
        file_name = save_path + "/pdf" + "/" + ".".join(("_".join(link.split("/")[6:])).split(".")[0:-1]) + ".pdf"
        try:
            with open(file_name, 'wb') as f:
                f.write(response.content)
            file_names.append((link, file_name))
            good += 1
        except Exception as e:
            file_names_failed.append((link, file_name))
            exceptions.append(str(e))
            bad += 1
    print("completed requests: {}; failed requests: {}\n".format(good, bad))
    print("Exceptions occured: {}\n".format(",".join(list(set(exceptions)))))
    file_names_failed_2 = []
    good, bad = 0, 0
    exceptions = []
    for file_name in tqdm(file_names, desc="Converting to txt: {}".format(period)):
        try:
            text = textract.process(file_name[-1])
            text = text.decode("utf-8").split("\n")
            with codecs.open(save_path + "/txt/" + ".".join(file_name[-1].split("/")[-1].split(".")[0:-1]) + ".txt", "w", "utf-8") as f:
                for line in text:
                    f.write(line + "\n")
            good += 1
        except Exception as e:
            exceptions.append(str(e))
            file_names_failed_2.append(file_name)
            bad += 1
    print("completed conversions: {}; failed conversions: {}\n".format(good, bad))
    print("Exceptions occured: {}\n".format(",".join(list(set(exceptions)))))

    for failed in file_names_failed_2:
        file_names.remove(failed)
    file_names_failed = file_names_failed + file_names_failed_2

    return [file_names, file_names_failed]

def brandenburg_crawler_sp(make_directories: bool = True,
                        save_path: str = "/vol/s5935481/parlamentary/brandenburg"):
    """
    Function for downloading and saving (as pdf and txt) all "Plenumprotokolle" for brandenburg.
    :param make_directories:
    :param save_path:
    :return:
    """
    if make_directories:
        try:
            pathlib.Path(save_path).mkdir(parents=True, exist_ok=False)
        except:
            print(save_path + " already exists...")
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
    configs = []
    for period in tqdm(electionperiods):
        if make_directories:
            try:
                pathlib.Path(save_path + "/" + period).mkdir(parents=True, exist_ok=False)
            except:
                print(save_path + "/" + period + " already exists...")

        configs.append([period, "Plenarprotokoll", save_path + "/" + period])
    driver.quit()
    del driver
    print("Start Downloading")

    results = []
    for config in configs:
        results.append(brandenburg_proc_sp(config))

    with open(save_path + "/stats.txt", "w") as f:
        correct = []
        failed = []
        for result in results:
            correct.extend([res[0] for res in result[0]])
            failed.extend([res[0] for res in result[1]])
        f.write("completed requests + conversions : {}".format(len(correct)) + "\n")
        f.write("failed requests + conversions    : {}".format(len(failed)) + "\n")
        f.write("total requests                   : {}".format(len(correct) + len(failed)) + "\n")
        f.write("==========completed requests==========" + "\n")
        for com in correct:
            f.write(com + "\n")
        f.write("==========failed requests==========" + "\n")
        for fail in failed:
            f.write(fail + "\n")
    return



def hamburg_crawler(make_directories:bool = True,
                    save_path: str = "/vol/s5935481/parlamentary/hamburg"):

    if make_directories:
        try:
            pathlib.Path(save_path).mkdir(parents=True, exist_ok=False)
        except:
            print(save_path + " already exists...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome("/home/stud_homes/s5935481/work4/parliament_crawler/src/crawling_services/chromedriver",
                              options=chrome_options)

    url = "https://www.buergerschaft-hh.de/parldok/neuedokumente"
    driver.get(url)
    time.sleep(5)
    checkbox = driver.find_element_by_xpath("/html/body/div[4]/div[2]/div/form/fieldset/table/tbody/tr[1]/td[2]/input[2]")
    driver.execute_script("arguments[0].setAttribute('checked', 'true')", checkbox)
    button = driver.find_element_by_xpath("/html/body/div[4]/div[2]/div/form/fieldset/table/tbody/tr[2]/td[2]/input")
    button.submit()
    pages = set()
    for i in tqdm(range(2, 12), desc="Crawling links"):
        source = driver.page_source
        soup = BeautifulSoup(source, 'html.parser')
        pattern = re.compile("pdf")
        for link in soup.find_all("a", href=pattern):
            if "href" in link.attrs:
                if link.attrs["href"] not in pages:
                    new_page = link.attrs["href"]
                    pages.add(new_page)
        if i < 11:
            driver.get(url + "/" + str(i))
            time.sleep(20)
    print("{} Links were collected...".format(len(pages)))
    pages = list(pages)
    pages = ["https://www.buergerschaft-hh.de" + link for link in pages]
    if make_directories:
        try:
            pathlib.Path(save_path + "/pdf").mkdir(parents=True, exist_ok=False)
            pathlib.Path(save_path + "/txt").mkdir(parents=True, exist_ok=False)
        except:
            print("one of the directories already exists")
    file_names = []
    good, bad = 0,0
    file_names_failed = []
    exceptions = []
    for link in tqdm(pages, desc="Downloading all files: "):
        electoral_term = "electoral_term_" + link.split("_")[1]
        try:
            pathlib.Path(save_path + "/pdf/" + electoral_term).mkdir(parents=True, exist_ok=False)
        except:
            pass
        response = requests.get(link)
        file_name = save_path + "/pdf/" + electoral_term + "/" + link.split("/")[-1]
        try:
            with open(file_name, 'wb') as f:
                f.write(response.content)
            file_names.append((link, file_name))
            good += 1
        except Exception as e:
            file_names_failed.append((link, file_name))
            exceptions.append(str(e))
            bad += 1
    print("completed requests: {}; failed requests: {}\n".format(good, bad))
    print("Exceptions occured: {}\n".format(",".join(list(set(exceptions)))))

    file_names_failed_2 = []
    good, bad = 0, 0
    exceptions = []
    for file_name in tqdm(file_names, desc="Converting to txt"):
        try:
            text = textract.process(file_name[-1])
            text = text.decode("utf-8").split("\n")
            with codecs.open(file_name[-1].replace("pdf", "txt"),
                             "w", "utf-8") as f:
                for line in text:
                    f.write(line + "\n")
            good += 1
        except Exception as e:
            exceptions.append(str(e))
            file_names_failed_2.append(file_name)
            bad += 1
    print("completed conversions: {}; failed conversions: {}\n".format(good, bad))
    print("Exceptions occured: {}\n".format(",".join(list(set(exceptions)))))
    driver.quit()
    return



def main(args):
    if args.brandenburg:
        brandenburg_crawler_sp()
    if args.hamburg:
        hamburg_crawler()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--brandenburg', action='store_true',
                        help='Do you want to crawl documents for brandenburg?')
    parser.add_argument('--hamburg', action='store_true',
                        help='Do you want to crawl documents for hamburg?')
    args = parser.parse_args()

    main(args)
