import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 스크린샷 저장 경로 설정
screenshot_dir = 'screenshots'
os.makedirs(screenshot_dir, exist_ok=True)

# Selenium WebDriver 설정
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

# 스레드풀의 최대 스레드 수 설정 (최대 병렬 처리 수)
MAX_THREADS = 10

# 링크를 처리하는 함수
def process_link(row):
    driver = webdriver.Chrome(options=chrome_options)
    result = row.copy()  # 원본 데이터를 변경하지 않기 위해 복사
    url = row['url']
    result['last_checked'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # URL에 대한 HTTP 요청 처리
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result['status'] = '정상'
        else:
            result['status'] = f'에러 ({response.status_code})'
        
        # 스크린샷 저장
        driver.get(url)
        screenshot_path = os.path.join(screenshot_dir, f"{row['id']}.png")
        driver.save_screenshot(screenshot_path)
        result['screenshot'] = screenshot_path
    except requests.exceptions.RequestException as e:
        result['status'] = f'에러 ({str(e)})'
        result['screenshot'] = None
    finally:
        driver.quit()
    
    return result

# 메인 처리 함수 - 병렬로 링크 처리
def check_links(input_file="test_data.xlsx", output_file="processed_data.xlsx"):
    # 엑셀 파일 읽기
    df = pd.read_excel(input_file)

    # 결과 저장을 위한 리스트
    processed_data = []

    # ThreadPoolExecutor를 사용하여 병렬 처리
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # 각 행(row)에 대해 병렬 작업 제출
        futures = [executor.submit(process_link, row) for _, row in df.iterrows()]
        
        # 완료된 작업에서 결과 수집
        for future in as_completed(futures):
            processed_data.append(future.result())

    # 처리된 데이터를 DataFrame으로 변환
    processed_df = pd.DataFrame(processed_data)

    # 결과를 새로운 엑셀 파일로 저장
    processed_df.to_excel(output_file, index=False)
    print(f"처리된 데이터가 {output_file} 파일로 저장되었습니다.")

# 실행 시 처리 로직 수행
if __name__ == "__main__":
    check_links(input_file="test_data.xlsx", output_file="processed_data.xlsx")
