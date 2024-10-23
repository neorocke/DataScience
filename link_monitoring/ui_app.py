import streamlit as st
import pandas as pd
from PIL import Image, UnidentifiedImageError

# 엑셀 파일 로드
@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)

# Tailwind CSS 적용을 위한 HTML 템플릿
tailwind_css = """
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
"""

st.markdown(tailwind_css, unsafe_allow_html=True)

# 데이터 로드
file_path = 'processed_data_20241023_100915.xlsx'
data = load_data(file_path)

# 제목
st.markdown("<h1 class='text-4xl font-bold text-center my-4'>URL 상태 모니터링 대시보드</h1>", unsafe_allow_html=True)

# URL 상태 필터링 옵션 추가
status_options = st.multiselect('상태를 선택하세요:', options=data['status'].unique(), default=data['status'].unique())
filtered_data = data[data['status'].isin(status_options)]

# 검색 기능 추가
search_query = st.text_input('ID 또는 URL 검색:')
if search_query:
    filtered_data = filtered_data[filtered_data['id'].str.contains(search_query) | 
                                  filtered_data['url'].str.contains(search_query, case=False)]

# 필터링된 데이터 프레임 표시
st.markdown("<h2 class='text-2xl font-semibold mt-6'>URL 목록</h2>", unsafe_allow_html=True)
st.dataframe(filtered_data[['id', 'url', 'status', 'last_checked', 'screenshot']])

# 선택한 URL 상세 정보 표시
st.markdown("<h2 class='text-2xl font-semibold mt-6'>URL 상세 보기</h2>", unsafe_allow_html=True)
selected_url = st.selectbox('URL을 선택하세요:', filtered_data['url'])

# 선택한 URL의 상세 정보 추출
url_info = filtered_data[filtered_data['url'] == selected_url].iloc[0]
st.write(f"**ID:** {url_info['id']}")
st.write(f"**상태:** {url_info['status']}")
st.write(f"**마지막 체크 시간:** {url_info['last_checked']}")

# 스크린샷 미리보기 및 전체보기 추가
if url_info['screenshot']:
    st.markdown("<h3 class='text-xl font-medium mt-4'>스크린샷:</h3>", unsafe_allow_html=True)
    image_path = url_info['screenshot']
    
    # 예외 처리 추가: 이미지 파일이 없거나 열 수 없을 경우 대비
    try:
        image = Image.open(image_path)
        # 미리보기 이미지
        st.image(image, width=300, caption="미리보기")

        # 전체 이미지 보기 버튼
        if st.button('전체보기'):
            st.image(image, use_column_width=True)
    except (FileNotFoundError, UnidentifiedImageError):
        st.markdown("<p class='text-red-500'>이미지를 불러올 수 없습니다.</p>", unsafe_allow_html=True)
else:
    st.markdown("<p class='text-red-500'>스크린샷을 사용할 수 없습니다.</p>", unsafe_allow_html=True)
