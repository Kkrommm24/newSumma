from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from crawler.crawlers.driver import get_driver
from news.models import NewsArticle, Category
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
            self._open_homepage(driver)
            potential_articles_elements = self._get_article_list(driver, limit * 2)
            
            basic_infos = []
            potential_urls = set()
            for elem in potential_articles_elements:
                info = self._get_basic_info(elem)
                if info:
                    basic_infos.append(info)
                    potential_urls.add(info[1])
            
            existing_urls_in_db = set()
            if potential_urls:
                try:
                    existing_urls_in_db = set(NewsArticle.objects.filter(url__in=list(potential_urls)).values_list('url', flat=True))
                    logger.info(f"Tìm thấy {len(existing_urls_in_db)} URL đã tồn tại trong DB từ batch này.")
                except Exception as db_err:
                    logger.error(f"Lỗi khi kiểm tra URL tồn tại hàng loạt: {db_err}")
            
            try:
                valid_category_names_in_db = set(Category.objects.values_list('name', flat=True))
            except Exception as db_err:
                logger.error(f"Lỗi khi lấy danh sách category hợp lệ: {db_err}")
                valid_category_names_in_db = set()

            processed_count = 0
            for i in range(len(basic_infos)):
                if processed_count >= limit:
                    break
                    
                title, url, published_at = basic_infos[i]

                if url in existing_urls_in_db:
                    logger.info(f"⏭️ Bỏ qua URL đã tồn tại (đã kiểm tra): {url}")
                    continue

                try:
                    logger.info(f"Đang xử lý chi tiết bài viết {i+1}/{len(basic_infos)} (target: {limit}) - URL: {url}")
                    
                    if not self._open_article_page(driver, url):
                        continue
                    
                    category_name = self._get_category(driver, url)
                    if not category_name or category_name not in valid_category_names_in_db:
                        logger.info(f"⏭️ Bỏ qua category không hợp lệ hoặc không tìm thấy: {category_name}")
                        self._close_article_tab(driver)
                        self.urls_processed.append({"url": url,"success": False,"reason": f"Category không hợp lệ/không tìm thấy: {category_name}"})
                        continue
                    
                    content = self._get_content(driver, url)
                    if not content:
                        self._close_article_tab(driver)
                        continue
                    
                    image_url = self._get_image_url(driver, url)
                    if not image_url:
                        self._close_article_tab(driver)
                        continue
                    
                    self._close_article_tab(driver)
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'published_at': published_at,
                        'image_url': image_url,
                        'content': content,
                        'category_name': category_name
                    })
                    processed_count += 1
                    self._log_success(url, title)
                    existing_urls_in_db.add(url) 
                    
                except Exception as detail_err:
                    logger.error(f"❌ Lỗi xử lý chi tiết bài viết {url}: {detail_err}")
                    if len(driver.window_handles) > 1:
                        self._close_article_tab(driver)
                    continue
        except Exception as e:
            logger.error(f"❌ Lỗi trong quá trình crawl.")
        finally:
            driver.quit()
            logger.info(f"Kết thúc crawl: thu thập được {len(results)} bài viết (target: {limit})")

        return results
    
    def _open_homepage(self, driver):
        driver.get(self.base_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, '//h3[@class="font-semibold block"]/a'))
        )
    
    def _get_article_list(self, driver, limit):
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
            
            if len(articles) < limit:
                attempts = 0
                while len(articles) < limit and attempts < 5:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    articles = driver.find_elements(By.XPATH, '//div[contains(@class,"group/card") and contains(@class,"bm-card")]')
                    if not articles:
                        articles = driver.find_elements(By.XPATH, '//div[contains(@class,"group/card")]')
                    attempts += 1
            return articles
        except Exception as e:
            logger.error(f"❌ Lỗi khi tìm bài viết.")
            return []
    
    def _scroll_to_article(self, driver, article):
        try:
            if not article:
                return
            try:
                driver.execute_script("return arguments[0].tagName", article)
            except:
                return

            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", article)
                time.sleep(1.5)  # Tăng thời gian chờ sau khi cuộn
            except Exception as e:
                logger.warning(f"Không thể sử dụng scrollIntoView.")
                
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
            return title, url, published_at
        except Exception as e:
            return None
    
    def _open_article_page(self, driver, url):
        """Mở tab mới và truy cập vào URL bài viết"""
        try:
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
        try:
            main_content = driver.find_element(By.XPATH, '//div[contains(@class, "bm-section block main-container")]')
            category_elem = main_content.find_element(By.XPATH, './/a[contains(@class, "item")]')
            category_name = category_elem.text.strip()
            
            if category_name == 'SỨC KHỎE':
                category_name = 'SỨC KHOẺ'
            return category_name
        except Exception as e:
            logger.warning(f"❌ Không thể lấy thông tin category cho {url}.")
            return None
    
    def _get_content(self, driver, url):
        """Lấy nội dung bài viết"""
        main_content = driver.find_element(By.XPATH, '//div[contains(@class,"content-main relative")]')
        
        # Thử lấy paragraphs bằng XPath chính
        paragraphs = main_content.find_elements(By.XPATH, './/p[contains(@class, "text") and not(contains(@class, "body-author"))]')

        content = "\n\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
        
        if not content:
            content = main_content.text
        if not content:
            logger.warning(f"❌ Không thể lấy content cho {url}")
            self.urls_processed.append({
                "url": url,
                "success": False,
                "reason": "Không thể lấy content"
            })
            return None
        return content
    
    def _get_image_url(self, driver, url):
        """Lấy URL hình ảnh của bài viết"""
        try:
            # Phương pháp 1: Tìm trong main-content
            main_content = driver.find_element(By.XPATH, '//div[contains(@class,"content-main relative")]')
            img_elem = main_content.find_element(By.XPATH, './/img[contains(@src, ".j") and contains(@alt, "")]')
            image_url = img_elem.get_attribute("src")
            return image_url
        except Exception:
            try:
                img_elem = driver.find_element(
                    By.XPATH,
                    '//img[contains(@src, ".jpg") or contains(@src, ".png") or contains(@src, ".jpeg")]'
                )
                image_url = img_elem.get_attribute("src")
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
