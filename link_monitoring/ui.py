import streamlit as st
import pandas as pd
import os

# HTTP 응답 코드 설명 사전
http_status_descriptions = {
    200: "정상: 요청이 성공적으로 완료되었습니다.",
    400: "잘못된 요청: 서버가 요청을 이해하지 못했습니다.",
    401: "인증되지 않음: 서버에서 요청을 수행하려면 인증이 필요합니다.",
    403: "금지됨: 서버에서 요청을 거부했습니다.",
    404: "찾을 수 없음: 서버에서 요청한 리소스를 찾을 수 없습니다.",
    500: "내부 서버 오류: 서버에서 요청을 처리하는 중 오류가 발생했습니다.",
    502: "잘못된 게이트웨이: 서버에서 잘못된 응답을 받았습니다.",
    503: "서비스 불가: 서버가 일시적으로 요청을 처리할 수 없습니다.",
    504: "게이트웨이 시간 초과: 서버가 응답하는 데 시간이 너무 오래 걸렸습니다."
}

# HTTP 상태 코드에 대한 설명을 가져오는 함수
def get_http_status_description(status):
    try:
        # 상태 코드가 문자열로 저장된 경우 숫자로 변환
        status_code = int(status.split(' ')[1].strip('()'))
        return http_status_descriptions.get(status_code, "알 수 없는 상태 코드")
    except (ValueError, IndexError):
        return "상태 코드가 올바르지 않습니다."

# 엑셀 파일에서 데이터를 읽고 Streamlit UI로 표시하는 함수
def display_results():
    # 처리된 엑셀 파일 읽기
    file_path = "processed_data.xlsx"
    
    if not os.path.exists(file_path):
        st.error("처리된 데이터 파일이 없습니다. 먼저 데이터를 처리하세요.")
        return None, None

    # 처리된 엑셀 파일 읽기
    df = pd.read_excel(file_path)
    
    # 에러가 있는 링크만 추출
    error_links = df[df['status'] != '정상']

    return df, error_links

# Streamlit 앱 구성
st.title("링크 모니터링 결과")

# 처리된 데이터를 표시
df, error_links = display_results()

if df is not None:
    # 전체 데이터프레임 표시
    st.subheader("전체 데이터")
    st.dataframe(df[['id', 'title', 'url', 'page_type', 'last_checked', 'status']])

    # 에러가 있는 링크만 표시
    if not error_links.empty:
        st.subheader("에러가 발생한 링크 및 스크린샷")
        
        for idx, row in error_links.iterrows():
            # HTML로 카드 스타일 레이아웃을 만들어 시각적 구분을 추가
            st.markdown(
                f"""
                <div style="border: 2px solid #4CAF50; padding: 10px; margin: 10px 0; border-radius: 10px;">
                    <h3 style="color: #FF6347;">{row['title']}</h3>
                    <p><strong>URL:</strong> {row['url']}</p>
                    <p><strong>상태:</strong> {row['status']}</p>
                    <p><strong>설명:</strong> {get_http_status_description(row['status'])}</p>
                </div>
                """, unsafe_allow_html=True
            )

            screenshot_path = row['screenshot']
            
            # 스크린샷이 있는 경우 이미지 추가
            if pd.notna(screenshot_path) and os.path.exists(screenshot_path):
                st.image(screenshot_path, caption=f"{row['title']}의 스크린샷", use_column_width=True)
            else:
                st.warning("스크린샷을 찾을 수 없습니다.")
            
            # 항목 간의 경계선 추가
            st.markdown("<hr>", unsafe_allow_html=True)
    else:
        st.info("에러가 발생한 링크가 없습니다.")
