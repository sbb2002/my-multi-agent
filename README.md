# 0. 프로젝트 이동
cd C:\Users\user\Documents\claudespace\my-multi-agent

# 1. 가상환경 생성 (권장)
python -m venv venv
venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. API 키 입력 (.env 파일 열어서)
# ANTHROPIC_API_KEY=sk-ant-여기에_실제_키_입력

# 4. 서버 실행
cd app
uvicorn main:app --reload