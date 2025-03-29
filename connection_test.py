# connection_test.py

import sys
import os
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

# Selenium Hub のURLを環境変数 SELENIUM_HUB から取得
# docker-compose.yml で設定したデフォルト値が使われるはず
SELENIUM_URL = os.getenv('SELENIUM_HUB', 'http://selenium:4444/wd/hub')

print(f"Attempting to connect to Selenium Hub at: {SELENIUM_URL}")

# まずはプロキシなしのシンプルなオプションで試す
options = EdgeOptions()
# 必要ならヘッドレスなどのオプションを追加
# options.add_argument("--headless")
# options.add_argument("--disable-gpu")

try:
    # webdriver.Remote を使用して Selenium Hub (コンテナ) に接続
    driver = webdriver.Remote(
        command_executor=SELENIUM_URL,
        options=options
    )
    print("Successfully connected to Selenium Hub!")

    # 簡単な操作を実行して動作確認
    target_url = "https://example.com"
    print(f"Navigating to {target_url}...")
    driver.get(target_url)
    page_title = driver.title
    print(f"Page title: {page_title}")
    assert "Example Domain" in page_title, f"Unexpected page title: {page_title}"

    print("Closing the browser...")
    driver.quit() # WebDriver セッションを終了
    print("Browser closed successfully.")
    print("\nConnection test PASSED!")
    sys.exit(0) # 成功コードで終了

except Exception as e:
    print(f"\nAn error occurred during the connection test: {e}")
    print("\n--- Potential Issues ---")
    print("- Are the 'py-proxy-rotator' and 'selenium' containers running? (Check 'docker-compose ps')")
    print(f"- Is the SELENIUM_URL '{SELENIUM_URL}' correct? (Matches service name and port)")
    print("- Are both containers on the same Docker network ('selenium_net')?")
    print("- Is the Selenium service ('selenium') correctly configured and listening on port 4444?")
    print("- Check the logs of the 'selenium' container ('docker-compose logs selenium') for errors.")
    print("\nConnection test FAILED.")
    sys.exit(1) # 失敗コードで終了