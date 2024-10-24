# 필요한 라이브러리 임포트
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import pandas as pd
from PIL import Image, UnidentifiedImageError
import streamlit as st
import plotly.graph_objects as go

# 페이지 레이아웃 설정
st.set_page_config(layout="wide")

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
file_path = 'processed_data_20241024_094802.xlsx'
data = load_data(file_path)

# 제목
st.markdown("<h1 class='text-4xl font-bold text-center my-4'>URL 상태 모니터링 대시보드</h1>", unsafe_allow_html=True)

# 탭 구성
tabs = st.tabs(["데이터 필터링", "요약 차트 보기", "이미지 전체 보기"])

with tabs[0]:
    st.markdown("<h2 class='text-2xl font-semibold mt-6'>데이터 필터링</h2>", unsafe_allow_html=True)
    
    # URL 상태 필터링 옵션 추가
    status_options = st.multiselect('상태를 선택하세요:', options=data['status'].unique(), default=data['status'].unique())
    filtered_data = data[data['status'].isin(status_options)]

    # 검색 기능 추가
    search_query = st.text_input('ID 또는 URL 검색:')
    if search_query:
        filtered_data = filtered_data[filtered_data['id'].str.contains(search_query) | 
                                      filtered_data['url'].str.contains(search_query, case=False)]

    # 레이아웃 나누기
    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown("<h2 class='text-2xl font-semibold mt-6'>URL 목록</h2>", unsafe_allow_html=True)
        
        # AgGrid를 사용하여 데이터 테이블 생성 ('screenshot' 열 제외)
        display_data = filtered_data[['id', 'url', 'status', 'last_checked','log']]
        gb = GridOptionsBuilder.from_dataframe(display_data)
        gb.configure_selection(selection_mode='single', use_checkbox=False)  # 체크박스 제거
        gb.configure_grid_options(enableRangeSelection=True, enableCellTextSelection=True)  # 복사 기능 활성화
        grid_options = gb.build()
        grid_options['enableClipboard'] = True  # 클립보드 기능 활성화

        grid_response = AgGrid(
            display_data,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            # height=400,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=True  # 엔터프라이즈 모듈 활성화
        )
        
        # 다운로드 버튼 추가
        # csv_data = display_data.to_csv(index=False).encode('utf-8')
        # st.download_button(
        #     label='전체 다운로드',
        #     data=csv_data,
        #     file_name='filtered_data.csv',
        #     mime='text/csv'
        # )

    with col2:
        st.markdown("<h2 class='text-2xl font-semibold mt-6'>URL 상세 보기</h2>", unsafe_allow_html=True)
        
        # 선택된 행이 있는지 확인
        selected_rows = grid_response['selected_rows']
        print(selected_rows)
        # 기존 selected_rows 처리 코드 유지
        if isinstance(selected_rows, pd.DataFrame):
            if not selected_rows.empty:
                selected_row = selected_rows.iloc[0]
                
                st.write(f"**ID:** {selected_row['id']}")
                st.write(f"**상태:** {selected_row['status']}")
                st.write(f"**마지막 체크 시간:** {selected_row['last_checked']}")
                st.write(f"**Log:** {selected_row['log']}")
                # 스크린샷 경로 가져오기
                screenshot_path = filtered_data[ (filtered_data['id'] == selected_row['id']) & (filtered_data['url'] == selected_row['url'])]['screenshot'].values[0]
                
                # 스크린샷 표시
                if pd.notnull(screenshot_path) and screenshot_path != '':
                    st.markdown("<h3 class='text-xl font-medium mt-4'>스크린샷:</h3>", unsafe_allow_html=True)
                    
                    # 예외 처리 추가
                    try:
                        with open(screenshot_path, 'rb') as f:
                            image = Image.open(f)
                            st.image(image, use_column_width=True, caption="미리보기")

                            # 전체 이미지 보기 버튼
                            # if st.button('전체보기', key='full_image'):
                            #     st.image(image, use_column_width=True)
                    except (FileNotFoundError, UnidentifiedImageError):
                        st.markdown("<p class='text-red-500'>이미지를 불러올 수 없습니다.</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p class='text-red-500'>스크린샷을 사용할 수 없습니다.</p>", unsafe_allow_html=True)
            else:
                st.write("선택된 URL이 없습니다.")
        elif isinstance(selected_rows, list):
            if len(selected_rows) > 0:
                selected_row = selected_rows[0]
                
                st.write(f"**ID:** {selected_row['id']}")
                st.write(f"**상태:** {selected_row['status']}")
                st.write(f"**마지막 체크 시간:** {selected_row['last_checked']}")
                
                # 스크린샷 경로 가져오기
                screenshot_path = filtered_data[filtered_data['id'] == selected_row['id']]['screenshot'].values[0]
                
                # 스크린샷 표시
                if pd.notnull(screenshot_path) and screenshot_path != '':
                    st.markdown("<h3 class='text-xl font-medium mt-4'>스크린샷:</h3>", unsafe_allow_html=True)
                    
                    # 예외 처리 추가
                    try:
                        with open(screenshot_path, 'rb') as f:
                            image = Image.open(f)
                            st.image(image, use_column_width=True, caption="미리보기")

                            # 전체 이미지 보기 버튼
                            # if st.button('전체보기', key='full_image'):
                            #     st.image(image, use_column_width=True)
                    except (FileNotFoundError, UnidentifiedImageError):
                        st.markdown("<p class='text-red-500'>이미지를 불러올 수 없습니다.</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p class='text-red-500'>스크린샷을 사용할 수 없습니다.</p>", unsafe_allow_html=True)
            else:
                st.write("선택된 URL이 없습니다.")
        else:
            st.write("선택된 URL이 없습니다.")
            
with tabs[1]:
    st.markdown("<h2 class='text-2xl font-semibold mt-6'>요약 차트 보기</h2>", unsafe_allow_html=True)
    
    # status별 데이터 개수 계산
    status_counts = data['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']

    # Plotly로 막대 차트 그리기 (막대 위에 count 표시 추가)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=status_counts['status'],
        y=status_counts['count'],
        text=status_counts['count'],
        textposition='auto',  # 막대 위에 텍스트 표시
        marker_color='skyblue'
    ))

    # 레이아웃 설정 (차트 크기 조정 포함)
    fig.update_layout(
        title='Status별 URL 개수',
        xaxis_title='Status',
        yaxis_title='Count',
        xaxis={'categoryorder': 'total descending'},  # 막대 정렬 (개수 내림차순)
        template='plotly_white',
        height=600,  # 차트 높이 조정
        width=1000   # 차트 너비 조정
    )

    # 차트 표시
    st.plotly_chart(fig)

with tabs[2]:
    st.markdown("<h2 class='text-2xl font-semibold mt-6'>이미지 전체 보기</h2>", unsafe_allow_html=True)
    
    # ID별로 데이터 그룹화
    grouped_data = filtered_data.groupby('id')

    # 각 ID별로 그룹화된 이미지를 표시
    for id, group in grouped_data:
        st.markdown(f"### ID: {id}")
        image_paths = group['screenshot'].dropna().unique()  # 중복 제거
        
        # 3열 갤러리로 이미지 표시
        cols = st.columns(3)
        for i, image_path in enumerate(image_paths):
            try:
                image = Image.open(image_path)
                with cols[i % 3]:  # 3열 갤러리에서 반복
                    st.image(image, caption=image_path, use_column_width=True)
            except (FileNotFoundError, UnidentifiedImageError):
                with cols[i % 3]:
                    st.error(f"이미지 로드 실패: {image_path}")
