from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from news.utils.parse_datetime import parse_datetime_manual
from crawler.crawlers.driver import get_driver
from news.models import NewsArticle, Category
import time
import logging

logger = logging.getLogger(__name__)


class VNExpressCrawler:
    def __init__(self, base_url="https://vnexpress.net"):
        self.base_url = base_url
        self.urls_processed = []

    def crawl(self, limit=10):
        results = []
        driver = get_driver()

        try:
            self._open_homepage(driver)
            potential_articles_elements = self._get_article_list(
                driver, limit * 2)

            basic_infos = []
            potential_urls = set()
            for elem in potential_articles_elements:
                info = self._get_basic_info(elem)
                if info:
                    title, url = info
                    if self._is_video_url(url):
                        continue
                    basic_infos.append(info)
                    potential_urls.add(url)
            existing_urls_in_db = set()
            if potential_urls:
                try:
                    existing_urls_in_db = set(
                        NewsArticle.objects.filter(
                            url__in=list(potential_urls)).values_list(
                            'url', flat=True))
                    logger.info(
                        f"Tìm thấy {len(existing_urls_in_db)} URL VNExpress đã tồn tại trong DB từ batch này.")
                except Exception as db_err:
                    logger.error(
                        f"Lỗi khi kiểm tra URL VNExpress tồn tại hàng loạt: {db_err}")

            try:
                valid_category_names_in_db = set(
                    Category.objects.values_list('name', flat=True))
            except Exception as db_err:
                logger.error(
                    f"Lỗi khi lấy danh sách category hợp lệ: {db_err}")
                valid_category_names_in_db = set()
            # -----------------------------------------------------

            processed_count = 0
            for i in range(len(basic_infos)):
                if processed_count >= limit:
                    break

                title, url = basic_infos[i]

                if not title or not url:
                    continue

                if url in existing_urls_in_db:
                    continue

                # Xử lý chi tiết từng bài viết
                try:
                    logger.info(
                        f"Đang xử lý chi tiết bài viết VNExpress - URL: {url}")

                    if not self._open_article_page(driver, url):
                        continue

                    published_at = self._get_published_time(driver, url)
                    if not published_at:
                        self._close_article_tab(driver)
                        continue

                    category_name = self._get_category(driver, url)
                    if not category_name or category_name not in valid_category_names_in_db:
                        logger.info(
                            f"⏭️ Bỏ qua category không hợp lệ hoặc không tìm thấy cho VNExpress: {category_name}")
                        self._close_article_tab(driver)
                        self.urls_processed.append(
                            {
                                "url": url,
                                "success": False,
                                "reason": f"Category VNExpress không hợp lệ/không tìm thấy: {category_name}"})
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
                    logger.error(
                        f"❌ Lỗi xử lý chi tiết bài viết VNExpress {url}: {detail_err}")
                    if len(driver.window_handles) > 1:
                        self._close_article_tab(driver)
                    continue
        except Exception as e:
            logger.error(f"❌ Lỗi trong quá trình crawl.")
        finally:
            # Đảm bảo luôn đóng driver khi hoàn thành
            driver.quit()
            logger.info(
                f"Kết thúc crawl VNExpress: thu thập được {len(results)} bài viết (target: {limit})")

        return results

    def _open_homepage(self, driver):
        driver.get(self.base_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, '//article'))
        )

    def _get_article_list(self, driver, limit):
        try:
            articles = driver.find_elements(By.XPATH, '//article')
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
            except BaseException:
                logger.warning("Phần tử article không còn tồn tại trong DOM")
                return

            # Sử dụng JavaScript để cuộn đến phần tử
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", article)
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Không thể sử dụng scrollIntoView.")
        except Exception as e:
            logger.warning(f"❌ Không thể cuộn đến bài viết.")

    def _get_basic_info(self, article):
        try:
            title_elem = article.find_element(
                By.XPATH, './/h3[contains(@class, "title-news")]')
            title = title_elem.text.strip()
            url_elem = title_elem.find_element(
                By.XPATH, './/a[contains(@href, "")]')
            url = url_elem.get_attribute("href")

            return title, url
        except Exception as e:
            return None

    def _is_video_url(self, url):
        if "video.vnexpress.net" in url:
            self.urls_processed.append({
                "url": url,
                "success": False,
                "reason": "URL video"
            })
            return True
        return False

    def _open_article_page(self, driver, url):
        try:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(url)

            WebDriverWait(
                driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'article.fck_detail')))

            driver.execute_script("window.scrollTo(0, 700);")
            time.sleep(2)

            # Đợi paragraph đầu tiên
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'p.Normal'))
            )

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

    def _get_published_time(self, driver, url):
        try:
            datetime_elem = driver.find_element(
                By.XPATH, '//span[contains(@class, "date")]')
            published_at = parse_datetime_manual(datetime_elem.text.strip())
            return published_at
        except Exception as e:
            logger.warning(f"❌ Không thể lấy thông tin datetime.")
            self.urls_processed.append({
                "url": url,
                "success": False,
                "reason": f"Không thể lấy thời gian xuất bản."
            })
            return None

    def _get_category(self, driver, url):
        try:
            category_elem = driver.find_element(
                By.XPATH,
                '//ul[contains(@class, "breadcrumb")]//a[contains(@data-medium, "Menu")]')
            category_name = category_elem.text.strip().upper()

            if category_name == 'SỨC KHỎE':
                category_name = 'SỨC KHOẺ'
            return category_name
        except Exception as e:
            logger.warning(
                f"❌ Không thể lấy thông tin category cho VNExpress {url}.")
            return None

    def _get_content(self, driver, url):
        try:
            paragraphs = driver.find_elements(
                By.XPATH, './/p[contains(@class, "Normal") or contains(@class, "description")]')
            content = "\n\n".join([p.text.strip()
                                  for p in paragraphs if p.text.strip()])

            if len(content) < 50:
                self.urls_processed.append({
                    "url": url,
                    "success": False,
                    "reason": "Nội dung quá ngắn hoặc trống"
                })
                return None

            return content
        except Exception as e:
            logger.warning(f"❌ Không thể lấy content.")
            self.urls_processed.append({
                "url": url,
                "success": False,
                "reason": f"Không thể lấy content."
            })
            return None

    def _get_image_url(self, driver, url):
        try:
            # Phương pháp 1: Tìm ảnh có đuôi .jpg, .jpeg, .png và alt
            img_elem = driver.find_element(
                By.XPATH, './/img[contains(@src, ".j") and contains(@alt, "")]')
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
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception as e:
            logger.error(f"❌ Lỗi khi đóng tab.")
            # Cố gắng phục hồi bằng cách quay lại tab đầu tiên
            if len(driver.window_handles) > 0:
                driver.switch_to.window(driver.window_handles[0])

    def _log_success(self, url, title):
        self.urls_processed.append({
            "url": url,
            "success": True,
            "title": title
        })
