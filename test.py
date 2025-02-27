from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import urljoin, urlparse
import os
import json
import re
import time

# 设置Chrome选项，可以添加更多选项如代理设置等
chrome_options = Options()
# chrome_options.add_argument("--headless")  # 运行时不会打开浏览器窗口
# chrome_options.add_argument("--disable-gpu")
# chrome_options.add_argument("--no-sandbox")

# 如果ChromeDriver不在系统PATH中，请指定其路径
webdriver_path = "D:/msedgedriver.exe"  # 修改为您的chromedriver实际路径

service = Service(executable_path=webdriver_path)
driver = webdriver.Edge(service=service, options=chrome_options)

visited_urls = set()  # 已经访问过的URL集合

def is_valid(url):
    """检查URL是否属于目标站点"""
    parsed = urlparse(url)
    return bool(parsed.netloc) and 'info.xzcit.cn' in url

def is_element(by, value):
    """检查元素是否存在"""
    try:
        driver.find_element(by, value)
    except:
        return False
    return True

def smooth_scrol(scroll_step=200, wait_time=0.1):
    """
    按照指定步长和等待时间进行页面滚动。
    :param scroll_step: 每次滚动的像素数
    :param wait_time: 每次滚动间的等待时间(秒)
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
    """使用Selenium获取页面内容"""
    if url in visited_urls:
        return None
    
    print(f"Crawling: {url}")
    visited_urls.add(url)
    
    driver.get(url)

    smooth_scrol()

    html_content = driver.page_source
    return html_content if html_content else None

def parse_articles_and_links(url):
    """解析HTML内容提取文章信息和内部链接"""
    articles = []
    links = []

    if is_element(By.ID, 'content-detail-container'):
        title = driver.find_element(By.CSS_SELECTOR, 'section-title').text
        content = driver.find_element('div', class_='content-container')
        text = ''
        for p in content.find_elements(By.TAG_NAME, 'p'):
            if p.text != '':
                text += p.text + '\n'
        text = "".join(re.split('\xa0| ', text))
        articles.append({'title': title, 'content': text})
        print({'title': title, 'content': text})

    # 提取页面中的所有链接
    main = driver.find_element(By.CSS_SELECTOR, 'main')
    for a in main.find_elements(By.TAG_NAME, 'a'):
        link = a.get_attribute("href")
        full_link = urljoin(url, link)
        if is_valid(full_link) and full_link not in visited_urls and full_link not in links :
            links.append(full_link)

    clickable_count = len(driver.find_elements(By.CSS_SELECTOR, 'div.clickable'))
    for i in range(clickable_count):
        if i == 18:
            print(18)
        div = driver.find_elements(By.CSS_SELECTOR, 'div.clickable')[i]
        print(div.get_attribute('innerHTML'))
        # 使用ActionChains进行点击
        actions = ActionChains(driver)
        actions.move_to_element(div).click().perform()
        time.sleep(0.5)
        link = driver.current_url
        full_link = urljoin(url, link)
        if is_valid(full_link) and full_link not in visited_urls:
            print(full_link)
            links.append(full_link)
        driver.back()  # 返回上一页
        smooth_scrol()
        
    return articles, links

def crawl(url):
    """递归函数，用于爬取页面"""
    html_content = fetch_page_content(url)
    if not html_content:
        return

    articles, links = parse_articles_and_links(url)
    
    with open(os.path.join(output_dir, f"articles_{time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime())}.json"), "w", encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

    for link in links:
        crawl(link)  # 递归调用自身处理每个新链接

if __name__ == '__main__':
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    start_url = f"https://info.xzcit.cn/#/"  # 确定起始页面
    crawl(start_url)
    driver.quit()  # 关闭浏览器
