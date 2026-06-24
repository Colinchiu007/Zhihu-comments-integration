import random
import time
from typing import List, Dict, Any
from playwright.sync_api import Page

class AntiDetection:
    def __init__(self):
        self.mouse_movements = []
        
    def _stealth_inject(self, page: Page):
        stealth_js = """
        // 隐藏webdriver属性
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // 修改chrome属性
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // 修改permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // 修改plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // 修改languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en']
        });
        """
        page.add_init_script(stealth_js)
    
    def _simulate_mouse_movement(self, page: Page, target_x: int, target_y: int):
        current_x = random.randint(100, 500)
        current_y = random.randint(100, 300)
        
        steps = random.randint(5, 15)
        for i in range(steps):
            progress = (i + 1) / steps
            x = int(current_x + (target_x - current_x) * progress + random.randint(-5, 5))
            y = int(current_y + (target_y - current_y) * progress + random.randint(-5, 5))
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.01, 0.05))
        
        page.mouse.move(target_x, target_y)
    
    def _simulate_scroll(self, page: Page, scroll_amount: int = None):
        if scroll_amount is None:
            scroll_amount = random.randint(300, 800)
        
        page.mouse.wheel(0, scroll_amount)
        time.sleep(random.uniform(0.1, 0.3))
    
    def _simulate_click(self, page: Page, selector: str):
        element = page.query_selector(selector)
        if element:
            box = element.bounding_box()
            if box:
                x = box['x'] + random.randint(5, box['width'] - 5)
                y = box['y'] + random.randint(5, box['height'] - 5)
                
                self._simulate_mouse_movement(page, x, y)
                time.sleep(random.uniform(0.1, 0.3))
                page.mouse.click(x, y)
    
    def _random_pause(self, min_sec: float = 0.5, max_sec: float = 2.0):
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _humanize_scroll(self, page: Page, max_scrolls: int = 10):
        for i in range(max_scrolls):
            scroll_amount = random.randint(200, 600)
            self._simulate_scroll(page, scroll_amount)
            
            pause_time = random.uniform(1.0, 3.0)
            if random.random() < 0.3:
                pause_time += random.uniform(2.0, 5.0)
            
            time.sleep(pause_time)
            
            if random.random() < 0.2:
                try:
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(random.uniform(0.5, 1.0))
                except:
                    pass
    
    def _check_detection(self, page: Page) -> bool:
        detection_scripts = [
            "navigator.webdriver",
            "window.chrome && window.chrome.runtime",
            "navigator.plugins.length > 0",
            "document.querySelectorAll('[id*=\\'captcha\\']').length > 0",
            "document.querySelectorAll('[class*=\\'verify\\']').length > 0"
        ]
        
        for script in detection_scripts:
            try:
                result = page.evaluate(script)
                if result:
                    return True
            except:
                continue
        
        return False
    
    def _handle_verification(self, page: Page):
        verification_indicators = [
            '.Captcha-container',
            '.VerificationContainer',
            '[data-za-detail-view-name="Captcha"]'
        ]
        
        for indicator in verification_indicators:
            if page.query_selector(indicator):
                print("检测到验证码，等待人工处理...")
                time.sleep(30)
                return True
        
        return False