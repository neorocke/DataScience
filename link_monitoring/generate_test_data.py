import random
import pandas as pd

# 테스트 데이터 생성 함수
def generate_test_data(num_samples=10, output_file="test_data.xlsx"):
    titles = [
        '최신 스마트폰 출시', '여름 맞이 패션 아이템', '건강한 식단 가이드',
        '프로그래밍 입문서', '여행지 추천', '홈트레이닝 방법',
        '신작 영화 리뷰', '재테크 비법', '사진 촬영 팁', 'DIY 인테리어'
    ]
    base_urls = [
        'https://www.google.com/', 'https://naver.com', 
    ]
    data = []
    for i in range(num_samples):
        title = random.choice(titles)
        page_type = random.choice(['제품', '정보'])
        # 일부 URL에 에러를 의도적으로 삽입
        if random.random() < 0.2:
            url = 'https://example.com/invalid/' + str(i)
        else:
            url = random.choice(base_urls)
        data.append({
            'id': i,
            'title': title,
            'url': url,
            'page_type': page_type,
            'last_checked': None,
            'status': None,
        })

    # 데이터를 pandas DataFrame으로 변환 후 엑셀로 저장
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)
    print(f"데이터가 {output_file} 파일로 저장되었습니다.")

# 실행 시 데이터 생성
if __name__ == "__main__":
    generate_test_data(num_samples=20, output_file="test_data.xlsx")
