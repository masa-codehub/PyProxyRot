# proxy_connection_test.py (JSON抽出ロジック追加版)

import sys
import os
import json
import re # 正規表現を使う場合 (今回はfindで)
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import WebDriverException, NoSuchElementException

# ... (import, 設定部分は変更なし) ...
try:
    from src.domain.proxy_info import ProxyInfo
    from src.adapters.edge_option_factory import EdgeOptionFactory
except ImportError as e:
    print(f"ERROR: Could not import necessary modules from src: {e}")
    sys.exit(1)

SELENIUM_URL = os.getenv('SELENIUM_HUB', 'http://selenium:4444/wd/hub')
PROXY_SERVICE_NAME = "proxy-server"
PROXY_PORT = 8080
TARGET_URL = "https://api.ipify.org?format=json"

print(f"--- Proxy Connection Test ---")
# ... (print 設定情報) ...
print("-" * 30)

driver = None
try:
    proxy_info = ProxyInfo(host=PROXY_SERVICE_NAME, port=PROXY_PORT)
    factory = EdgeOptionFactory()
    proxy_options = factory.create_options(proxy_info)
    print("Generated EdgeOptions with proxy settings.")

    print(f"Attempting to connect to {SELENIUM_URL} with proxy options...")
    driver = webdriver.Remote(
        command_executor=SELENIUM_URL,
        options=proxy_options
    )
    print("Successfully connected via webdriver.Remote!")

    print(f"Navigating to {TARGET_URL}...")
    driver.get(TARGET_URL)
    screenshot_path = "proxy_error_page.png"
    try:
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
    except Exception as screenshot_error:
        print(f"Warning: Could not save screenshot: {screenshot_error}")
    print("Page loaded.")

    # 5. レスポンスからIPアドレス情報を取得
    detected_ip = "Could not determine IP from page content."
    body_text = ""
    json_string = "" # 抽出後のJSON文字列用
    try:
        body_text = driver.find_element("tag name", "body").text.strip()
        print(f"DEBUG: Raw text from <body> tag:\n---\n{body_text}\n---")

        if "api.ipify.org" in TARGET_URL or "httpbin.org/ip" in TARGET_URL:
            # ★★★ JSON部分を抽出する処理を追加 ★★★
            # 最初の '{' を探す
            json_start_index = body_text.find('{')
            # 最後の '}' を探す
            json_end_index = body_text.rfind('}')

            if json_start_index != -1 and json_end_index != -1 and json_start_index < json_end_index:
                # '{' から '}' までを抽出
                json_string = body_text[json_start_index : json_end_index + 1]
                print(f"DEBUG: Extracted potential JSON string:\n---\n{json_string}\n---")

                # 抽出した文字列でJSONパースを試みる
                try:
                    data = json.loads(json_string)
                    detected_ip = data.get("origin") or data.get("ip", "Not found in JSON")
                    print("DEBUG: JSON parsed successfully from extracted string.")
                except json.JSONDecodeError as e:
                    print(f"ERROR: Could not parse extracted JSON: {e}")
                    print(f"DEBUG: Extracted string that failed to parse:\n---\n{json_string}\n---")
            else:
                # 有効なJSON構造が見つからなかった場合
                print("ERROR: Could not find valid JSON structure '{...}' in the body text.")
                print(f"DEBUG: Original body text was:\n---\n{body_text}\n---")
        else:
             print("DEBUG: Target URL is not JSON type, using raw body text.")
             detected_ip = body_text

    except Exception as e: # NoSuchElementExceptionなども含む
        print(f"ERROR: Could not extract IP from page: {e}")
        if body_text: # body_textが取得できていれば表示
             print(f"DEBUG: Content at time of error:\n---\n{body_text}\n---")


    print(f"\nDetected IP Address / Origin: {detected_ip}")

    # --- 検証 ---
    print("\n--- Verification ---")
    print(f"Does '{detected_ip}' look like the IP address of your proxy container ('{PROXY_SERVICE_NAME}') or its egress IP?")
    print(f"To check container IP: 'docker inspect {PROXY_SERVICE_NAME} | grep IPAddress' (adjust container name if needed)")
    print("If using mitmproxy, check the web UI (http://localhost:8081) for captured requests.")

    # ★ アサーションを追加して自動チェック（任意） ★
    # 期待するIPアドレスが事前にわかっている場合や、"Could not determine"でないことを確認
    assert detected_ip != "Could not determine IP from page content.", "Failed to extract a valid IP address!"
    # assert "160.86.23.140" in detected_ip # 例：もしこのIPが期待値なら

    print("\nProxy connection test finished.")

except WebDriverException as e:
    print(f"\nERROR: WebDriverException occurred: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
    sys.exit(1)
finally:
    if driver:
        print("Closing the browser...")
        driver.quit()
        print("Browser closed.")