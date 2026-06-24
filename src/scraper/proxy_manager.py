import json
import random
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta

class ProxyManager:
    def __init__(self, config_path: str = "config/settings.json"):
        self.config = self._load_config(config_path)
        self.proxy_file = Path("config/proxies.json")
        self.last_refresh = None
        self.proxies = []
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        default_config = {
            "proxy": {
                "enabled": False,
                "use_free_api": False,
                "refresh_interval_hours": 6,
                "proxy_list": [],
                "proxy_timeout": 10
            }
        }
        
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            print(f"配置加载失败: {e}")
        
        return default_config
    
    def _load_proxies_from_file(self) -> List[str]:
        if not self.proxy_file.exists():
            return []
        
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('proxies', [])
        except:
            return []
    
    def _save_proxies_to_file(self, proxies: List[str]):
        data = {
            'proxies': proxies,
            'updated_at': datetime.now().isoformat()
        }
        
        with open(self.proxy_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _fetch_xiaoxiang_proxies(self) -> List[str]:
        xx_config = self.config.get("xiaoxiang_proxy", {})
        if not xx_config.get("enabled", False) or not xx_config.get("api_url"):
            return []
        
        api_url = xx_config["api_url"]
        timeout = self.config["proxy"]["proxy_timeout"]
        
        try:
            response = requests.get(api_url, timeout=timeout)
            if response.status_code == 200:
                text = response.text.strip()
                proxies = []
                for line in text.split('\n'):
                    line = line.strip()
                    if line and ':' in line:
                        proxies.append(f"http://{line}")
                return proxies
        except Exception as e:
            print(f"小象代理获取失败: {e}")
        
        return []
    
    def _fetch_ja_proxies(self) -> List[str]:
        ja_config = self.config.get("ja_proxy", {})
        if not ja_config.get("enabled", False) or not ja_config.get("key"):
            return []
        
        key = ja_config["key"]
        num = ja_config.get("num", 5)
        timeout = self.config["proxy"]["proxy_timeout"]
        
        url = f"https://api.ja.cn/getip?key={key}&num={num}"
        
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                if data.get("status_code") == 0:
                    proxies = []
                    for item in data.get("data", []):
                        proxy_address = item.get("proxy_address")
                        if proxy_address:
                            proxies.append(f"http://{proxy_address}")
                    return proxies
        except Exception as e:
            print(f"极安代理获取失败: {e}")
        
        return []
    
    def _fetch_free_proxies(self) -> List[str]:
        if not self.config["proxy"]["use_free_api"]:
            return []
        
        apis = [
            "https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps&country=CN",
            "https://proxylist.geonode.com/api/proxy-list?limit=100&page=2&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps",
            "http://free-proxy.cz/en/proxylist/country/US/uptime/level1/https",
        ]
        
        proxies = []
        timeout = self.config["proxy"]["proxy_timeout"]
        
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=timeout)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('data', []):
                        ip = item.get('ip')
                        port = item.get('port')
                        if ip and port:
                            proxies.append(f"http://{ip}:{port}")
            except:
                continue
        
        return proxies
    
    def refresh_proxies(self):
        if not self.config["proxy"]["enabled"]:
            return
        
        refresh_interval = timedelta(hours=self.config["proxy"]["refresh_interval_hours"])
        if self.last_refresh and datetime.now() - self.last_refresh < refresh_interval:
            return
        
        file_proxies = self._load_proxies_from_file()
        api_proxies = self._fetch_free_proxies()
        ja_proxies = self._fetch_ja_proxies()
        xx_proxies = self._fetch_xiaoxiang_proxies()
        
        all_proxies = list(set(file_proxies + api_proxies + ja_proxies + xx_proxies))
        
        if all_proxies:
            self.proxies = all_proxies
            self._save_proxies_to_file(all_proxies)
            self.last_refresh = datetime.now()
            print(f"刷新代理列表: {len(self.proxies)} 个代理")
    
    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        if not self.config["proxy"]["enabled"]:
            return None
        
        self.refresh_proxies()
        
        if not self.proxies:
            proxy_list = self.config["proxy"]["proxy_list"]
            if proxy_list:
                proxy = random.choice(proxy_list)
                if isinstance(proxy, str):
                    return {"server": proxy}
                return proxy
            return None
        
        max_attempts = min(5, len(self.proxies))
        for _ in range(max_attempts):
            proxy = random.choice(self.proxies)
            if self.validate_proxy(proxy):
                if isinstance(proxy, str):
                    return {"server": proxy}
                return proxy
        
        return None
    
    def add_proxy(self, proxy: str):
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            self._save_proxies_to_file(self.proxies)
    
    def remove_proxy(self, proxy: str):
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            self._save_proxies_to_file(self.proxies)
    
    def validate_proxy(self, proxy: str) -> bool:
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {"http": proxy, "https": proxy}
            response = requests.get(test_url, proxies=proxies, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def remove_invalid_proxies(self):
        valid_proxies = []
        for proxy in self.proxies:
            if self.validate_proxy(proxy):
                valid_proxies.append(proxy)
        
        if len(valid_proxies) != len(self.proxies):
            self.proxies = valid_proxies
            self._save_proxies_to_file(self.proxies)
            print(f"移除无效代理，剩余 {len(valid_proxies)} 个")