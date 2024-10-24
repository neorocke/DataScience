#!/bin/bash

# Conda 환경 이름 설정
ENV_NAME="link_monitor_env"

# 필요한 패키지 목록
REQUIRED_PACKAGES=(
    "python"
    "requests"
    "pandas=2.2.2"
    "openpyxl"
    "pip"
    "selenium"
)

# Conda가 설치되어 있는지 확인
if ! command -v conda &> /dev/null
then
    echo "Conda가 설치되어 있지 않습니다. 먼저 Conda를 설치해주세요."
    exit 1
fi

# 새로운 Conda 환경 생성
echo "Conda 환경 '$ENV_NAME'을 생성합니다..."
conda create -y -n $ENV_NAME ${REQUIRED_PACKAGES[@]}

# 환경 활성화
echo "Conda 환경 '$ENV_NAME'을 활성화합니다..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate $ENV_NAME

# pip로 추가 패키지 설치
echo "Selenium 및 Gradio 패키지를 설치합니다..."
pip install selenium beautifulsoup4 streamlit streamlit-aggrid pillow plotly

# Chrome 및 ChromeDriver 설치 (Ubuntu 20.04 기준)
echo "Google Chrome 및 ChromeDriver를 설치합니다..."

# 시스템 업데이트
sudo apt update -y

# 필수 패키지 설치
sudo apt install -y wget unzip xvfb libxi6 libgconf-2-4

# Google Chrome 설치 (129 버전)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# Chrome 버전 추출
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+')
CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d'.' -f1)

echo "Chrome 버전: $CHROME_VERSION"
echo "Chrome 주요 버전: $CHROME_MAJOR_VERSION"

# 최신 ChromeDriver 버전 확인 및 다운로드 (Chrome for Testing 사용)
CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_$CHROME_MAJOR_VERSION")

if [ -z "$CHROMEDRIVER_VERSION" ]; then
    echo "ChromeDriver 버전을 찾을 수 없습니다. 최신 버전으로 다운로드를 시도합니다."
    CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE")
fi

# ChromeDriver 설치
echo "ChromeDriver 버전: $CHROMEDRIVER_VERSION"
wget -N "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip"
if [ $? -ne 0 ]; then
    echo "ChromeDriver 다운로드에 실패했습니다."
    exit 1
fi

unzip -o chromedriver-linux64.zip -d ./
chmod +x ./chromedriver-linux64/chromedriver
sudo mv -f ./chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
rm chromedriver-linux64.zip

# font
sudo apt install fonts-nanum

# Conda 환경 설정 완료 메시지
echo "설치가 완료되었습니다. '$ENV_NAME' 환경이 준비되었습니다."
echo "환경을 활성화하려면 'conda activate $ENV_NAME'을 실행하세요."
