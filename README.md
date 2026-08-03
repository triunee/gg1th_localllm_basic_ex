# local_llm_app
local llm app 만들기 실무 실습자료

# 가상 환경 만들기
## uv 설치
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## path 설정
```
source $HOME/.local/bin/env
```
## 가상환경 만들기 
- 파이썬 버전과 프롬프트 설정
```
# .venv : 가상환경 이름
# local_llm : 프롬프트
uv venv .venv --python 3.12 --prompt local_llm
```
## 가상환경 활성화
```
source .venv/bin/activate
```