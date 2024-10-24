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

# Google Material Design 적용을 위한 HTML/CSS 템플릿
material_css = """
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
    body { font-family: 'Roboto', sans-serif; }
    .md-card { box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); border-radius: 8px; padding: 20px; margin: 20px 0; }
    .md-title { font-size: 2rem; font-weight: bold; color: #3C4043; display: flex; align-items: center; }
    .md-title i { font-size: 2rem; margin-right: 8px; }
    .md-subtitle { font-size: 1.5rem; color: #5F6368; display: flex; align-items: center; }
    .md-subtitle i { font-size: 1.5rem; margin-right: 4px; }
    .md-button { background-color: #1A73E8; color: white; padding: 10px 20px; border-radius: 8px; cursor: pointer; text-align: center; }
    .md-button:hover { background-color: #155BB5; }
    .md-error { color: #D93025; }
    .md-gallery img { border-radius: 8px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15); margin: 10px; }
</style>
"""

st.markdown(material_css, unsafe_allow_html=True)

# 데이터 로드
file_path = 'processed_data_20241024_094802.xlsx'
data = load_data(file_path)

# 제목
st.markdown("<div class='md-title text-center'><i class='material-icons'>assessment</i> URL 상태 모니터링 대시보드</div>", unsafe_allow_html=True)

# 탭 구성
tabs = st.tabs(["데이터 필터링", "요약 차트 보기", "이미지 전체 보기"])

with tabs[0]:
    st.markdown("<div class='md-subtitle'><i class='material-icons'>filter_list</i> 데이터 필터링</div>", unsafe_allow_html=True)
    with st.expander(f"Search", expanded=True):
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
        st.markdown("<div class='md-subtitle'><i class='material-icons'>view_list</i> URL 목록</div>", unsafe_allow_html=True)

        # AgGrid를 사용하여 데이터 테이블 생성 ('screenshot' 열 제외)
        display_data = filtered_data[['id', 'url', 'status', 'last_checked','log']]
        gb = GridOptionsBuilder.from_dataframe(display_data)
        gb.configure_selection(selection_mode='single', use_checkbox=False)
        gb.configure_grid_options(enableRangeSelection=True, enableCellTextSelection=True)
        grid_options = gb.build()
        grid_options['enableClipboard'] = True

        grid_response = AgGrid(
            display_data,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=True
        )

    with col2:
        st.markdown("<div class='md-subtitle'><i class='material-icons'>info</i> URL 상세 보기</div>", unsafe_allow_html=True)

        # 선택된 행이 있는지 확인
        selected_rows = grid_response['selected_rows']
        if isinstance(selected_rows, pd.DataFrame):
            if not selected_rows.empty:
                selected_row = selected_rows.iloc[0]
                st.write(f"**ID:** {selected_row['id']}")
                st.write(f"**상태:** {selected_row['status']}")
                st.write(f"**마지막 체크 시간:** {selected_row['last_checked']}")
                st.write(f"**Log:** {selected_row['log']}")

                # 스크린샷 경로 가져오기
                screenshot_path = filtered_data[(filtered_data['id'] == selected_row['id'])]['screenshot'].values[0]

                if pd.notnull(screenshot_path) and screenshot_path != '':
                    st.markdown("<div class='md-subtitle'><i class='material-icons'>image</i> 스크린샷:</div>", unsafe_allow_html=True)
                    try:
                        with open(screenshot_path, 'rb') as f:
                            image = Image.open(f)
                            st.image(image, use_column_width=True, caption="미리보기")
                    except (FileNotFoundError, UnidentifiedImageError):
                        st.markdown("<div class='md-error'>이미지를 불러올 수 없습니다.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='md-error'>스크린샷을 사용할 수 없습니다.</div>", unsafe_allow_html=True)

with tabs[1]:
    st.markdown("<div class='md-subtitle'><i class='material-icons'>bar_chart</i> 요약 차트 보기</div>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])

    with col1:
        status_counts = data['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=status_counts['status'],
            y=status_counts['count'],
            text=status_counts['count'],
            textposition='auto',
            marker_color='#4285F4'  # 구글의 기본 색상
        ))

        fig.update_layout(
            title='Status별 URL 개수',
            xaxis_title='Status',
            yaxis_title='Count',
            xaxis={'categoryorder': 'total descending'},
            template='plotly_white',
            height=600,
            width=1000
        )

        st.plotly_chart(fig)

    with col2:
        # 색상 팔레트 정의
        colors = ['#FF7F0E', '#1F77B4', '#2CA02C', '#D62728', '#9467BD', '#8C564B', '#E377C2']

        # 도넛형 차트 생성
        fig = go.Figure(go.Pie(
            labels=status_counts['status'],
            values=status_counts['count'],
            hole=0.4,
            textinfo='label+percent',
            hoverinfo='label+percent+value',
            marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2))
        ))

        # 차트 레이아웃 설정
        fig.update_layout(
            title='Status별 URL 개수 분포',
            annotations=[dict(text='Status', x=0.5, y=0.5, font_size=20, showarrow=False)],
            showlegend=False,
            height=600,
            width=1000,
            template='plotly_white'
        )

        # 인포그래픽 요소 추가
        fig.add_annotation(
            text="전체 URL의 상태별 비율",
            x=0.5,
            y=-0.15,
            showarrow=False,
            font=dict(size=16)
        )

        fig.add_annotation(
            text=f"총 URL 개수: {data.shape[0]}",
            x=0.5,
            y=-0.25,
            showarrow=False,
            font=dict(size=14)
        )

        st.plotly_chart(fig)

with tabs[2]:
    st.markdown("<div class='md-subtitle'><i class='material-icons'>image</i> 이미지 전체 보기</div>", unsafe_allow_html=True)

    grouped_data = filtered_data.groupby('id')
    for id, group in grouped_data:
        with st.expander(f"ID: {id}", expanded=True):
            image_paths = group['screenshot'].dropna().unique()

            cols = st.columns(3)
            for i, image_path in enumerate(image_paths):
                try:
                    image = Image.open(image_path)
                    with cols[i % 3]:
                        st.image(image, caption=image_path, use_column_width=True)
                except (FileNotFoundError, UnidentifiedImageError):
                    with cols[i % 3]:
                        st.markdown(f"<div class='md-error'>이미지 로드 실패: {image_path}</div>", unsafe_allow_html=True)