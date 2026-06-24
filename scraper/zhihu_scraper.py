import time
import random
import json
import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import sync_playwright, Browser, Page
from pathlib import Path
from .anti_detection import AntiDetection
from .proxy_manager import ProxyManager

class ZhihuScraper:
    def __init__(self, config_path: str = "config/settings.json"):
        self.config = self._load_config(config_path)
        self.request_count = 0
        self.last_request_time = 0
        self.proxy_manager = ProxyManager(config_path)
        self.anti_detection = AntiDetection()
        
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "scraper.log")
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        default_config = {
            "scraper": {
                "request_delay": [2, 5],
                "max_scrolls": 15,
                "scroll_delay": [1, 3],
                "user_agents": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
                ],
                "headless": False,
                "viewport": {"width": 1920, "height": 1080},
                "page_load_timeout": 30000,
                "disable_images": False,
                "disable_css": False
            },
            "proxy": {
                "enabled": False,
                "proxy_list": [],
                "use_free_api": True,
                "rotate_interval": 5,
                "proxy_timeout": 10
            },
            "limits": {
                "max_comments": 500,
                "daily_limit": 1000,
                "cooldown_minutes": 30,
                "max_retries": 3,
                "retry_delay": [30, 60]
            },
            "detection": {
                "enable_stealth": True,
                "enable_verification_check": True,
                "verification_wait_time": 30,
                "humanize_behavior": True
            },
            "logging": {
                "level": "INFO",
                "file": "scraper.log",
                "max_size_mb": 10,
                "backup_count": 5
            }
        }
        
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            print(f"配置加载失败，使用默认配置: {e}")
        
        return default_config
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        return self.proxy_manager.get_random_proxy()
    
    def _random_delay(self, min_sec: float = None, max_sec: float = None):
        if min_sec is None:
            min_sec = self.config["scraper"]["request_delay"][0]
        if max_sec is None:
            max_sec = self.config["scraper"]["request_delay"][1]
        
        delay = random.uniform(min_sec, max_sec)
        
        elapsed = time.time() - self.last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
        
        self.last_request_time = time.time()
    
    def _check_rate_limit(self):
        daily_limit = self.config["limits"]["daily_limit"]
        if self.request_count >= daily_limit:
            cooldown = self.config["limits"]["cooldown_minutes"] * 60
            print(f"达到每日限制 ({daily_limit})，冷却 {self.config['limits']['cooldown_minutes']} 分钟")
            time.sleep(cooldown)
            self.request_count = 0
    
    def _get_random_user_agent(self) -> str:
        return random.choice(self.config["scraper"]["user_agents"])
    
    def _scroll_to_bottom(self, page: Page):
        max_scrolls = self.config["scraper"]["max_scrolls"]
        scroll_delay = self.config["scraper"]["scroll_delay"]
        
        for i in range(max_scrolls):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self._random_delay(scroll_delay[0], scroll_delay[1])
            
            if i > 0 and page.evaluate("document.body.scrollHeight") == page.evaluate("window.scrollY + window.innerHeight"):
                break
    
    def _parse_url_type(self, url: str) -> Dict[str, Any]:
        import re
        
        if 'zhuanlan.zhihu.com/p/' in url:
            return {'type': 'article', 'id': re.search(r'/p/(\d+)', url).group(1)}
        
        answer_match = re.search(r'zhihu\.com/question/(\d+)/answer/(\d+)', url)
        if answer_match:
            return {'type': 'answer', 'question_id': answer_match.group(1), 'answer_id': answer_match.group(2)}
        
        question_match = re.search(r'zhihu\.com/question/(\d+)', url)
        if question_match:
            return {'type': 'question', 'question_id': question_match.group(1)}
        
        return {'type': 'unknown', 'raw_url': url}
    
    def _extract_comments_from_article(self, page: Page) -> List[Dict[str, Any]]:
        comments = []
        comment_elements = page.query_selector_all('.CommentItem')
        for elem in comment_elements:
            try:
                comment = self._parse_comment_element(elem)
                if comment:
                    comments.append(comment)
            except Exception as e:
                continue
        return comments
    
    def _extract_comments_from_answer(self, page: Page) -> List[Dict[str, Any]]:
        comments = []
        
        answer_items = page.query_selector_all('.AnswerItem')
        if not answer_items:
            answer_items = page.query_selector_all('[data-zop="answer"]')
        
        target_answer = None
        for item in answer_items:
            is_expanded = item.query_selector('.ContentItem-expandButton')
            if not is_expanded or item.evaluate("el => el.offsetHeight > 200"):
                target_answer = item
                break
        
        if not target_answer and answer_items:
            target_answer = answer_items[0]
        
        if target_answer:
            # 点击评论按钮展开评论
            comment_btn = target_answer.query_selector('button:has-text("条评论")')
            if comment_btn:
                try:
                    comment_btn.click()
                    page.wait_for_timeout(3000)
                except:
                    pass
            
            comment_containers = target_answer.query_selector_all('.CommentItem')
            for elem in comment_containers:
                try:
                    comment = self._parse_comment_element(elem)
                    if comment:
                        comments.append(comment)
                except Exception as e:
                    continue
        
        if not comments:
            comments = self._extract_comments_from_article(page)
        
        return comments
    
    def _extract_comments_from_question(self, page: Page) -> List[Dict[str, Any]]:
        return self._extract_comments_from_answer(page)
    
    def _parse_comment_element(self, elem) -> Dict[str, Any]:
        author = elem.query_selector('.AuthorInfo-name, .CommentItem-meta .AuthorInfo-name')
        content = elem.query_selector('.RichText, .CommentItem-content .RichText')
        likes_elem = elem.query_selector('.Button--plain, .CommentItem-actions .Button--plain')
        
        likes_text = '0'
        if likes_elem:
            likes_text = likes_elem.inner_text().strip()
            likes_text = likes_text.replace('赞同', '').replace('条回复', '').strip() or '0'
        
        return {
            'author': author.inner_text().strip() if author else '匿名用户',
            'content': content.inner_text().strip() if content else '',
            'likes': likes_text,
            'timestamp': elem.get_attribute('data-creation-time') or ''
        }
    
    def _extract_comments(self, page: Page, url: str = '') -> List[Dict[str, Any]]:
        url_info = self._parse_url_type(url)
        self.logger.info(f"URL类型: {url_info['type']}")
        
        if url_info['type'] == 'article':
            return self._extract_comments_from_article(page)
        elif url_info['type'] == 'answer':
            return self._extract_comments_from_answer(page)
        elif url_info['type'] == 'question':
            return self._extract_comments_from_question(page)
        else:
            return self._extract_comments_from_article(page)
    
    def _retry_scrape(self, url: str, max_comments: int) -> List[Dict[str, Any]]:
        max_retries = self.config["limits"]["max_retries"]
        retry_delay = self.config["limits"]["retry_delay"]
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"尝试 {attempt + 1}/{max_retries}")
                comments = self.scrape(url, max_comments)
                if comments:
                    return comments
                else:
                    self.logger.warning(f"第 {attempt + 1} 次尝试未获取到评论")
            except Exception as e:
                self.logger.error(f"第 {attempt + 1} 次尝试失败: {e}")
            
            if attempt < max_retries - 1:
                wait_time = random.uniform(retry_delay[0], retry_delay[1])
                self.logger.info(f"等待 {wait_time:.1f} 秒后重试...")
                time.sleep(wait_time)
        
        self.logger.error("所有重试尝试均失败")
        return []
    
    def scrape(self, url: str, max_comments: int = None) -> List[Dict[str, Any]]:
        if max_comments is None:
            max_comments = self.config["limits"]["max_comments"]
        
        all_comments = []
        self._check_rate_limit()
        self.logger.info(f"开始抓取: {url}")
        
        with sync_playwright() as p:
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-web-security",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu"
            ]
            
            proxy = self._get_proxy()
            if proxy:
                self.logger.info(f"使用代理: {proxy.get('server', '未知')}")
            
            browser = p.chromium.launch(
                headless=self.config["scraper"]["headless"],
                args=browser_args,
                proxy=proxy
            )
            
            context = browser.new_context(
                user_agent=self._get_random_user_agent(),
                viewport=self.config["scraper"]["viewport"],
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                java_script_enabled=True,
                bypass_csp=True,
                ignore_https_errors=True
            )
            
            if self.config["scraper"]["disable_images"]:
                context.route("**/*.{png,jpg,jpeg,gif,svg,webp}", lambda route: route.abort())
            
            if self.config["scraper"]["disable_css"]:
                context.route("**/*.css", lambda route: route.abort())
            
            self.anti_detection._stealth_inject(context.pages[0] if context.pages else context.new_page())
            
            page = context.new_page()
            
            try:
                self.logger.info("加载页面...")
                timeout = self.config["scraper"]["page_load_timeout"]
                page.goto(url, wait_until='networkidle', timeout=timeout)
                self._random_delay()
                
                if self.config["detection"]["enable_stealth"]:
                    self.anti_detection._stealth_inject(page)
                
                if self.config["detection"]["enable_verification_check"]:
                    if self.anti_detection._check_detection(page):
                        self.logger.warning("检测到反爬虫机制，尝试绕过...")
                        time.sleep(random.uniform(5, 10))
                    
                    if self.anti_detection._handle_verification(page):
                        self.logger.info("验证码处理完成，继续抓取...")
                
                if self.config["detection"]["humanize_behavior"]:
                    self.logger.info("开始模拟用户滚动...")
                    self.anti_detection._humanize_scroll(page)
                else:
                    self._scroll_to_bottom(page)
                
                self.logger.info("提取评论...")
                all_comments = self._extract_comments(page, url)
                all_comments = all_comments[:max_comments]
                
                self.request_count += 1
                self.logger.info(f"成功抓取 {len(all_comments)} 条评论")
                
            except Exception as e:
                self.logger.error(f"抓取出错: {e}")
                if "captcha" in str(e).lower() or "verify" in str(e).lower():
                    self.logger.warning("可能触发了验证码，建议稍后重试")
            finally:
                browser.close()
                self.logger.info("浏览器已关闭")
        
        return all_comments