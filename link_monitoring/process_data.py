import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import os
import shutil
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import urlparse, urlunparse
import re
import configparser

# ------------------------ 설정 파일 읽기 ------------------------
config = configparser.ConfigParser()
config.read('config.ini')

# 로깅 설정
logging.basicConfig(
    filename=config.get('Logging', 'log_file', fallback='process.log'),
    level=config.getint('Logging', 'log_level', fallback=logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 환경 설정 상수
screenshot_dir = config.get('Settings', 'screenshot_dir', fallback='screenshots')
MAX_THREADS = config.getint('Settings', 'max_threads', fallback=16)
REQUEST_TIMEOUT = config.getint('Settings', 'request_timeout', fallback=20)
WAIT_FOR_PAGE_TIMEOUT = config.getint('Settings', 'wait_for_page_timeout', fallback=20)
DEFAULT_FONT_PATH = config.get('Settings', 'default_font_path', fallback='/usr/share/fonts/truetype/nanum/NanumGothic.ttf')

# 상태 코드 상수 정의
STATUS_OK = "OK"
STATUS_REDIRECT = "REDIRECT"
STATUS_CLIENT_ERROR = "CLIENT_ERROR"
STATUS_SERVER_ERROR = "SERVER_ERROR"
STATUS_EMPTY_CONTENT = "EMPTY_CONTENT"
STATUS_YOUTUBE_PRIVATE = "YOUTUBE_PRIVATE"
STATUS_YOUTUBE_DELETED = "YOUTUBE_DELETED"
STATUS_YOUTUBE_AGE_RESTRICTED = "YOUTUBE_AGE_RESTRICTED"
STATUS_YOUTUBE_REGION_BLOCKED = "YOUTUBE_REGION_BLOCKED"
STATUS_YOUTUBE_EMBEDDING_DISABLED = "YOUTUBE_EMBEDDING_DISABLED"
STATUS_YOUTUBE_UNAVAILABLE = "YOUTUBE_UNAVAILABLE"
STATUS_ERROR = "ERROR"

# 초기 디렉토리 및 파일 설정
def setup_directories():
    try:
        if os.path.exists("processed_data.xlsx"):
            os.remove("processed_data.xlsx")
        if os.path.exists(screenshot_dir):
            shutil.rmtree(screenshot_dir)
        os.makedirs(screenshot_dir, exist_ok=True)
        logging.info("디렉토리 설정 완료.")
    except Exception as e:
        logging.error(f"디렉토리 설정 실패: {str(e)}")

# Selenium WebDriver 설정
def configure_webdriver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 추가적인 옵션 설정 가능
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
        logging.info(f"스크린샷 변환 완료: {jpg_path}")
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
                if stable_count >= stability_threshold:
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
    logging.error(f"{error_type} 오류: {str(exception)}", exc_info=True)
    result['status'] = STATUS_ERROR
    result['log'] = f'오류 ({error_message}: {str(exception)})'

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

        # 폰트 설정
        try:
            font = ImageFont.truetype(DEFAULT_FONT_PATH, 150)
        except IOError:
            font = ImageFont.load_default()

        # 텍스트 크기 계산
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
        logging.info(f"대체 이미지 생성 완료: {fallback_image_path}")
        return fallback_image_path
    except Exception as e:
        logging.error(f"대체 이미지 생성 오류: {str(e)}")
        return None

# Full HTML에서 링크만 추출하는 함수 (To-do List 구현)
def extract_links_from_html(html_content):
    try:
        # 정규식을 이용하여 모든 링크 추출
        links = re.findall(r'href=["\'](.*?)["\']', html_content, re.IGNORECASE)
        logging.info(f"추출된 링크 수: {len(links)}")
        return links
    except Exception as e:
        logging.error(f"HTML에서 링크 추출 실패: {str(e)}")
        return []

# 유튜브 상태 감지 함수
def detect_youtube_status(html_content):
    lower_text = html_content.lower()
    
    # 유튜브 비공개 동영상 감지
    if re.search(r'(비공개|login_required)', lower_text):
        return STATUS_YOUTUBE_PRIVATE, "유튜브 비공개 동영상 감지"
    
    # 유튜브 삭제된 동영상 감지
    if re.search(r'(삭제한|removed by the user)', lower_text):
        return STATUS_YOUTUBE_DELETED, "유튜브 삭제된 동영상 감지"
    
    # 유튜브 연령 제한 동영상 감지
    if re.search(r'(age-restricted|연령 제한)', lower_text):
        return STATUS_YOUTUBE_AGE_RESTRICTED, "유튜브 연령 제한 동영상 감지"
    
    # 유튜브 지역 제한 동영상 감지
    if re.search(r'(not available in your country|현재 국가에서 사용할 수 없습니다)', lower_text):
        return STATUS_YOUTUBE_REGION_BLOCKED, "유튜브 지역 제한 동영상 감지"
    
    # 유튜브 임베딩 비활성화 감지
    if re.search(r'(embedding has been disabled|임베딩이 비활성화되었습니다)', lower_text):
        return STATUS_YOUTUBE_EMBEDDING_DISABLED, "유튜브 임베딩 비활성화 감지"
    
    # 유튜브 기타 사용 불가 상태 감지
    if re.search(r'(video unavailable|동영상 사용 불가)', lower_text):
        return STATUS_YOUTUBE_UNAVAILABLE, "유튜브 동영상 사용 불가 감지"
    
    return STATUS_OK, "정상 응답"

# 빈 콘텐츠 감지 함수 (렌더된 HTML 기반으로 수정)
def is_empty_content_rendered(driver):
    try:
        # 렌더된 HTML 가져오기
        rendered_html = driver.page_source

        # 기본 빈도 검사
        if len(rendered_html.strip()) == 0:
            return True

        # 콘텐츠 길이 기준 추가 (예: 200자 미만)
        if len(rendered_html.strip()) < 200:
            return True

        # <body> 태그 내에 실제 콘텐츠가 있는지 검사
        body_match = re.search(r'<body[^>]*>(.*?)</body>', rendered_html, re.DOTALL | re.IGNORECASE)
        if body_match:
            body_content = body_match.group(1).strip()
            # 주요 콘텐츠 태그가 있는지 확인
            if not re.search(r'<(div|p|span|h[1-6]|article|section|main|nav|header|footer|aside)[^>]*>', body_content, re.IGNORECASE):
                return True
        else:
            # <body> 태그가 없으면 빈 콘텐츠로 간주
            return True

        # 추가적인 텍스트 기반 검사 (예: 스크립트나 스타일 태그 외에 실제 텍스트가 있는지)
        visible_text = re.sub(r'<script[^>]*>.*?</script>', '', rendered_html, flags=re.DOTALL | re.IGNORECASE)
        visible_text = re.sub(r'<style[^>]*>.*?</style>', '', visible_text, flags=re.DOTALL | re.IGNORECASE)
        visible_text = re.sub(r'<[^>]+>', '', visible_text).strip()
        if len(visible_text) < 50:
            return True

        return False
    except Exception as e:
        logging.error(f"렌더된 HTML에서 빈 콘텐츠 검사 실패: {str(e)}")
        return False

# 링크를 처리하는 함수 (표준화된 용어 사용 및 유튜브 상태 세분화)
def process_link(row):
    driver = webdriver.Chrome(options=chrome_options)
    result = row.copy()
    url = row['url']
    try:
        # WebDriver 설정
        driver.set_window_size(1920, 1080)
        
        # Selenium을 이용하여 페이지 로드 및 대기
        driver.get(url)
        wait_for_page_load(driver)

        # 리다이렉트를 허용하고 요청 시도
        response = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)

        # 리다이렉트 히스토리에서 상태 코드 수집
        redirect_codes = [resp.status_code for resp in response.history]
        result['redirect_codes'] = redirect_codes if redirect_codes else "없음"

        # 최종 응답 상태 코드 처리
        if 300 <= response.status_code < 400:
            # 리다이렉트 최종 상태 코드
            result['status'] = STATUS_REDIRECT
            final_url = response.url
            result['log'] = f"리다이렉트 코드 {response.status_code} -> 최종 URL: {final_url}"
        elif 400 <= response.status_code < 500:
            result['status'] = STATUS_CLIENT_ERROR
            result['log'] = f"클라이언트 오류 코드 {response.status_code}"
        elif 500 <= response.status_code < 600:
            result['status'] = STATUS_SERVER_ERROR
            result['log'] = f"서버 오류 코드 {response.status_code}"
        else:
            # Selenium을 이용한 렌더된 HTML 기반 빈 콘텐츠 감지
            if is_empty_content_rendered(driver):
                result['status'] = STATUS_EMPTY_CONTENT
                result['log'] = "200 OK 응답 - 콘텐츠 없음 (빈 페이지)"
            else:
                # 유튜브 URL인지 확인
                if "youtube.com" in urlparse(url).netloc:
                    youtube_status, youtube_log = detect_youtube_status(driver.page_source)
                    result['status'] = youtube_status
                    result['log'] = youtube_log
                else:
                    result['status'] = STATUS_OK
                    result['log'] = "정상 응답"

        result['last_checked'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Selenium을 이용한 스크린샷 저장
        url_hash = generate_hash(url)
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S%f')[:-3]
        screenshot_png_path = os.path.join(screenshot_dir, f"{row['id']}_{url_hash}_{current_time}.png")
        screenshot_jpg_path = os.path.join(screenshot_dir, f"{row['id']}_{url_hash}_{current_time}.jpg")

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

# 실행 시간을 기록하는 데코레이터
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
        # 필요한 경우 특정 행 필터링
        # df = df[df['id'].astype(str).str.startswith('F차0925006') | df['id'].astype(str).str.startswith('E국0926003')]
        # df = df[df['id'].astype(str).str.startswith('E국0926003')]
        processed_data = []
        setup_directories()

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(process_link, row) for _, row in df.iterrows()]
            for future in as_completed(futures):
                processed_data.append(future.result())

        processed_df = pd.DataFrame(processed_data)
        processed_df.to_excel(output_file, index=False)
        logging.info(f"처리된 데이터가 {output_file} 파일로 저장되었습니다.")
        print(f"처리된 데이터가 {output_file} 파일로 저장되었습니다.")

    except Exception as e:
        logging.error(f"파일 처리 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    check_links(input_file="test_data_20241025.xlsx")
