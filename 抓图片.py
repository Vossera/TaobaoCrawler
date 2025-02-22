from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import TimeoutException
from pyquery import PyQuery as pq
import time
import os
import requests
import subprocess

# Chrome 可执行文件路径
chrome_path = "C:\Program Files\Google\Chrome\Application\chrome.exe"  # Windows 示例路径
# 如果需要指定其他路径，请根据实际情况修改

# 命令行参数
chrome_args = [
    chrome_path,
    "--remote-debugging-port=9222",
]

# 启动 Chrome
try:
    process = subprocess.Popen(chrome_args)
    print("Chrome 已启动，远程调试端口为 9222")
except Exception as e:
    print(f"启动 Chrome 时出错: {e}")

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "localhost:9222") #此处端口保持和命令行启动的端口一致
driver = Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)
driver.maximize_window()

counter = 1
# 模拟淘宝登录
# 从 url.txt 中读取 URL

def get_urls():
    with open("url.txt", "r") as f:
        urls = [line.strip() for line in f.readlines()]  # 读取所有行并去除换行符
    return urls

def load_page(url):
    driver.get(url)
    # 拉到底部，但是有新的加载就会退回到三分之二的位置；加载出来后又跳到四分之一的位置
    driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
    time.sleep(1)   # 等待一段时间，方便查看滚动的效果
    #driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')  # 再继续滚动
    
def download_file(url, folder='test', filename=None, max_retries=3, retry_delay=5):
    global counter
    if not os.path.exists(folder):
        os.makedirs(folder)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://item.taobao.com/',  # 必须与图片所在商品页一致
        'Accept': 'image/webp,image/apng,*/*;q=0.8',
    }
    # 如果未提供文件名，尝试从 URL 中提取
    if not filename:
        if 'jpg' in url:
            filename = f"{counter}.jpg"
        elif 'png' in url:
            filename = f"{counter}.png"
        elif 'mp4' in url:
            filename = f"{counter}.mp4"
    counter += 1
    filepath = os.path.join(folder, filename)
    # 重试机制
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, headers=headers)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                print(f"文件已保存到: {filepath}")
                return  # 下载成功，退出函数
            else:
                print(f"尝试 {attempt + 1}/{max_retries}: 无法下载文件: {url} (状态码: {response.status_code})")
        except Exception as e:
            print(f"尝试 {attempt + 1}/{max_retries}: 下载文件时出错: {e}")
        
        # 如果未达到最大重试次数，等待一段时间后重试
        if attempt < max_retries - 1:
            print(f"等待 {retry_delay} 秒后重试...")
            time.sleep(retry_delay)
    
    print(f"下载失败: {url} (已达到最大重试次数 {max_retries})")

def get_product_pics():
    html = driver.page_source
    doc = pq(html)


    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '.switchTabsItem--NDCNfRRJ.switchTabsItemSelect--icApCpu_')
    ))    
    video_click = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '.switchTabsItem--NDCNfRRJ.switchTabsItemSelect--icApCpu_')
    ))    
    video_click.click()
    time.sleep(1)
    html = driver.page_source
    doc = pq(html)
    mp4_url = doc('video.lib-video').attr('src')
    items = doc('li.thumbnail--TxeB1sWz').items()
    for item in items:
        image_url = item.find('img').attr('src')
        print(image_url)
        download_file(image_url, folder=driver.title)

    if mp4_url:
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://item.taobao.com/',  # 必须与触发视频的页面一致
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        }

    # 启用会话并自动处理重定向
    mp4_url = "https:" + mp4_url
    session = requests.Session()
    response = session.get(mp4_url, headers=headers, allow_redirects=True)
    url = response.url
    download_file(url, folder=driver.title)




if __name__ == '__main__':
    try:
        urls = get_urls()
        
        for url in urls:
            load_page(url)
            get_product_pics()
    except:
        import traceback
        traceback.print_exc()
    driver.close()
    time.sleep(5)
    os.system('taskkill /im chromedriver.exe /F')
    os.system('taskkill /im chrome.exe /F')
