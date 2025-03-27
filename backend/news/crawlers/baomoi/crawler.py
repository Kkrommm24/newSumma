from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from news.utils.check_exist_in_db import check_url_exist, check_category_exist
from news.crawlers.driver import get_driver
import time
import logging

logger = logging.getLogger(__name__)

class BaomoiCrawler:
    def __init__(self, base_url="https://baomoi.com"):
        self.base_url = base_url
        self.urls_processed = []
        
    def crawl(self, limit=10):
        results = []
        driver = get_driver()
        
        try:
            # 1. Mở trang chủ và tìm danh sách bài viết
            self._open_homepage(driver)
            articles = self._get_article_list(driver, limit)
            
            # 2. Xử lý từng bài viết
            for i in range(min(limit, len(articles))):
                try:
                    logger.info(f"Đang xử lý bài viết {i+1}/{min(limit, len(articles))}")
                    article = articles[i]
                    
                    # 2.1 Scroll để hiển thị bài viết
                    self._scroll_to_article(driver, article)
                    
                    # 2.2 Lấy thông tin cơ bản từ trang chủ
                    article_info = self._get_basic_info(article)
                    if not article_info:
                        continue
                    
                    title, url, published_at = article_info
                    
                    # 2.3 Kiểm tra URL đã tồn tại
                    if self._check_existing_url(url):
                        continue
                    
                    # 2.4 Mở tab mới và truy cập vào URL bài viết
                    if not self._open_article_page(driver, url):
                        continue
                    
                    # 2.5 Lấy thông tin category
                    category_name = self._get_category(driver, url)
                    if not category_name:
                        self._close_article_tab(driver)
                        continue
                    
                    # 2.6 Lấy nội dung bài viết
                    content = self._get_content(driver, url)
                    if not content:
                        self._close_article_tab(driver)
                        continue
                    
                    # 2.7 Lấy URL hình ảnh
                    image_url = self._get_image_url(driver, url)
                    if not image_url:
                        self._close_article_tab(driver)
                        continue
                    
                    # 2.8 Đóng tab và quay lại trang chủ
                    self._close_article_tab(driver)
                    
                    # 2.9 Thêm bài viết vào kết quả
                    results.append({
                        'title': title,
                        'url': url,
                        'published_at': published_at,
                        'image_url': image_url,
                        'content': content,
                        'category_name': category_name
                    })
                    
                    # 2.10 Ghi log bài viết thành công
                    self._log_success(url, title)
                    
                except Exception as e:
                    logger.error(f"❌ Lỗi xử lý bài viết thứ {i+1}.")
                    # Đảm bảo đóng tab nếu đang ở tab bài viết
                    if len(driver.window_handles) > 1:
                        self._close_article_tab(driver)
                    continue
        except Exception as e:
            logger.error(f"❌ Lỗi trong quá trình crawl.")
        finally:
            # Đảm bảo luôn đóng driver khi hoàn thành
            driver.quit()
            logger.info(f"Kết thúc crawl: thu thập được {len(results)}/{limit} bài viết")

        return results
    
    def _open_homepage(self, driver):
        """Mở trang chủ Baomoi"""
        logger.info(f"Đang mở trang chủ {self.base_url}")
        driver.get(self.base_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, '//h3[@class="font-semibold block"]/a'))
        )
        logger.info("Đã tải trang chủ thành công")
    
    def _get_article_list(self, driver, limit):
        logger.info("Đợi trang tải đầy đủ các bài viết...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"group/card")]'))
        )
        time.sleep(3)
        
        try:
            articles = []
            articles = driver.find_elements(By.XPATH, '//div[contains(@class,"group/card") and contains(@class,"bm-card")]')
            if not articles:
                articles = driver.find_elements(By.XPATH, '//div[contains(@class,"group/card")]')
            
            if not articles:
                h3_elements = driver.find_elements(By.XPATH, '//h3[@class="font-semibold block"]')
                if h3_elements:
                    articles = []
                    for h3 in h3_elements:
                        try:
                            parent = h3.find_element(By.XPATH, './ancestor::div[contains(@class,"group/card")]')
                            articles.append(parent)
                        except:
                            continue          
            logger.info(f"Đã tìm thấy {len(articles)} bài viết trên trang")
            
            if len(articles) < limit:
                logger.info("Số bài viết không đủ, đang cuộn trang để tải thêm")
                attempts = 0
                while len(articles) < limit and attempts < 5:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    articles = driver.find_elements(By.XPATH, '//div[contains(@class,"group/card") and contains(@class,"bm-card")]')
                    if not articles:
                        articles = driver.find_elements(By.XPATH, '//div[contains(@class,"group/card")]')
                    logger.info(f"Sau khi cuộn: tìm thấy {len(articles)} bài viết")
                    attempts += 1
            return articles
        except Exception as e:
            logger.error(f"❌ Lỗi khi tìm bài viết.")
            return []
    
    def _scroll_to_article(self, driver, article):
        try:
            if not article:
                logger.warning("Đối tượng article không tồn tại, bỏ qua bước cuộn")
                return
                
            logger.info("Đang cuộn đến bài viết")
            try:
                driver.execute_script("return arguments[0].tagName", article)
            except:
                logger.warning("Phần tử article không còn tồn tại trong DOM")
                return
                
            # Sử dụng JavaScript để cuộn đến phần tử
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", article)
                time.sleep(1.5)  # Tăng thời gian chờ sau khi cuộn
            except Exception as e:
                logger.warning(f"Không thể sử dụng scrollIntoView.")
                
                # Phương pháp thay thế - cuộn dựa trên offset
                try:
                    y_position = driver.execute_script("return arguments[0].getBoundingClientRect().top + window.pageYOffset;", article)
                    driver.execute_script(f"window.scrollTo(0, {y_position - 200});")
                    time.sleep(1)
                except Exception as e2:
                    logger.warning(f"Không thể cuộn theo cách thay thế: {str(e2)}")
        except Exception as e:
            logger.warning(f"❌ Không thể cuộn đến bài viết.")
    
    def _get_basic_info(self, article):
        """Lấy thông tin cơ bản của bài viết từ trang chủ"""
        try:
            a_tag = article.find_element(By.XPATH, './/h3[@class="font-semibold block"]/a')
            title = a_tag.get_attribute("title")
            url = a_tag.get_attribute("href")
            
            time_tag = article.find_element(By.XPATH, './/time[contains(@class, "content-time")]')
            published_at = time_tag.get_attribute("datetime")
            
            logger.info(f"Đã lấy thông tin cơ bản: {title}")
            return title, url, published_at
        except Exception as e:
            logger.warning(f"❌ Không thể lấy thông tin bài viết từ trang chủ.")
            return None
    
    def _check_existing_url(self, url):
        """Kiểm tra URL đã tồn tại trong database chưa"""
        if check_url_exist(url):
            logger.info(f"⏭️ Bỏ qua URL đã tồn tại: {url}")
            self.urls_processed.append({
                "url": url,
                "success": False,
                "reason": "URL đã tồn tại trong DB"
            })
            return True
        return False
    
    def _open_article_page(self, driver, url):
        """Mở tab mới và truy cập vào URL bài viết"""
        try:
            logger.info(f"Đang mở tab mới để truy cập: {url}")
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(url)
            # Đợi trang tải xong
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//img[contains(@src, ".j") and contains(@alt, "")]'))
            )
            # Cuộn trang để tải đầy đủ nội dung
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1)
            return True
        except Exception as e:
            logger.warning(f"❌ Không thể mở trang bài viết {url}.")
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            self.urls_processed.append({
                "url": url,
                "success": False,
                "reason": f"Không thể mở trang bài viết."
            })
            return False
    
    def _get_category(self, driver, url):
        """Lấy thông tin category của bài viết"""
        try:
            main_content = driver.find_element(By.XPATH, '//div[contains(@class, "bm-section block main-container")]')
            category_elem = main_content.find_element(By.XPATH, './/a[contains(@class, "item")]')
            category_name = category_elem.text.strip()
            
            if category_name == 'SỨC KHỎE':
                category_name = 'SỨC KHOẺ'
                
            if not check_category_exist(category_name):
                logger.info(f"⏭️ Bỏ qua category không tồn tại: {category_name}")
                self.urls_processed.append({
                    "url": url,
                    "success": False,
                    "reason": f"Category không tồn tại: {category_name}"
                })
                return None
            
            logger.info(f"Đã lấy category: {category_name}")
            return category_name
        except Exception as e:
            logger.warning(f"❌ Không thể lấy thông tin category.")
            self.urls_processed.append({
                "url": url,
                "success": False,
                "reason": f"Không thể lấy category."
            })
            return None
    
    def _get_content(self, driver, url):
        """Lấy nội dung bài viết"""
        main_content = driver.find_element(By.XPATH, '//div[contains(@class,"content-main relative")]')
        logger.info(f"Đã tìm thấy main_content cho {url}")
        
        # Thử lấy paragraphs bằng XPath chính
        paragraphs = main_content.find_elements(By.XPATH, './/p[contains(@class, "text") and not(contains(@class, "body-author"))]')

        content = "\n\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
        
        # Nếu vẫn không có nội dung, thử lấy toàn bộ text của main_content
        if not content:
            logger.warning(f"Không tìm thấy nội dung qua paragraphs, thử lấy toàn bộ text")
            content = main_content.text
        
        # Kiểm tra nội dung trống
        if not content:
            logger.warning(f"❌ Không thể lấy content cho {url}")
            self.urls_processed.append({
                "url": url,
                "success": False,
                "reason": "Không thể lấy content"
            })
            return None
        
        logger.info(f"Đã lấy nội dung bài viết ({len(content)} ký tự)")
        return content
    
    def _get_image_url(self, driver, url):
        """Lấy URL hình ảnh của bài viết"""
        try:
            # Phương pháp 1: Tìm trong main-content
            main_content = driver.find_element(By.XPATH, '//div[contains(@class,"content-main relative")]')
            img_elem = main_content.find_element(By.XPATH, './/img[contains(@src, ".j") and contains(@alt, "")]')
            image_url = img_elem.get_attribute("src")
            logger.info(f"Đã lấy được ảnh từ main-content: {image_url}")
            return image_url
        except Exception:
            # Phương pháp 2: Tìm bất kỳ ảnh nào
            try:
                logger.info("Thử tìm ảnh bằng phương pháp khác")
                img_elem = driver.find_element(
                    By.XPATH,
                    '//img[contains(@src, ".jpg") or contains(@src, ".png") or contains(@src, ".jpeg")]'
                )
                image_url = img_elem.get_attribute("src")
                logger.info(f"Đã lấy được ảnh bằng phương pháp 2: {image_url}")
                return image_url
            except Exception as e:
                logger.warning(f"❌ Không thể lấy ảnh đại diện.")
                self.urls_processed.append({
                    "url": url,
                    "success": False,
                    "reason": "Không thể lấy ảnh đại diện"
                })
                return None
    
    def _close_article_tab(self, driver):
        """Đóng tab bài viết và quay lại trang chủ"""
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception as e:
            logger.error(f"❌ Lỗi khi đóng tab.")
            # Cố gắng phục hồi bằng cách quay lại tab đầu tiên
            if len(driver.window_handles) > 0:
                driver.switch_to.window(driver.window_handles[0])
    
    def _log_success(self, url, title):
        """Ghi log bài viết crawl thành công"""
        logger.info(f"✅ Crawl thành công: {title}")
        self.urls_processed.append({
            "url": url,
            "success": True,
            "title": title
        })
