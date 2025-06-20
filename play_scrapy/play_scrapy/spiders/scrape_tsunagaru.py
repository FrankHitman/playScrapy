from playwright.sync_api import sync_playwright
import time

def scrape_tsunagaru(url: str):
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 访问网页
        page.goto(url, wait_until="domcontentloaded")
        
        # 等待页面加载完成，增加超时时间到60秒
        try:
            page.wait_for_load_state('networkidle', timeout=60000)
        except Exception as e:
            print(f"等待网络空闲超时: {e}")
        
        # 额外等待以确保内容加载完成
        time.sleep(5)
        
        # 获取页面内容
        content = page.content()
        
        # 关闭浏览器
        browser.close()
        
        return content

if __name__ == "__main__":
    url = "https://tsunagarujp.mext.go.jp/level03/c01/"
    content = scrape_tsunagaru(url)
    with open("tsunagaru.html", "w", encoding="utf-8") as f:
        f.write(content)