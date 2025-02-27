from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urljoin, urlparse
import os
import json
import re
import time

start_url = "https://www.xzcit.cn/"
visited_urls = []  # 已经访问过的URL
articles = []

options = Options()
# options.add_argument("--headless")
# options.add_argument("--disable-gpu")
# options.add_argument("--no-sandbox")

service = Service(executable_path='D:/msedgedriver.exe')
driver = webdriver.Edge(service=service, options=options)

def is_valid(url):
    """检查URL是否属于目标站点"""
    parsed = urlparse(url)
    return bool(parsed.netloc) and 'www.xzcit.cn' in url

def is_element(by, value):
    """检查元素是否存在"""
    try:
        driver.find_element(by, value)
    except:
        return False
    return True

def smooth_scrol(scroll_step=300, wait_time=0.1):
    """
    按照指定步长和等待时间进行页面滚动。
    scroll_step: 每次滚动的像素数
    wait_time: 每次滚动间的等待时间
    """
    driver.execute_script("window.scrollTo({top: 0});")
    # 获取当前文档高度
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        for i in range(0, last_height, scroll_step):
            driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(wait_time)  # 控制滚动速度  
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def fetch_page_content(url):
    """获取页面内容"""
    if url in visited_urls:
        return None
    
    print(f"Crawling: {url}")
    visited_urls.append(url)
    
    try:
        driver.get(url)
    except:
        return None

    smooth_scrol()

    html_content = driver.page_source
    return html_content if html_content else None

def parse_articles_and_links(url):
    """提取文章信息和内部链接""" 
    links = []

    if is_element(By.CLASS_NAME, 'article'):
        title = driver.find_element(By.CLASS_NAME, 'arti_title').text
        content = driver.find_element(By.CLASS_NAME, 'entry')
        text = ''
        for p in content.find_elements(By.TAG_NAME, 'p'):
            if p.text != '':
                text += p.text + '\n'
        text = "".join(re.split('\xa0| ', text))
        articles.append({'title': title, 'content': text})
        print({'title': title, 'content': text})

    # 提取页面中的所有链接
    for a in driver.find_elements(By.TAG_NAME, 'a'):
        link = a.get_attribute("href")
        full_link = urljoin(url, link)
        if is_valid(full_link) and full_link not in visited_urls and full_link not in links :
            links.append(full_link)
            print(full_link)

    return links

def crawl(url):
    """爬取页面"""
    html_content = fetch_page_content(url)
    if not html_content:
        return

    links = parse_articles_and_links(url)
    
    for link in links:
        crawl(link)  # 递归调用自身处理新链接

if __name__ == '__main__':
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    crawl(start_url)

    with open(os.path.join(output_dir, f"articles_{time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime())}.json"), "w", encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

    driver.quit()
