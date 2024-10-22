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
from PIL import Image  # Pillow 라이브러리 추가
import time
from urllib.parse import urlparse, urlunparse
import shutil

# 스크린샷 저장 경로 설정
screenshot_dir = 'screenshots'
os.remove("processed_data.xlsx") if os.path.exists('processed_data.xlsx') else None
shutil.rmtree(screenshot_dir) if os.path.exists(screenshot_dir) else None
os.makedirs(screenshot_dir, exist_ok=True)

# Selenium WebDriver 설정
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

# 스레드풀의 최대 스레드 수 설정 (최대 병렬 처리 수)
MAX_THREADS = 10

# URL 해시값 생성 함수
def generate_hash(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()

# 주 도메인 추출 함수
def extract_main_domain(url):
    """
    주어진 URL에서 서브도메인을 제외하고 주 도메인만 반환합니다.
    예: 'www.example.com' -> 'example.com', 'm.blog.example.com' -> 'example.com'
    """
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')
    if len(domain_parts) > 2:  # 서브도메인이 있는 경우
        main_domain = '.'.join(domain_parts[-2:])  # 뒤에서 두 개의 요소를 결합 (주 도메인)
    else:
        main_domain = parsed_url.netloc  # 서브도메인이 없는 경우 그대로 사용
    
    return main_domain

# URL 표준화 함수
def normalize_url_without_subdomain(url):
    """
    서브도메인을 제외하고 주 도메인, 경로, 쿼리를 포함한 URL을 표준화하여 반환합니다.
    """
    parsed_url = urlparse(url)
    main_domain = extract_main_domain(url)
    
    # 표준화된 URL 생성 (주 도메인 + 경로 + 쿼리만 포함)
    normalized_url = urlunparse((
        '',  # 프로토콜을 무시
        main_domain,  # 추출한 주 도메인 사용
        parsed_url.path.lower(),  # 경로를 소문자로 변환
        '',  # 파라미터 무시
        parsed_url.query,  # 쿼리 유지
        ''  # 프래그먼트 무시
    ))
    
    return normalized_url

# 두 URL을 서브도메인 무시하고 비교
def compare_without_subdomain(url1, url2):
    """
    두 URL에서 서브도메인을 제외한 주 도메인과 경로, 쿼리를 비교하여 동일한지 확인합니다.
    """
    normalized_url1 = normalize_url_without_subdomain(url1)
    normalized_url2 = normalize_url_without_subdomain(url2)
    
    return normalized_url1 == normalized_url2

# PNG 스크린샷을 JPG로 변환하는 함수
def convert_png_to_jpg(png_path, jpg_path):
    with Image.open(png_path) as img:
        rgb_img = img.convert('RGB')  # PNG는 투명도(alpha 채널)이 있기 때문에 RGB로 변환
        rgb_img.save(jpg_path, "JPEG", quality=85)  # JPG로 저장, quality 파라미터로 압축률 조절

# 페이지 완전 로딩 대기 함수 (document.readyState 체크 후 추가 대기)
def wait_for_page_load(driver, timeout=20, check_interval=0.5, additional_wait=3):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
    
    # 추가로 DOM 변화 감지 후 일정 시간 대기
    last_html = driver.page_source
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(check_interval)
        current_html = driver.page_source
        if current_html == last_html:
            break
        last_html = current_html
    
    # 추가로 일정 시간 대기 (동적 로딩이 끝났을 가능성에 대비)
    time.sleep(additional_wait)

# 링크를 처리하는 함수
def process_link(row):
    driver = webdriver.Chrome(options=chrome_options)
    result = row.copy()  # 원본 데이터를 변경하지 않기 위해 복사
    url = row['url']


    try:
        # 리다이렉트 허용하며 URL 요청
        response = requests.get(url, timeout=20, allow_redirects=True)
        
        # HTTP 상태 코드 검증 (4xx, 5xx 에러 처리)
        if response.status_code >= 400:
            result['status'] = f"에러 코드 {response.status_code} - 페이지 없음"
        else:
            # 리다이렉트 여부 확인 (최종 URL과 원래 URL 비교)
            if not compare_without_subdomain(url, response.url):
                result['status'] = f"리다이렉트 감지 (최종 URL: {response.url})"
            else:
                result['status'] = "정상"
            
            # 페이지 내용에서 오류 감지 (404 페이지 메시지 검출)
            # if any(keyword in response.text.lower() for keyword in ["404", "not found", "페이지를 찾을 수 없습니다", "에러"]):
            #     result['status'] = "에러 페이지 감지 (내용)"
        result['last_checked'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 브라우저 창 크기 설정
        driver.set_window_size(1920, 1080)  # 원하는 해상도 설정

        # 페이지 로딩을 기다림
        driver.get(url)
        wait_for_page_load(driver)

        # URL의 해시값 생성
        url_hash = generate_hash(url)
        
        # 스크린샷 저장 경로 생성 (임시로 PNG로 저장)
        screenshot_png_path = os.path.join(screenshot_dir, f"{row['id']}_{url_hash}.png")
        screenshot_jpg_path = os.path.join(screenshot_dir, f"{row['id']}_{url_hash}.jpg")
        
        # 스크린샷을 PNG로 저장
        driver.save_screenshot(screenshot_png_path)

        # PNG 스크린샷을 JPG로 변환
        convert_png_to_jpg(screenshot_png_path, screenshot_jpg_path)

        # PNG 파일 삭제 (필요 없다면)
        os.remove(screenshot_png_path)

        result['screenshot'] = screenshot_jpg_path
    except requests.exceptions.RequestException as e:
        result['status'] = f'에러 ({str(e)})'
        result['screenshot'] = None
    except Exception as e:
        result['status'] = f'에러 (스크린샷 오류: {str(e)})'
        result['screenshot'] = None
    finally:
        driver.quit()

    return result

# 메인 처리 함수 - 병렬로 링크 처리
def check_links(input_file="test_data.xlsx", output_file="processed_data.xlsx"):
    # 엑셀 파일 읽기
    df = pd.read_excel(input_file)
    # 'id'가 'J강0923'로 시작하는 행만 선택
    # df = df[df['id'].astype(str).str.startswith('L자0923005')]
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
    check_links(input_file="test_data_20241014.xlsx", output_file="processed_data.xlsx")



## To do List
# - Full HTML 에서 link 만 뽑아내기.
# - 리다이렉트시 문제 확인( 최상위 도메인으로 보는 방식(네이버), 유투브는 200으로 오는데 원숭이 등장..)