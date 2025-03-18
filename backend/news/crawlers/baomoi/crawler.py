from selenium.webdriver.common.by import By
from news.utils.check_exist_in_db import check_url_exist, check_category_exist
from news.crawlers.driver import get_driver
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

logger = logging.getLogger(__name__)

class BaomoiCrawler:
    def __init__(self, base_url="https://baomoi.com"):
        self.base_url = base_url

    def crawl(self, limit=10):
        results = []
        driver = get_driver()
        try:
            driver.get("https://baomoi.com")
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, '//h3[@class="font-semibold block"]/a'))
            )

            articles = driver.find_elements(By.XPATH, '//div[contains(@class,"group/card")]')
            for i in range(min(limit, len(articles))):
                try:
                    # articles = driver.find_elements(By.XPATH, '//div[contains(@class,"group/card")]')
                    # if i >= len(articles):
                    #     break

                    article = articles[i]
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", article)
                    time.sleep(1)

                    try:
                        a_tag = article.find_element(By.XPATH, './/h3[@class="font-semibold block"]/a')
                        title = a_tag.get_attribute("title")
                        url = a_tag.get_attribute("href")

                        if check_url_exist(url):
                            logger.info(f"⏭️ Bỏ qua URL đã tồn tại: {url}")
                            continue
                        time_tag = article.find_element(By.XPATH, './/time[contains(@class, "content-time")]')
                        published_at = time_tag.get_attribute("datetime")
                    except Exception:
                        logger.warning("❌ Không thể lấy thông tin bài viết từ trang chủ")
                        continue

                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[1])
                    driver.get(url)

                    image_url = None
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//img[contains(@src, ".j") and contains(@alt, "")]'))
                        )
                        driver.execute_script("window.scrollBy(0, 1000);")
                        time.sleep(1)

                        
                        try:
                            main_content = driver.find_element(By.XPATH, '//div[contains(@class, "bm-section block main-container")]')
                            category_elem = main_content.find_element(By.XPATH, './/a[contains(@class, "item")]')
                            category_name = category_elem.text.strip()
                            if not check_category_exist(category_name):
                                logger.info(f"⏭️ Bỏ qua category không tồn tại: {category_name}")
                                continue
                        except Exception:
                            logger.warning("❌ Không thể lấy thông tin category")
                            continue

                        try:
                            main_content = driver.find_element(By.XPATH, '//div[contains(@class,"content-main relative")]')
                            paragraphs = main_content.find_elements(By.XPATH, './/p[contains(@class, "text") and not(contains(@class, "body-author"))]')
                            content = "\n\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
                        except Exception as e:
                            logger.warning(f"❌ Không thể lấy content: {e}")
                            continue

                        try:
                            main_content = driver.find_element(By.XPATH, '//div[contains(@class,"content-main relative")]')
                            img_elem = main_content.find_element(By.XPATH, './/img[contains(@src, ".j") and contains(@alt, "")]')
                            image_url = img_elem.get_attribute("src")
                        except Exception:
                            try:
                                img_elem = driver.find_element(
                                    By.XPATH,
                                    '//img[contains(@src, ".jpg") or contains(@src, ".png") or contains(@src, ".jpeg")]'
                                )
                                image_url = img_elem.get_attribute("src")
                            except Exception:
                                logger.warning("❌ Không thể lấy ảnh đại diện")
                                continue

                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    
                    except Exception:
                        if len(driver.window_handles) > 1:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                        logger.warning("❌ Không thể lấy thông tin bài viết từ trang bài viết")
                        continue                       
                except Exception:
                    continue

                results.append({
                            'title': title,
                            'url': url,
                            'published_at': published_at,
                            'image_url': image_url,
                            'content': content,
                            'category_name': category_name
                        })
        finally:
            driver.quit()

        return results
