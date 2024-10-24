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
from PIL import Image, ImageDraw, ImageFont
import time
from urllib.parse import urlparse, urlunparse
import shutil
import time
import logging


# 로깅 설정
logging.basicConfig(filename='process.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 환경 설정 상수
screenshot_dir = 'screenshots'
MAX_THREADS = 16
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
def wait_for_page_load(driver, timeout=WAIT_FOR_PAGE_TIMEOUT, check_interval=0.5, stability_threshold=15):
    try:
        # document.readyState가 'complete'가 될 때까지 대기
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        stable_count = 0
        last_dom_length = None
        start_time = time.time()

        while time.time() - start_time < timeout:
            time.sleep(check_interval)
            # 현재 DOM 요소의 개수를 가져옴
            current_dom_length = driver.execute_script("return document.getElementsByTagName('*').length")
            
            if last_dom_length is not None and current_dom_length == last_dom_length:
                stable_count += 1
                # print(stable_count)
                if stable_count >= stability_threshold:
                    # 안정화 임계값에 도달하면 루프 종료
                    break
            else:
                stable_count = 0  # 안정화 카운트 리셋

            last_dom_length = current_dom_length
        else:
            logging.warning("페이지가 지정된 시간 내에 안정화되지 않았습니다.")
    except Exception as e:
        logging.error(f"페이지 로딩 대기 실패: {str(e)}")

# 에러 처리 함수 정의
def handle_error(result, error_type, exception, error_message, default_image_path):
    logging.error(f"{error_type} 오류: {str(exception)}")
    result['status'] = "에러"
    result['log'] = f'에러 ({error_message}: {str(exception)})'
    
    # 대체 이미지 저장
    result['screenshot'] = save_default_image(default_image_path, result['id'])

# 대체 이미지 생성 및 저장 함수
def save_default_image(default_image_path, unique_id):
    try:
        # 대체 이미지 생성
        image = Image.new('RGB', (1920, 1080), color=(255, 255, 255))  # 흰색 배경의 기본 이미지

        # 이미지에 텍스트 추가를 위한 ImageDraw 객체 생성
        draw = ImageDraw.Draw(image)
        error_text = "ERROR"
        error_message = f"ID: {unique_id}"

        # 폰트 설정 (시스템 기본 폰트로 설정, 크기는 150)
        try:
            font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"  # Linux 시스템에서의 예시 경로
            font = ImageFont.truetype(font_path, 150)
        except IOError:
            font = ImageFont.load_default(size=150)  # Arial 폰트가 없는 경우 기본 폰트 사용

        # 텍스트 크기 계산 (bounding box를 이용)
        text_bbox = draw.textbbox((0, 0), error_text, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        message_bbox = draw.textbbox((0, 0), error_message, font=font)
        message_width, message_height = message_bbox[2] - message_bbox[0], message_bbox[3] - message_bbox[1]

        # 중앙에 텍스트 배치
        draw.text(((1920 - text_width) / 2, (1080 - text_height) / 2 - 200), error_text, fill=(255, 0, 0), font=font)
        draw.text(((1920 - message_width) / 2, (1080 - message_height) / 2 + 100), error_message, fill=(0, 0, 0), font=font)

        # 파일 경로 생성 및 저장
        fallback_image_path = os.path.join(screenshot_dir, f"{unique_id}_error.jpg")
        image.save(fallback_image_path, "JPEG", quality=85)
        return fallback_image_path
    except Exception as e:
        logging.error(f"대체 이미지 생성 오류: {str(e)}")
        return None



# 링크를 처리하는 함수 (변경된 부분 포함)
def process_link(row):
    driver = webdriver.Chrome(options=chrome_options)
    result = row.copy()
    url = row['url']
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if response.status_code >= 400:
            result['status'] = "에러"
            result['log'] = f"에러 코드 {response.status_code} - 페이지 없음"
        else:
            if not compare_without_subdomain(url, response.url):
                result['status'] = "리다이렉트 감지"
                result['log'] = f"Final URL: {response.url}"
            else:
                result['status'] = "정상"
            
            # 유튜브 URL인지 확인
            if "youtube.com" in urlparse(url).netloc:
                if "비공개" in response.text.lower() or "LOGIN_REQUIRED" in response.text.lower():
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
        handle_error(result, "HTTP 요청", e, "HTTP 오류", screenshot_dir)
    except Exception as e:
        handle_error(result, "처리 중", e, "스크린샷 오류", screenshot_dir)
    finally:
        driver.quit()

    return result

def time_logger(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        elapsed_time_str = time.strftime("%H시간 %M분 %S초", time.gmtime(elapsed_time))
        logging.info(f"{func.__name__} 처리 시간: {elapsed_time_str}")
        print(f"{func.__name__} 처리 시간: {elapsed_time_str}")
        return result
    return wrapper

# 메인 처리 함수 - 병렬로 링크 처리
@time_logger
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
    check_links(input_file="test_data_20241025.xlsx")


## To do List
# - Full HTML 에서 link 만 뽑아내기.