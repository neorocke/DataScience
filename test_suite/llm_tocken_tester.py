import time
import requests
import json

# API URL
api_url = "https://digilocas.duckdns.org/api/generate"

# 요청할 모델과 프롬프트
model_name = "qwen2.5:32b"
input_text = "이것은 LLAMA3 모델의 성능을 테스트하기 위한 문장입니다."

# 성능 테스트 함수
def test_performance(input_text):
    start_time = time.time()
    total_tokens = 0
    complete_response = ""

    for _ in range(50):  # 100회 반복
        # API 요청 데이터
        data = {
            "model": model_name,
            "prompt": input_text,
            "options": {
                "num_ctx": 4096
            }
        }
        
        # POST 요청
        response = requests.post(api_url, json=data, headers={"Content-Type": "application/json"})
        
        # 응답 상태 코드 및 내용 출력
        print("응답 상태 코드:", response.status_code)  # 상태 코드 출력
        
        # 응답 내용이 여러 JSON 객체로 되어 있을 경우 처리
        for line in response.text.splitlines():
            try:
                response_data = json.loads(line)  # 각 줄을 JSON으로 변환
                print("응답 JSON:", response_data)  # JSON 내용 출력
                
                # 토큰 수 확인
                if 'response' in response_data:
                    complete_response += response_data['response']  # 전체 응답 조합
                else:
                    print("'response' 키가 응답에 없습니다. 응답 데이터:", response_data)
                    return None
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}, 응답 내용: {line}")
                return None

    end_time = time.time()
    elapsed_time = end_time - start_time
    total_tokens = len(complete_response.split())  # 전체 응답의 단어 수 계산
    tpm = (total_tokens / elapsed_time) * 60  # 분당 토큰 수 계산

    return tpm

# 성능 테스트 실행
if __name__ == "__main__":
    tpm = test_performance(input_text)
    if tpm is not None:
        print(f"분당 토큰 수: {tpm}")