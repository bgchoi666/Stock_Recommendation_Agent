import os
import pandas as pd
import yfinance as yf
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage

import datetime

#from retrievers import ai_contents

# OpenAI API 키 설정 (환경 변수로 설정하는 것을 권장)
os.environ["OPENAI_API_KEY"] = "API_KEY"
#os.environ["OPENAI_API_KEY"] = "API_KEY"

version = "gpt-5"

# 1. 주식 데이터 가져오기 도구 정의
@tool
def get_stock_info(ticker: str) -> str:
    """
    Yahoo Finance에서 특정 주식 종목의 현재 가격과 기본 통계 정보를 가져옵니다.
    :param ticker: 주식 심볼 (예: 'AAPL', 'TSLA')
    :return: 주식 정보가 포함된 문자열
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get('currentPrice', 'N/A')
        pe_ratio = info.get('trailingPE', 'N/A')
        market_cap = info.get('marketCap', 'N/A')
        return f"{ticker}의 현재 가격: {current_price}, P/E 비율: {pe_ratio}, 시가총액: {market_cap}"
    except Exception as e:
        return f"Error: {e}"

@tool
def get_historical_data(ticker: str, days: int = 30) -> str:
    """
    Yahoo Finance에서 특정 주식 종목의 지정된 기간 동안의 종가 데이터를 가져옵니다.
    :param ticker: 주식 심볼 (예: 'AAPL')
    :param days: 과거 일수 (기본값: 30일)
    :return: 과거 종가 데이터의 문자열 표현
    """
    try:
        hist = yf.Ticker(ticker).history(period=f'{days}d')
        if hist.empty:
            return f"No historical data found for {ticker}"
        # 최근 5일치 데이터만 반환하도록 제한
        recent_data = hist['Close'].tail(5).to_string()
        return f"{ticker}의 최근 {days}일 중 마지막 5일 종가:\n{recent_data}"
    except Exception as e:
        return f"Error: {e}"

def search_items():

    # 조건검색식 추천 종목 얻기
    now = datetime.datetime.now().strftime("%Y/%m/%d/00:00")
    df = pd.read_csv("PyCond/searched_items.csv", encoding="euc-kr")
    df = df.loc[df['date'] >= now].reset_index(drop=True)

    # 오늘 날짜로 검색된 추천 종목 없으면 프로그램 실행
    if len(df) == 0:
        os.chdir("PyCond")
        os.system("C:/anaconda3_32/python PyCond.py exit")
        os.chdir("../")

        df = pd.read_csv("PyCond/searched_items.csv", encoding="euc-kr")
        df = df.loc[df['date'] >= now].reset_index(drop=True)

    # 뉴스 분석 추천 종목 얻기
    now_bert = datetime.datetime.now().strftime("%Y-%m-%d-00:00")
    df_bert = pd.read_csv("뉴스분석/임의기간상승.csv", encoding="euc-kr")
    df_bert = df_bert.loc[df_bert['date'] >= now_bert].reset_index(drop=True)

    # 오늘 날짜로 검색된 뉴스 분석 추천 종목 없으면 프로그램 실행
    if len(df) == 0:
        os.chdir("뉴스분석")
        os.system("C:/Users/user/Anaconda3/envs/tensorflow-text/python 급등주추천3.py all 0.95")
        os.chdir("../")

        df_bert = pd.read_csv("뉴스분석/임의기간상승.csv", encoding="euc-kr")
        df = df.loc[df['date'] >= now].reset_index(drop=True)
    
    prompt = f"""
    다음은 키움 조건 검색식에 있는 여러 분야(데이터의 컬럼 참조)로부터 기술적 지표상 매수 추천 주식 종목들입니다. 

    --- 조건 검색식 추천 데이터 시작 ---
    항목 이름들
    {df.columns}
    데이터
    {df.values}
    --- 조건 검색식 추천 데이터 끝 ---

    다음은 Bert를 이용하여 학습한 뉴스 분석 프로그램에서 전일 뉴스와 관련하여 상승 확률이 높은 종목들을 추출한 것입니다
    항목이름들
    --- 뉴스 분석 추천 데이터 시작 ---
    항목 이름들
    {df_bert.columns}
    데이터
    {df_bert.values}
    --- 뉴스 분석 추천 데이터 끝 ---

    이 데이터들을 분석하여 best 종목 세개만 추천해 주세요.
    """

    return prompt

# 2. 첫 질문 LLM 도구 설정
#tools = [get_stock_info, get_historical_data]
#llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
model = ChatOpenAI(
    model=version,
    temperature=0,
    #max_tokens=1000,
    #timeout=30
    # ... (other params)
)

# 3. 에이전트 생성 및 실행기 초기화
#agent = create_openai_tools_agent(llm, tools, prompt)
agent = create_agent(model=model, system_prompt="당신은 주식 시장 데이터에 접근할 수 있는 전문 금융 분석가입니다.")

#agent = create_agent(model=model)

# 4. 사용자 입력 처리 예시
#user_input = "삼성전자는 어떤 기업인가요"#"애플(AAPL)은 어떤 기업인가요"
user_input = search_items()

print(f"사용자 입력: {user_input}\n")
#response = agent_executor.invoke({"input": user_input, "chat_history": []})

response = agent.invoke({
    "messages": [
        {"role": "user", "content": user_input}
    ]
})

print("\n--- 첫 질문 답변 ---")
#print(response)

# 5. 파싱 로직
ai_contents = []

for message in response['messages']:
    # 메시지가 AIMessage 타입인지 확인
    if isinstance(message, AIMessage):
        ai_contents.append(message.content)

# 6.첫 답변 결과 출력
for content in ai_contents:
    print(content)


# 7. 두 번쩨 질문의 LLM 및 도구 설정
tools = [get_stock_info, get_historical_data]
#llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
model2 = ChatOpenAI(
    model=version,
    temperature=0,
    #max_tokens=1000,
    #timeout=30
    # ... (other params)
)

# 8. 두 번쩨 질문의 에이전트 생성 및 실행기 초기화
#agent = create_openai_tools_agent(llm, tools, prompt)
agent2 = create_agent(model=model2, tools=tools,
    system_prompt="당신은 주식 시장 데이터에 접근할 수 있는 전문 금융 분석가입니다.")


# 9. 두 번쩨 질문의 사용자 입력 처리
user_input2 = ai_contents[-1] + ("\n\n 이상으로 추천된 3개 종목의 선정 이유를 간단히 설명하고 비교 분석한 후 최종 best 종목을 "
                                 "추천해 주는데 필요하면 주어진 tool들을 사용헤 주세요"
                                 "종목코드는 숫자옆에 .ks 또는 .kq를 붙이면 됩니다.")


print(f"사용자 입력2: {user_input2}\n")

response2 = agent2.invoke({
    "messages": [
        {"role": "user", "content": user_input2}
    ]
})

# 10. 두번 쨰 답변 파싱 로직
ai_contents = []

for message in response2['messages']:
    # 메시지가 AIMessage 타입인지 확인
    if isinstance(message, AIMessage):
        ai_contents.append(message.content)

# 11.두 번째 답변 결과 출력
for content in ai_contents:
    print(content)

# 12. 분석 결과 text 파일로 저장
now = datetime.datetime.now().strftime("%Y-%m-%d")
file_path = now + "_recom_gpt.txt"

# 파일을 'w' 모드(쓰기 모드)로 열고, 인코딩을 utf-8로 지정
# 'with' 구문은 파일이 자동으로 닫히게 해줍니다.
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)


print(f"'{file_path}'에 문자열이 성공적으로 저장되었습니다.")
