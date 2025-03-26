from selenium.webdriver.common.by import By
from news.utils.check_exist_in_db import check_url_exist, check_category_exist
from news.utils.parse_datetime import parse_datetime_manual
from news.crawlers.driver import get_driver
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

logger = logging.getLogger(__name__)

class VNExpressCrawler:
    def __init__(self, base_url="https://vnexpress.net"):
        self.base_url = base_url

    def crawl(self, limit=20):
        results = []
        driver = get_driver()
        try:
            driver.get("https://vnexpress.net")
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, '//article'))
            )

            articles = driver.find_elements(By.XPATH, '//article')
            for i in range(min(limit, len(articles))):
                try:
                    article = articles[i]
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", article)
                    time.sleep(1)

                    try:
                        
                        title_elem = article.find_element(By.XPATH, './/h3[contains(@class, "title-news")]')
                        title = title_elem.text.strip()
                        url_elem = title_elem.find_element(By.XPATH, './/a[contains(@href, "")]')
                        url = url_elem.get_attribute("href")
                        if check_url_exist(url):
                            logger.info(f"⏭️ Bỏ qua URL đã tồn tại: {url}")
                            continue
                    except Exception:
                        logger.warning("❌ Không thể lấy thông tin bài viết từ trang chủ")
                        continue

                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[1])
                    driver.get(url)
                    logger.info(f"Đã chuyển đến: {driver.current_url}")

                    try:
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'article.fck_detail'))
                        )
                        
                        # Scroll nhẹ nhàng hơn
                        driver.execute_script("window.scrollTo(0, 700);")
                        time.sleep(2)
                        
                        # Đợi paragraph đầu tiên
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'p.Normal'))
                        )

                        try:
                            datetime_elem = driver.find_element(By.XPATH, '//span[contains(@class, "date")]')
                            published_at = parse_datetime_manual(datetime_elem.text.strip())
                        except Exception:
                            logger.warning("❌ Không thể lấy thông tin datetime")
                            continue
                        
                        try:
                            category_elem = driver.find_element(By.XPATH, '//ul[contains(@class, "breadcrumb")]//a[contains(@data-medium, "Menu")]')
                            category_name = category_elem.text.strip().upper()
                            if not check_category_exist(category_name):
                                logger.info(f"⏭️ Bỏ qua category không tồn tại: {category_name}")
                                continue
                        except Exception:
                            logger.warning("❌ Không thể lấy thông tin category")
                            continue

                        try:
                            paragraphs = driver.find_elements(By.XPATH, './/p[contains(@class, "Normal") or contains(@class, "description")]')
                            content = "\n\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
                            
                            # Thêm logging để debug
                            logger.info(f"Số đoạn văn tìm thấy: {len(paragraphs)}")
                            logger.info(f"Độ dài content: {len(content)} ký tự")
                            
                            if len(content) < 50:
                                logger.warning(f"❌ Nội dung quá ngắn hoặc trống: {url}")
                                continue
                                
                        except Exception as e:
                            logger.warning(f"❌ Không thể lấy content: {e}")
                            continue

                        image_url = None
                        try:
                            img_elem = driver.find_element(By.XPATH, './/img[contains(@src, ".j") and contains(@alt, "")]')
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
                    except Exception as e:
                        logger.exception("⚠️ Lỗi không xác định trong crawl(): %s", str(e))
                        continue

                    logger.info(f"✅ Đã crawl thành công bài: {title}")
                    if image_url:
                        results.append({
                            'title': title,
                            'url': url,
                            'published_at': published_at,
                            'image_url': image_url,
                            'content': content,
                            'category_name': category_name
                        })
                except Exception:
                    continue
        finally:
            driver.quit()

        return results
