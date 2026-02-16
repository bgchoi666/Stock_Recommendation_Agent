# 📈 Stock Recommendation Agent 완전 가이드

> AI 기반 한국 주식 자동 추천 시스템 - 종합 분석 문서

**버전**: 1.0  
**작성일**: 2026년 2월 16일  
**저작권**: Copyright 2024 Bimghi Choi

---

## 📑 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [핵심 컴포넌트](#3-핵심-컴포넌트)
4. [설치 가이드](#4-설치-가이드)
5. [사용 방법](#5-사용-방법)
6. [데이터 구조](#6-데이터-구조)
7. [알고리즘 상세](#7-알고리즘-상세)
8. [문제 해결](#8-문제-해결)

---

## 1. 프로젝트 개요

### 1.1 소개

**Stock Recommendation Agent**는 한국 주식 시장을 위한 AI 기반 종합 자동화 트레이딩 시스템입니다.

**핵심 특징:**
- 🔍 키움증권 API 기반 기술적 분석
- 🤖 BERT 딥러닝 뉴스 감성 분석  
- 🎯 Google Gemini AI 통합 의사결정
- ⚡ 완전 자동화 워크플로우

### 1.2 주요 기능

#### 기술적 분석 모듈 (PyCond_refactored.py)
- 조건식 기반 종목 검색
- 복수 조건식 교집합 추출
- 재무지표 자동 수집 (PER, PBR, ROE)
- 매수/매도 리스트 관리

#### AI 뉴스 분석 (stock_news_analyzer.py)
- 구글 뉴스 자동 크롤링
- BERT 모델 학습 및 예측
- 종목별 상승/하락 확률 산출

#### 지능형 추천 (종목추천_gemini.py)
- Gemini API 다중 에이전트 분석
- 도구 기반 추가 정보 수집
- 최종 Best 종목 추천

### 1.3 시스템 요구사항

**필수:**
- Python 3.7+
- Windows OS (키움 OpenAPI)
- 키움증권 계좌
- 8GB RAM
- 인터넷 연결

**권장:**
- Python 3.9+
- 16GB RAM
- CUDA GPU
- SSD 저장장치

---

## 2. 시스템 아키텍처

### 2.1 전체 구조

```
┌────────────────────────────────────────┐
│   Stock Recommendation Agent          │
└────────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌────────┐ ┌──────┐ ┌────────┐
│PyCond  │ │BERT  │ │Gemini  │
│기술분석 │ │뉴스  │ │통합분석│
└────────┘ └──────┘ └────────┘
    │         │         │
    ▼         ▼         ▼
┌────────┐ ┌──────┐ ┌────────┐
│키움API │ │구글  │ │Gemini  │
│       │ │뉴스  │ │API     │
└────────┘ └──────┘ └────────┘
```

### 2.2 데이터 흐름

```
조건식 검색 → 종목 필터링 → 재무지표 수집
                ↓
        searched_items.csv
                ↓
        뉴스 크롤링 & BERT 분석
                ↓
        임의기간상승.csv
                ↓
        Gemini 종합 분석
                ↓
        최종 추천 결과
```

---

## 3. 핵심 컴포넌트

### 3.1 PyCond_refactored.py

**역할**: 키움 OpenAPI 기반 조건식 검색 및 관리

**주요 클래스**: `StockConditionManager`

**핵심 메서드:**
```python
search_stocks()              # 조건식 교집합 검색
get_stock_info()             # 재무지표 조회
search_all_combinations()    # 전체 자동 검색
_run_news_analysis()         # 뉴스 분석 실행
```

**알고리즘: 교집합 검색**
```python
def _find_common_stocks(condition_indices):
    common_stocks = []
    first_stocks = condCodes[condition_indices[0]]
    
    for stock_code in first_stocks:
        is_common = True
        for i in range(1, len(condition_indices)):
            if stock_code not in condCodes[condition_indices[i]]:
                is_common = False
                break
        if is_common:
            common_stocks.append(stock_code)
    
    return common_stocks
```

**재무지표 의미:**
- **PER**: 주가수익비율 (낮을수록 저평가)
- **PBR**: 주가순자산비율 (1 미만 저평가)
- **ROE**: 자기자본이익률 (높을수록 우량)

### 3.2 stock_news_analyzer.py

**역할**: BERT 기반 뉴스 감성 분석

**주요 클래스:**

1. **Config**: 전역 설정
```python
BERT_MODEL = 'small_bert/bert_en_uncased_L-4_H-512_A-8'
BATCH_SIZE = 32
EPOCHS = 1
LEARNING_RATE = 3e-5
```

2. **NewsCrawler**: 구글 뉴스 크롤링
```python
search_news(keyword, tbs, target)  # 뉴스 검색 및 수집
search_for_recommendation(keyword)  # 추천용 뉴스 (최근 5개)
```

3. **BERTModel**: 딥러닝 모델
```python
build_classifier()  # 모델 구축
train()             # 학습
predict()           # 예측
```

**BERT 아키텍처:**
```
입력 텍스트
    ↓
[BERT Preprocessing]
    ↓
[BERT Encoder (L-4, H-512)]
    ↓
[Pooled Output (512D)]
    ↓
[Dropout (0.1)]
    ↓
[Dense (1, sigmoid)]
    ↓
출력 (0~1 확률)
```

**학습 프로세스:**
1. 데이터 로드 (급등락뉴스.csv)
2. 학습/검증 분할 (90:10)
3. TensorFlow Dataset 생성
4. 모델 학습 (Adam optimizer)
5. 평가 및 가중치 저장

**추천 알고리즘:**
```python
for stock in stock_list:
    # 1. 최근 뉴스 5개 수집
    news_data = crawler.search_for_recommendation(stock)
    
    # 2. BERT 예측
    scores = model.predict(news_data)
    
    # 3. 평균 점수 계산
    avg_score = scores.mean()
    
    # 4. 임계값 확인
    if avg_score > threshold:
        recommendations.append(stock, avg_score)
```

### 3.3 종목추천_gemini.py

**역할**: Gemini AI 기반 통합 분석

**도구(Tools) 정의:**
```python
@tool
def search_news_of_item(item: str) -> str:
    """구글 뉴스에서 종목의 최근 24시간 뉴스 수집"""
    # 구현...

@tool
def get_stock_info(ticker: str) -> str:
    """Yahoo Finance에서 주식 정보 조회"""
    # 구현...

@tool
def get_historical_data(ticker: str, days: int) -> str:
    """과거 주가 데이터 조회"""
    # 구현...
```

**Gemini 워크플로우:**
```
[기술 + 뉴스 분석] → [초기 3개 추천]
        ↓
    [도구 활용]
     ↙  ↓  ↘
[뉴스] [주가] [재무]
     ↘  ↓  ↙
   [종합 분석]
        ↓
   [Best 선정]
```

---

## 4. 설치 가이드

### 4.1 Python 환경

```bash
# 가상환경 생성
python -m venv stock_env
stock_env\Scripts\activate  # Windows

# 패키지 설치
pip install PyQt5==5.15.9
pip install pandas numpy
pip install requests beautifulsoup4 lxml
pip install tensorflow==2.12.0
pip install tensorflow-hub tensorflow-text
pip install google-generativeai langchain-google-genai
pip install yfinance
```

### 4.2 API 키 설정

**종목추천_gemini.py (19번째 줄):**
```python
os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY_HERE"
```

### 4.3 파일 구조

```
project/
├── PyCond_refactored.py
├── stock_news_analyzer.py
├── 종목추천_gemini.py
├── condition.ui
├── Kiwoom.py
│
├── buy_list.csv
├── 코스피200.csv
├── 코스닥150.csv
│
├── 급등락뉴스.csv
├── model_weights.h5
└── 임의기간상승.csv
```

---

## 5. 사용 방법

### 5.1 완전 자동화 실행

```bash
# 1단계: 기술적 분석 (자동 종료)
python PyCond_refactored.py exit

# 2단계: 자동으로 뉴스 분석 실행됨

# 3단계: Gemini 통합 분석
python 종목추천_gemini.py

# 결과 확인
cat YYYY-MM-DD_recom_gemini.txt
```

### 5.2 PyCond GUI 모드

```bash
python PyCond_refactored.py
```

**주요 버튼:**
- **추가**: 조건식 검색 목록에 추가
- **새로고침**: 조건식 목록 갱신
- **검색**: 교집합 종목 검색
- **매수추가**: 선택 종목을 매수 리스트에 추가

### 5.3 뉴스 분석 독립 실행

**뉴스 크롤링:**
```bash
python stock_news_analyzer.py crawl \
  --start 2026 1 15 --end 2026 1 15 \
  --file buy_list.csv --threshold 10
```

**모델 학습:**
```bash
python stock_news_analyzer.py train \
  --data 급등락뉴스.csv \
  --train-size 60000
```

**종목 추천:**
```bash
# 전체 종목
python stock_news_analyzer.py recommend \
  --list all --threshold 0.8

# 개별 종목
python stock_news_analyzer.py recommend \
  --stocks 삼성전자 SK하이닉스
```

---

## 6. 데이터 구조

### 6.1 CSV 파일 형식

**searched_items.csv:**
```csv
date,매매,분류,code,종목명,PER,PBR,ROE,현재가,연중최고가,연중최저가
2026/01/15/09:00,매수,거래량급증,005930,삼성전자,15.23,1.45,12.5,75000,78000,65000
```

**buy_list.csv:**
```csv
종목명;종목코드
삼성전자;005930
SK하이닉스;000660
```

**급등락뉴스.csv:**
```csv
날짜,뉴스내용,target
2026-01-10,"삼성전자 신규 공장 투자...",1
2026-01-10,"SK하이닉스 실적 우려...",0
```

**임의기간상승.csv:**
```csv
date,item,news,result
2026-01-15-09:30,삼성전자,"신규 공장 착공...",0.8756
```

---

## 7. 알고리즘 상세

### 7.1 교집합 검색

**시간복잡도**: O(N × M)
- N: 조건식 개수
- M: 평균 종목 수

**최적화 (Set 연산):**
```python
result = set(condCodes[indices[0]])
for idx in indices[1:]:
    result &= set(condCodes[idx])
return list(result)
```

### 7.2 BERT 예측

**입력**: 뉴스 텍스트  
**출력**: 상승 확률 (0~1)

**프로세스:**
1. 토큰화 및 전처리
2. BERT 인코딩 (512차원)
3. Pooling
4. Dropout → Dense → Sigmoid
5. 확률 출력

### 7.3 종목 점수 산출

```python
# 개별 뉴스 점수 → 종목 점수
scores = [0.85, 0.92, 0.78, 0.88, 0.81]
avg_score = mean(scores)  # 0.848
```

**대안 방법:**
- 가중 평균 (최신 뉴스에 높은 가중치)
- 최댓값 (가장 긍정적인 뉴스 기준)
- 최솟값 제거 후 평균

---

## 8. 문제 해결

### 8.1 키움 API 오류

**증상**: 연결 실패

**해결:**
1. 영웅문 HTS 실행 확인
2. 수동 로그인
3. OpenAPI 권한 확인

### 8.2 메모리 부족

**증상**: OOM Error

**해결:**
```python
Config.BATCH_SIZE = 16  # 32 → 16
```

### 8.3 크롤링 실패

**증상**: HTTPError 429

**해결:**
```python
# 대기 시간 증가
time.sleep(5)

# User-Agent 변경
headers = {'user-agent': 'Mozilla/5.0 ...'}
```

### 8.4 정확도 문제

**원인:**
- 학습 데이터 부족
- 모델 과적합

**해결:**
```python
# 더 많은 데이터 수집 (10만 건+)
# Dropout 증가
Config.DROPOUT_RATE = 0.3

# 조기 종료
callbacks = [
    EarlyStopping(patience=3)
]
```

---

## 9. 성능 최적화

### 9.1 GPU 활용

```python
gpus = tf.config.list_physical_devices('GPU')
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)
```

### 9.2 병렬 처리

```python
from multiprocessing import Pool

with Pool(8) as pool:
    results = pool.map(crawl_single_stock, stock_list)
```

### 9.3 캐싱

```python
@lru_cache(maxsize=1000)
def get_cached_prediction(text):
    return model.predict([text])[0]
```

---

## 10. 고급 기능

### 10.1 배치 스크립트

**Windows (.bat):**
```batch
@echo off
python PyCond_refactored.py exit
python 종목추천_gemini.py
pause
```

**Linux (.sh):**
```bash
#!/bin/bash
python PyCond_refactored.py exit
python 종목추천_gemini.py
```

### 10.2 실시간 모니터링

```python
class RealtimeMonitor:
    def monitor(self, threshold=0.85):
        while True:
            for stock in watch_list:
                result = self.check_news(stock)
                if result['score'] >= threshold:
                    send_alert(result)
            time.sleep(300)  # 5분 간격
```

### 10.3 텔레그램 알림

```python
class TelegramNotifier:
    def send_recommendation(self, recommendations):
        message = "📈 오늘의 추천\n\n"
        for rec in recommendations:
            message += f"{rec['stock']}: {rec['score']}\n"
        self.send_message(message)
```

---

## 11. 참고 자료

### 11.1 기술 문서

- TensorFlow BERT: https://www.tensorflow.org/text/tutorials/classify_text_with_bert
- BERT Paper: https://arxiv.org/abs/1810.04805
- 키움 OpenAPI: https://www.kiwoom.com/

### 11.2 관련 프로젝트

- KoBERT: https://github.com/SKTBrain/KoBERT
- LangChain: https://python.langchain.com/

---

## 12. 라이선스 및 면책

**라이선스**: Copyright 2024 Bimghi Choi. All Rights Reserved.

**투자 경고**:
- ⚠️ 이 프로그램은 **투자 참고용**입니다
- 📉 과거 데이터가 미래를 보장하지 않습니다
- 💰 모든 투자는 본인 책임입니다

---

## 13. 문의 및 지원

**이슈**: GitHub Issues  
**문서**: 프로젝트 README 참조

---

**Made with ❤️ and 🐍 Python**
