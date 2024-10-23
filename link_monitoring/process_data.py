import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from PIL import Image
import time
from urllib.parse import urlparse, urlunparse
import shutil
import logging

# 로깅 설정
logging.basicConfig(filename='process.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 환경 설정 상수
screenshot_dir = 'screenshots'
MAX_THREADS = 10
REQUEST_TIMEOUT = 20  # 요청 타임아웃 (초)
WAIT_FOR_PAGE_TIMEOUT = 20  # 페이지 로드 대기 타임아웃 (초)

# 초기 디렉토리 및 파일 설정
def setup_directories():
    if os.path.exists("processed_data.xlsx"):
        os.remove("processed_data.xlsx")
    if os.path.exists(screenshot_dir):
        shutil.rmtree(screenshot_dir)
    os.makedirs(screenshot_dir, exist_ok=True)

# Selenium WebDriver 설정
def configure_webdriver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return chrome_options

chrome_options = configure_webdriver()

# URL 해시값 생성 함수
def generate_hash(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()

# 주 도메인 추출 함수
def extract_main_domain(url):
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')
    if len(domain_parts) > 2:
        main_domain = '.'.join(domain_parts[-2:])
    else:
        main_domain = parsed_url.netloc
    return main_domain

# URL 표준화 함수
def normalize_url_without_subdomain(url):
    parsed_url = urlparse(url)
    main_domain = extract_main_domain(url)

    # 경로를 소문자로 변환하고, 마지막 '/'가 있다면 제거
    normalized_path = parsed_url.path.lower().rstrip('/')

    # 표준화된 URL 생성 (주 도메인 + 경로 + 쿼리만 포함)
    normalized_url = urlunparse((
        '', main_domain, normalized_path, '', parsed_url.query, ''
    ))
    
    return normalized_url


# 두 URL을 서브도메인 무시하고 비교
def compare_without_subdomain(url1, url2):
    normalized_url1 = normalize_url_without_subdomain(url1)
    normalized_url2 = normalize_url_without_subdomain(url2)
    return normalized_url1 == normalized_url2

# PNG 스크린샷을 JPG로 변환하는 함수
def convert_png_to_jpg(png_path, jpg_path):
    try:
        with Image.open(png_path) as img:
            rgb_img = img.convert('RGB')
            rgb_img.save(jpg_path, "JPEG", quality=85)
        os.remove(png_path)
    except Exception as e:
        logging.error(f"PNG to JPG 변환 실패: {str(e)}")

# 페이지 완전 로딩 대기 함수
def wait_for_page_load(driver, timeout=WAIT_FOR_PAGE_TIMEOUT, check_interval=0.5, additional_wait=3):
    try:
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
        last_html = driver.page_source
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(check_interval)
            current_html = driver.page_source
            if current_html == last_html:
                break
            last_html = current_html
        time.sleep(additional_wait)
    except Exception as e:
        logging.error(f"페이지 로딩 대기 실패: {str(e)}")

# 링크를 처리하는 함수
def process_link(row):
    driver = webdriver.Chrome(options=chrome_options)
    result = row.copy()
    url = row['url']
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if response.status_code >= 400:
            result['status'] = f"에러 코드 {response.status_code} - 페이지 없음"
        else:
            if not compare_without_subdomain(url, response.url):
                result['status'] = f"리다이렉트 감지 (최종 URL: {response.url})"
            else:
                result['status'] = "정상"
            
            # 유튜브 URL인지 확인
            if "youtube.com" in urlparse(url).netloc:
                # HTML 콘텐츠에서 "비공개" 키워드 검색
                if "비공개" in response.text.lower() or "private video" in response.text.lower():
                    result['status'] = "비공개 동영상 감지"
                
        result['last_checked'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        driver.set_window_size(1920, 1080)
        driver.get(url)
        wait_for_page_load(driver)

        url_hash = generate_hash(url)
        screenshot_png_path = os.path.join(screenshot_dir, f"{row['id']}_{url_hash}.png")
        screenshot_jpg_path = os.path.join(screenshot_dir, f"{row['id']}_{url_hash}.jpg")

        driver.save_screenshot(screenshot_png_path)
        convert_png_to_jpg(screenshot_png_path, screenshot_jpg_path)

        result['screenshot'] = screenshot_jpg_path
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP 요청 오류: {str(e)}")
        result['status'] = f'에러 (HTTP 오류: {str(e)})'
        result['screenshot'] = None
    except Exception as e:
        logging.error(f"처리 중 오류 발생: {str(e)}")
        result['status'] = f'에러 (스크린샷 오류: {str(e)})'
        result['screenshot'] = None
    finally:
        driver.quit()

    return result

# 메인 처리 함수 - 병렬로 링크 처리
def check_links(input_file="test_data.xlsx"):
    try:
        # 현재 날짜와 시간을 가져와서 파일 이름 생성
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"processed_data_{current_time}.xlsx"
        
        df = pd.read_excel(input_file)
        # df = df[df['id'].astype(str).str.startswith('F카1014003')]
        processed_data = []
        setup_directories()

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(process_link, row) for _, row in df.iterrows()]
            for future in as_completed(futures):
                processed_data.append(future.result())

        processed_df = pd.DataFrame(processed_data)
        processed_df.to_excel(output_file, index=False)
        logging.info(f"처리된 데이터가 {output_file} 파일로 저장되었습니다.")
    except Exception as e:
        logging.error(f"파일 처리 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    check_links(input_file="test_data_20241014.xlsx")


## To do List
# - Full HTML 에서 link 만 뽑아내기.