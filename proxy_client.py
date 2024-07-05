import requests
import random

from utils.utils import *
from dataclasses import dataclass


@dataclass
class ProxyData:
    protocol: str
    proxy: str

class ProxyClient:
    def __init__(
        self, 
        proxies: list[ProxyData],
        *, 
        retries: int, 
        timeout: int = 60
    ) -> None:
        self.proxies = proxies
        self.retries = retries
        self.timeout = timeout

        self.retry = self.retry_p if self.proxies else self.retry_r

    @staticmethod
    def proxy_request(method: str, url: str, proxy: ProxyData, **kwargs) -> requests.Response:
        return requests.request(
            method,
            url,
            proxies={ "http": f"{proxy.protocol}://{proxy.proxy}", "https": f"{proxy.protocol}://{proxy.proxy}" },
            **kwargs
        )
    
    @debug("{method} {url} - все попытки получить успешный ответ от сервера исчерпаны")
    def retry_r(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response | None:
        headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0" }

        for _ in range(self.retries):
            try:
                req = requests.request(method, url, headers=headers, **kwargs)
                logger.log(LogType.INFO, f"{method} {url} - {req.status_code}")
                    
                if req.status_code not in [200, 404]: req.raise_for_status()
                return req
            
            except requests.RequestException:
                logger.log(LogType.INFO, f"Не удалось выполнить запрос {method} {url}")
                continue

        raise requests.RequestException(f"All {self.retries} retries exhausted. Request failed")

    @debug("{method} {url} - все попытки получить успешный ответ от сервера исчерпаны")
    def retry_p(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response | None:
        headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0" }

        for _ in range(self.retries):
            all_proxies = list(self.proxies)
            
            while all_proxies:
                random.shuffle(all_proxies)
                proxy = all_proxies.pop()

                try:
                    req = self.proxy_request(method, url, proxy, headers=headers, timeout=self.timeout, **kwargs)
                    logger.log(LogType.INFO, f"{method} {url} - {req.status_code}. Proxy: {proxy.proxy}")
                    
                    if req.status_code not in [200, 404]: req.raise_for_status()
                    return req
                
                except requests.RequestException:
                    logger.log(LogType.INFO, f"Не удалось выполнить запрос {method} {url}, используя прокси {proxy.proxy}")
                    continue
        
        raise requests.RequestException(f"All {self.retries} retries exhausted. Request failed")


            
def map_proxies(protocol: str, proxies: list[str]) -> list[ProxyData]:
    if any(proxies):
        return [
            ProxyData(protocol, i) 
            for i in proxies
        ]

    return []
