from selenium import webdriver

def get_driver(headless=True):
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("window-size=1920x1080")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-extensions')  # Tắt extensions để tránh xung đột
    chrome_options.add_argument('--disable-browser-side-navigation')  # Tránh lỗi timeout
    chrome_options.add_argument('--disable-infobars')  # Tắt thông báo
    chrome_options.add_argument('--disable-gpu')  # Tắt GPU để tránh một số vấn đề

    chrome_options.add_argument('--incognito')
    chrome_options.add_argument('--disable-application-cache')
    
    # chrome_options.add_argument('user-data-dir=C:\\Users\\draxe\\AppData\\Local\\Google\\Chrome\\User Data')
    # Khởi tạo driver
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver