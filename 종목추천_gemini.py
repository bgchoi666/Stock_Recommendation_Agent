import os
import pandas as pd
import yfinance as yf

#import google.generativeai as genai
import google.genai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

import datetime

# 구슬 뉴스 스크로링을 위하여
import re
import requests
import lxml
from bs4 import BeautifulSoup as bs

os.environ["GOOGLE_API_KEY"] = "API_KEY"
#os.environ["GOOGLE_API_KEY"] = "API_KEY"
#genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
# 클라이언트 인스턴스화 (configure 대신 사용)
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


# 1. 구글 뉴스 가져오기 도구 정의
@tool
def search_news_of_item(item: str) -> str:
    """
    구글 뉴스에서 특정 주식 종목의 현재부터 1일전 깨지의 뉴스를 가져옵니다.
    :param 종목 이름: 주식 종목 이름(예: '삼성전자', 'sk하이닉스')
    :return: 입력 주식 종목에 대한 뉴스가 포함된 문자열
    """
    time_pools = [
        "1시간 전", "2시간 전", "3시간 전", "4시간 전", "5시간 전", "6시간 전", "7시간 전", "8시간 전",
        "9시간 전", "10시간 전", "11시간 전", "12시간 전", "13시간 전", "14시간 전", "15시간 전", "16시간 전",
        "17시간 전", "18시간 전", "19시간 전", "20시간 전", "21시간 전", "22간 전", "23시간 전", "24시간 전",
        #"1일 전", "2일 전", "3일 전"
    ]

    #item = '나노신소재'
    params = {'q': item, 'hl': 'ko', 'tbm': 'nws'}

    header = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
    cookie = {'CONSENT' : 'YES'}
    url = 'https://www.google.com/search?'

    res = requests.get(url, params = params, headers = header, cookies = cookie)
    soup = bs(res.text, 'lxml')

    # 기사제목 파싱하는 부분
    titles = soup.find_all('div', 'ilUpNd UFvD1 aSRlid IwSnJ')#''n0jPhd ynAwRc MBeuO nDgy9d')
    contents = soup.find_all('div', 'ilUpNd H66NU aSRlid')#'GI74Re nDgy9d')
    times = soup.find_all('span', 'UK5aid MDvRSc')#''OSrXXb rbYSKb LfVVr')

    all_news = []
    concat_titles = ''
    n = 0
    for i in range(len(titles)):

        if times[i].get_text() not in time_pools and '분' not in times[i].get_text():
            continue

        n += 1
        if n < 10:
            #concat_titles += titles[i].get_text() + ' '
            #concat_titles = re.sub(r'[^\uAC00-\uD7A30-9a-zA-Z\s\-\+\%\.\,\/\*\$\?\!]', ' ', concat_titles)

            news = titles[i].get_text() + " " + contents[i].get_text()
            news = re.sub(r'[^\uAC00-\uD7A30-9a-zA-Z\s\-\+\%\.\,\/\*\$\?\!]', ' ', news)

            all_news.append(news)

    #result = []

    #result.append(item)
    #result.append(concat_titles)
    #result.append(all_news)

    return " ".join(all_news)

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
    df = pd.read_csv("H:/알고리즘트레이딩2/searched_items.csv", encoding="euc-kr")
    df = df.loc[df['date'] >= now].reset_index(drop=True)

    # 오늘 날짜로 검색된 추천 종목 없으면 프로그램 실행
    if len(df) == 0:
        os.chdir("H:/알고리즘트레이딩2")
        os.system("C:/anaconda3_32/python PyCond.py exit")
        os.chdir("H:/langchain")

        df = pd.read_csv("H:/알고리즘트레이딩2/searched_items.csv", encoding="euc-kr")
        df = df.loc[df['date'] >= now].reset_index(drop=True)

    # 뉴스 분석 추천 종목 얻기
    now_bert = datetime.datetime.now().strftime("%Y-%m-%d-00:00")
    df_bert = pd.read_csv("H:/급등주_bert/임의기간상승.csv", encoding="euc-kr")
    df_bert = df_bert.loc[df_bert['date'] >= now_bert].reset_index(drop=True)

    # 오늘 날짜로 검색된 뉴스 분석 추천 종목 없으면 프로그램 실행
    if len(df) == 0:
        os.chdir("H:/급등주_bert")
        os.system("C:/Users/user/Anaconda3/envs/tensorflow-text/python 급등주추천3.py all 0.97")
        os.chdir("H:/langchain")

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

    이 데이터들을 분석하여 3개 종목들을 추천해 주세요.
    """

    return prompt

#이 데이터들을 분석하여 3개 종목들을 추천해 주고 선정 이유에 대한 설명과 비교 분석을 통하여 최종 best 종목 하나를 추천해 주세요.

version = 'gemini-3-flash-preview'#'gemini-2.5-flash'

# 1. 모델 선택 (gemini-1.5-flash는 빠르고 비용 효율적입니다)
#model = genai.GenerativeModel(version)

# 2. 콘텐츠 생성 요청
prompt = search_items()
#response = model.generate_content(prompt)
response = client.models.generate_content(model=version, contents=prompt)

print(response.text)

# 3. tool과 결합한 생성 모델 설정
tools = [get_stock_info, get_historical_data, search_news_of_item]
tools_map = {
    "get_stock_info": get_stock_info,
    "get_historical_data": get_historical_data,
    "search_news_of_item": search_news_of_item
}

# Gemini 모델 초기화 (예: gemini-2.5-flash)
llm = ChatGoogleGenerativeAI(model=version)

# 모델에 도구 바인딩
model_with_tools = llm.bind_tools(tools)

# 모델에게 도구 사용을 유도하는 메시지 전달
query = response.text + ("\n\n 이상으로 추천된 3개 종목의 선정 이유를 간단히 설명하고 비교 분석한 후 최종 best 종목을 "
                                 "추천해 주는데 필요하면 주어진 tool들을 사용헤 주세요"
                                 "종목코드는 숫자옆에 .ks 또는 .kq를 붙이면 됩니다.")

#prompt = search_items()
messages = [HumanMessage(content=query)]

# 첫 번째 호출 (모델이 도구 사용을 결정)
response = model_with_tools.invoke(messages)
messages.append(response)

print(f"모델의 1차 응답 (도구 호출 요청 수): {len(response.tool_calls)}")
print("호출할 도구 정보:", response.tool_calls)
print("모델 응답 (도구 호출):", response.content)

# 2단계: 애플리케이션에서 도구 실행 (여기서는 수동으로 시뮬레이션)
if response.tool_calls:
    for tool_call in response.tool_calls:
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        tool_call_id = tool_call['id']

        print(f" -> 도구 호출 감지: {tool_name} with args {tool_args}")

        # 해당 도구가 존재하는지 확인 후 실행
        if tool_name in tools_map:
            selected_tool = tools_map[tool_name]
            # 도구 실행
            observation = selected_tool.invoke(tool_args)
            print(f" -> 실행 결과: {observation}")

            # 5. 도구 결과를 메시지 리스트에 추가
            messages.append(ToolMessage(
                content=str(observation),  # 결과는 문자열로 변환하는 것이 안전
                tool_call_id=tool_call_id,
                name=tool_name
            ))

    # 6. 최종 응답 생성 (도구 실행 결과를 바탕으로 모델이 답변)
    final_response = model_with_tools.invoke(messages)
    print("최종 모델 응답:", final_response.content)
else:
    print("모델이 도구를 호출하지 않았습니다.")


# 도구 사용 안하고 best 종목 추천
#query = response.text + ("\n\n 이상으로 추천된 3개 종목의 선정 이유를 간단히 설명하고 비교 분석한 후 최종 best 종목을 "
#                                 "추천해 주 주세요")
#final_response = model.generate_content(query)

# 12. 분석 결과 text 파일로 저장
now = datetime.datetime.now().strftime("%Y-%m-%d")
file_path = now + "_recom_gemini.txt"

# 파일을 'w' 모드(쓰기 모드)로 열고, 인코딩을 utf-8로 지정
# 'with' 구문은 파일이 자동으로 닫히게 해줍니다.
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(str(final_response.text)) # 두 번째 답변
    #f.write(str(response.text)) # 첫 번째 답변

print(f"'{file_path}'에 문자열이 성공적으로 저장되었습니다.")
