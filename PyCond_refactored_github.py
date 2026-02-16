# -*- coding:utf-8 -*-
"""
PyCond - 키움증권 조건식 검색 및 매매 관리 프로그램

주요 기능:
- 조건식 기반 종목 검색
- 매수/매도 리스트 관리
- 보유종목 조회
- 재무지표 분석 (PER, PBR, ROE)
"""

import sys
import os
import time
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import uic
import pandas as pd
import numpy as np
from Kiwoom import Kiwoom


# UI 파일 로드
UI_FORM_CLASS = uic.loadUiType("../condition.ui")[0]

# 상수 정의
API_CALL_DELAY = 0.2  # API 호출 간 대기 시간 (초)
TIMER_INTERVAL = 1000  # 타이머 간격 (밀리초)
EVAL_SCORE_INVALID = 999  # 유효하지 않은 평가 점수
STOCK_CODE_LENGTH = 6  # 종목코드 길이

# 파일 경로
FILE_BUY_LIST = "buy_list.txt"
FILE_SELL_LIST = "sell_list.txt"
FILE_BUY_LIST_CSV = "buy_list.csv"
FILE_SEARCHED_ITEMS = "searched_items.csv"

# 파일 형식
ENCODING_UTF8 = 'utf-8'
ENCODING_EUCKR = 'euc-kr'


class StockConditionManager(QMainWindow, UI_FORM_CLASS):
    """주식 조건식 검색 및 관리를 위한 메인 윈도우 클래스"""
    
    def __init__(self, mode=0):
        """
        초기화 함수
        
        Args:
            mode: 프로그램 동작 모드 ('exit': 자동검색 후 종료, 기타: GUI 모드)
        """
        super().__init__()
        self.mode = mode
        self.item_info_display_state = 0  # 0: 가격정보, 1: 재무지표
        self.first_refresh = 1
        
        # UI 초기화
        self.setupUi(self)
        
        # 키움 API 초기화
        self._init_kiwoom_api()
        
        # UI 컨트롤 연결
        self._connect_ui_controls()
        
        # 테이블 설정
        self._setup_table()
        
        # 타이머 설정
        self._setup_timer()
    
    def _init_kiwoom_api(self):
        """키움 API 초기화 및 로그인"""
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()  # 로그인
        self.kiwoom.dynamicCall('GetConditionLoad()')  # 조건식 목록 요청
        time.sleep(API_CALL_DELAY)
    
    def _connect_ui_controls(self):
        """UI 버튼과 이벤트 핸들러 연결"""
        # 조건식 관리
        self.pushButton.clicked.connect(self.select_condition_item)
        self.pushButton_2.clicked.connect(self.refresh_conditions)
        self.pushButton_3.clicked.connect(self.search_stocks)
        self.pushButton_4.clicked.connect(self.clear_selected_conditions)
        self.pushButton_5.clicked.connect(self.delete_selected_condition)
        self.pushButton_6.clicked.connect(self.delete_table_row)
        
        # 매수 리스트 관리
        self.pushButton_7.clicked.connect(self.add_to_buy_list)
        self.pushButton_8.clicked.connect(self.load_buy_list)
        self.pushButton_9.clicked.connect(self.reset_buy_list)
        
        # 매도 리스트 관리
        self.pushButton_10.clicked.connect(self.add_to_sell_list)
        self.pushButton_11.clicked.connect(self.load_sell_list)
        self.pushButton_13.clicked.connect(self.reset_sell_list)
        
        # 전체 검색
        self.pushButton_12.clicked.connect(self.search_all_combinations)
    
    def _setup_table(self):
        """테이블 위젯 초기 설정"""
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.clicked.connect(self.get_stock_info)
    
    def _setup_timer(self):
        """타이머 설정 (자동 검색 모드용)"""
        self.timer = QTimer(self)
        self.timer.start(TIMER_INTERVAL)
        self.timer.timeout.connect(self._on_timer_timeout)
    
    # ========== 타이머 이벤트 ==========
    
    def _on_timer_timeout(self):
        """타이머 만료 시 호출 (자동 검색 모드)"""
        if self.mode == 'exit':
            self.search_all_combinations()
            exit(0)
    
    # ========== 조건식 관리 ==========
    
    def show_condition_name_list(self):
        """키움 서버에서 가져온 조건식 목록 표시"""
        for condition_name in self.kiwoom.conditionNames:
            self.listWidget.addItem(condition_name)
    
    def select_condition_item(self):
        """선택한 조건식을 검색 조건 리스트에 추가"""
        selected_item = self.listWidget.currentItem()
        if selected_item:
            self.listWidget_2.addItem(selected_item.text())
    
    def refresh_conditions(self):
        """조건식 목록 새로고침"""
        self.listWidget.clear()
        
        # 기존에 추가된 보유종목 제거
        if '보유종목' in self.kiwoom.conditionNames:
            del self.kiwoom.condCodes[-3:]
        
        self._load_holding_stocks()
        self.show_condition_name_list()
    
    def clear_selected_conditions(self):
        """선택된 조건식 리스트 초기화"""
        self.listWidget_2.clear()
    
    def delete_selected_condition(self):
        """선택된 조건식 하나 삭제"""
        current_row = self.listWidget_2.currentRow()
        self.listWidget_2.takeItem(current_row)
    
    def delete_table_row(self):
        """테이블에서 선택된 행 삭제"""
        current_row = self.tableWidget.currentRow()
        self.tableWidget.removeRow(current_row)
    
    # ========== 종목 검색 ==========
    
    def search_stocks(self):
        """선택된 조건식들의 교집합 종목 검색"""
        self.tableWidget.setRowCount(0)
        
        # 선택된 조건식의 인덱스 추출
        condition_indices = self._get_selected_condition_indices()
        
        # 교집합 종목 코드 추출
        common_stock_codes = self._find_common_stocks(condition_indices)
        
        # 검색 결과 로드
        self._load_stock_list_to_table(common_stock_codes)
    
    def _get_selected_condition_indices(self):
        """
        선택된 조건식들의 인덱스를 반환
        
        Returns:
            list: 조건식 인덱스 리스트
        """
        indices = []
        for i in range(self.listWidget_2.count()):
            condition_name = self.listWidget_2.item(i).text()
            index = self.kiwoom.conditionNames.index(condition_name)
            indices.append(index)
        return indices
    
    def _find_common_stocks(self, condition_indices):
        """
        여러 조건식의 공통 종목 찾기
        
        Args:
            condition_indices: 조건식 인덱스 리스트
            
        Returns:
            list: 공통 종목 코드 리스트
        """
        if not condition_indices:
            return []
        
        common_stocks = []
        first_condition_stocks = self.kiwoom.condCodes[condition_indices[0]]
        
        # 첫 번째 조건의 각 종목이 다른 모든 조건에도 포함되는지 확인
        for stock_code in first_condition_stocks:
            is_common = True
            
            for i in range(1, len(condition_indices)):
                if stock_code not in self.kiwoom.condCodes[condition_indices[i]]:
                    is_common = False
                    break
            
            if is_common:
                common_stocks.append(stock_code)
        
        return common_stocks
    
    # ========== 종목 정보 조회 ==========
    
    def get_stock_info(self):
        """테이블에서 선택한 종목의 상세 정보 조회 및 표시"""
        current_row = self.tableWidget.currentRow()
        stock_code = self.tableWidget.item(current_row, 0).text()
        
        # 종목 정보 조회
        self._request_stock_info(stock_code)
        time.sleep(API_CALL_DELAY)
        
        # 표시 모드에 따라 다른 정보 표시
        if self.item_info_display_state == 0:
            self._display_price_info(current_row)
            self.item_info_display_state = 1
        else:
            self._display_financial_info(current_row)
            self.item_info_display_state = 0
        
        self.tableWidget.resizeRowsToContents()
    
    def _request_stock_info(self, stock_code):
        """종목 정보 API 요청"""
        self.kiwoom.set_input_value('종목코드', stock_code)
        self.kiwoom.comm_rq_data('opt10001_req', 'opt10001', 0, 4000)
    
    def _display_price_info(self, row):
        """가격 정보 표시 (현재가, 연중최고가, 연중최저가)"""
        price_data = [
            (2, self.kiwoom.opt10001_현재가),
            (3, self.kiwoom.opt10001_연중최고),
            (4, self.kiwoom.opt10001_연중최저)
        ]
        
        for col, value in price_data:
            self._set_table_item(row, col, value)
    
    def _display_financial_info(self, row):
        """재무 정보 표시 (PER, PBR, ROE)"""
        financial_data = [
            (2, self.kiwoom.opt10001_PER),
            (3, self.kiwoom.opt10001_PBR),
            (4, self.kiwoom.opt10001_ROE)
        ]
        
        for col, value in financial_data:
            self._set_table_item(row, col, value)
    
    def _set_table_item(self, row, col, text):
        """테이블 셀에 값 설정 (중앙 정렬)"""
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
        self.tableWidget.setItem(row, col, item)
    
    # ========== 매수 리스트 관리 ==========
    
    def init_buy_list(self):
        """CSV에서 매수 리스트 초기화"""
        with open(FILE_BUY_LIST, "wt", encoding=ENCODING_UTF8) as f:
            df = pd.read_csv(FILE_BUY_LIST_CSV, encoding=ENCODING_EUCKR)
            
            for _, row in df.iterrows():
                stock_code = str(row['종목코드']).zfill(STOCK_CODE_LENGTH)
                stock_name = row['종목명']
                trade_line = self._create_trade_line('매수', stock_code, stock_name)
                f.write(trade_line + '\n')
    
    def add_to_buy_list(self):
        """선택된 종목을 매수 리스트에 추가"""
        current_row = self.tableWidget.currentRow()
        stock_code = self.tableWidget.item(current_row, 0).text()
        stock_name = self.tableWidget.item(current_row, 1).text()
        
        with open(FILE_BUY_LIST, "at", encoding=ENCODING_UTF8) as f:
            trade_line = self._create_trade_line('매수', stock_code, stock_name)
            f.write(trade_line + '\n')
        
        self._sort_trade_list(FILE_BUY_LIST, '매수', reverse=False)
    
    def reset_buy_list(self):
        """테이블의 모든 종목으로 매수 리스트 재설정"""
        row_count = self.tableWidget.rowCount()
        
        with open(FILE_BUY_LIST, "wt", encoding=ENCODING_UTF8) as f:
            for i in range(row_count):
                stock_code = self.tableWidget.item(i, 0).text()
                stock_name = self.tableWidget.item(i, 1).text()
                trade_line = self._create_trade_line('매수', stock_code, stock_name)
                f.write(trade_line + '\n')
        
        self._sort_trade_list(FILE_BUY_LIST, '매수', reverse=False)
    
    def load_buy_list(self):
        """매수 리스트 파일을 읽어서 테이블에 표시"""
        self._load_trade_list_to_table(FILE_BUY_LIST)
    
    # ========== 매도 리스트 관리 ==========
    
    def add_to_sell_list(self):
        """선택된 종목을 매도 리스트에 추가"""
        current_row = self.tableWidget.currentRow()
        stock_code = self.tableWidget.item(current_row, 0).text()
        stock_name = self.tableWidget.item(current_row, 1).text()
        
        with open(FILE_SELL_LIST, "at", encoding=ENCODING_UTF8) as f:
            trade_line = self._create_trade_line('매도', stock_code, stock_name)
            f.write(trade_line + '\n')
        
        self._sort_trade_list(FILE_SELL_LIST, '매도', reverse=True)
    
    def reset_sell_list(self):
        """테이블의 모든 종목으로 매도 리스트 재설정"""
        row_count = self.tableWidget.rowCount()
        
        with open(FILE_SELL_LIST, "wt", encoding=ENCODING_UTF8) as f:
            for i in range(row_count):
                stock_code = self.tableWidget.item(i, 0).text()
                stock_name = self.tableWidget.item(i, 1).text()
                trade_line = self._create_trade_line('매도', stock_code, stock_name)
                f.write(trade_line + '\n')
        
        self._sort_trade_list(FILE_SELL_LIST, '매도', reverse=True)
    
    def load_sell_list(self):
        """매도 리스트 파일을 읽어서 테이블에 표시"""
        self._load_trade_list_to_table(FILE_SELL_LIST)
    
    # ========== 공통 헬퍼 메서드 ==========
    
    def _create_trade_line(self, trade_type, stock_code, stock_name):
        """
        매매 리스트 파일 라인 생성
        
        Args:
            trade_type: '매수' 또는 '매도'
            stock_code: 종목코드
            stock_name: 종목명
            
        Returns:
            str: 파일 라인 문자열
        """
        status = f"{trade_type}전"
        return f"{trade_type};{stock_code};시장가;10;0;{status};{stock_name}"
    
    def _load_trade_list_to_table(self, filename):
        """
        매매 리스트 파일을 테이블에 로드
        
        Args:
            filename: 파일 경로
        """
        with open(filename, 'rt', encoding=ENCODING_UTF8) as f:
            trade_list = f.read().splitlines()
        
        self.tableWidget.setRowCount(len(trade_list))
        
        for i, line in enumerate(trade_list):
            stock_code = line.split(';')[1]
            
            # 종목 정보 조회
            self._request_stock_info(stock_code)
            time.sleep(API_CALL_DELAY)
            
            # 테이블에 정보 표시
            self._set_stock_info_to_table(i)
        
        self.tableWidget.resizeRowsToContents()
    
    def _set_stock_info_to_table(self, row):
        """
        종목 정보를 테이블 행에 설정
        
        Args:
            row: 테이블 행 번호
        """
        stock_data = [
            (0, self.kiwoom.opt10001_종목코드),
            (1, self.kiwoom.opt10001_종목명),
            (2, self.kiwoom.opt10001_PER),
            (3, self.kiwoom.opt10001_PBR),
            (4, self.kiwoom.opt10001_ROE)
        ]
        
        for col, value in stock_data:
            self._set_table_item(row, col, value)
    
    def _sort_trade_list(self, filename, trade_type, reverse=False):
        """
        매매 리스트를 평가 점수로 정렬
        
        Args:
            filename: 정렬할 파일 경로
            trade_type: '매수' 또는 '매도'
            reverse: True이면 내림차순, False이면 오름차순
        """
        # 파일 읽기
        with open(filename, 'rt', encoding=ENCODING_UTF8) as f:
            trade_list = f.read().splitlines()
        
        # 평가 점수 계산 및 데이터 구성
        data_with_scores = []
        for line in trade_list:
            parts = line.split(';')[:7]
            stock_code = parts[1]
            
            # 재무지표 조회
            self._request_stock_info(stock_code)
            time.sleep(API_CALL_DELAY)
            
            # 평가 점수 계산: PER - ROE + PBR
            eval_score = self._calculate_eval_score()
            parts.append(eval_score)
            data_with_scores.append(parts)
        
        # 정렬
        data_with_scores.sort(key=lambda x: x[7], reverse=reverse)
        
        # 파일에 저장
        with open(filename, "wt", encoding=ENCODING_UTF8) as f:
            for item in data_with_scores:
                line = f"{trade_type};{item[1]};시장가;10;0;{trade_type}전;{item[6]};{item[7]}\n"
                f.write(line)
    
    def _calculate_eval_score(self):
        """
        평가 점수 계산
        
        Returns:
            float: 평가 점수 (PER - ROE + PBR)
        """
        try:
            per = self.kiwoom.opt10001_PER
            pbr = self.kiwoom.opt10001_PBR
            roe = self.kiwoom.opt10001_ROE
            
            if not per or not pbr or not roe:
                return EVAL_SCORE_INVALID
            
            return float(per) - float(roe) + float(pbr)
        except (ValueError, AttributeError):
            return EVAL_SCORE_INVALID
    
    def _load_stock_list_to_table(self, stock_codes):
        """
        종목 코드 리스트를 테이블에 로드
        
        Args:
            stock_codes: 종목코드 리스트
        """
        self.tableWidget.setSortingEnabled(False)
        self.tableWidget.setRowCount(len(stock_codes))
        
        for row, stock_code in enumerate(stock_codes):
            # 종목코드 표시
            self._set_table_item(row, 0, stock_code)
            
            # 종목명 조회 및 표시
            stock_name = self.kiwoom.get_master_code_name(stock_code)
            self._set_table_item(row, 1, stock_name)
            
            # 재무지표 조회
            self._request_stock_info(stock_code)
            time.sleep(API_CALL_DELAY)
            
            # 재무지표 표시
            financial_data = [
                (2, self.kiwoom.opt10001_PER),
                (3, self.kiwoom.opt10001_PBR),
                (4, self.kiwoom.opt10001_ROE)
            ]
            
            for col, value in financial_data:
                self._set_table_item(row, col, value)
        
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.setSortingEnabled(True)
    
    # ========== 보유종목 관리 ==========
    
    def _load_holding_stocks(self):
        """계좌의 보유종목 조회 및 조건식에 추가"""
        # 보유종목 조건식 추가
        if '보유종목' not in self.kiwoom.conditionNames:
            self.kiwoom.conditionNames.append("보유종목")
        
        # 계좌 정보 초기화
        self.kiwoom.reset_opw00018_output()
        
        # 계좌번호 가져오기
        account_number = self._get_valid_account_number()
        
        # 보유종목 조회
        self._request_holding_stocks(account_number)
        
        # 조회 결과를 조건식 코드에 추가
        stock_codes = self._extract_holding_stock_codes()
        self.kiwoom.condCodes.append(stock_codes)
        
        # buy_list와 sell_list도 추가
        self._append_trade_lists()
    
    def _get_valid_account_number(self):
        """
        유효한 계좌번호 가져오기 (위탁계좌 우선)
        
        Returns:
            str: 계좌번호
        """
        account_numbers = self.kiwoom.get_login_info("ACCNO")
        accounts = account_numbers.split(';')
        
        # 계좌번호 뒤 두자리가 '11' 또는 '10'인 계좌 우선 선택
        primary_account = accounts[0]
        if primary_account[8:] not in ['11', '10'] and len(accounts) > 1:
            primary_account = accounts[1]
        
        return primary_account
    
    def _request_holding_stocks(self, account_number):
        """
        보유종목 조회 API 요청
        
        Args:
            account_number: 계좌번호
        """
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.set_input_value("조회구분", 2)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
        
        # 연속 조회
        while self.kiwoom.remained_data:
            time.sleep(API_CALL_DELAY)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.set_input_value("조회구분", 2)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")
    
    def _extract_holding_stock_codes(self):
        """
        보유종목 조회 결과에서 종목코드 추출
        
        Returns:
            list: 종목코드 리스트
        """
        stock_codes = []
        item_count = len(self.kiwoom.opw00018_output['multi'])
        
        for i in range(item_count):
            code = self.kiwoom.opw00018_output['multi'][i][6]
            stock_codes.append(code[1:])  # 앞의 'A' 제거
        
        return stock_codes
    
    def _append_trade_lists(self):
        """buy_list와 sell_list를 조건식에 추가"""
        # buy_list 추가
        if 'buy_list' not in self.kiwoom.conditionNames:
            self.kiwoom.conditionNames.append("buy_list")
        
        buy_codes = self._read_trade_list_codes(FILE_BUY_LIST)
        self.kiwoom.condCodes.append(buy_codes)
        
        # sell_list 추가
        if 'sell_list' not in self.kiwoom.conditionNames:
            self.kiwoom.conditionNames.append("sell_list")
        
        sell_codes = self._read_trade_list_codes(FILE_SELL_LIST)
        self.kiwoom.condCodes.append(sell_codes)
    
    def _read_trade_list_codes(self, filename):
        """
        매매 리스트 파일에서 종목코드 추출
        
        Args:
            filename: 파일 경로
            
        Returns:
            list: 종목코드 리스트
        """
        with open(filename, 'rt', encoding=ENCODING_UTF8) as f:
            lines = f.read().splitlines()
        
        return [line.split(';')[1] for line in lines]
    
    # ========== 전체 자동 검색 ==========
    
    def search_all_combinations(self):
        """
        매수 조건과 다른 조건들의 조합으로 자동 검색
        결과를 CSV에 저장하고 뉴스 분석 프로그램 실행
        """
        # 결과 저장용 데이터프레임
        columns = ['date', '매매', '분류', 'code', '종목명', 
                  'PER', 'PBR', 'ROE', '현재가', '연중최고가', '연중최저가']
        all_results = pd.DataFrame(columns=columns)
        
        # 인덱스 0 (매수)과 2~10의 각 조건을 조합하여 검색
        for i in range(2, 11):
            stock_codes = self._find_common_stocks([0, i])
            
            if not stock_codes:
                continue
            
            # 각 종목의 상세 정보 수집
            results = self._collect_stock_details(stock_codes, 0, i)
            
            # 결과 추가
            result_df = pd.DataFrame(results, columns=columns)
            all_results = pd.concat([all_results, result_df], ignore_index=True)
            
            print(f"{self.kiwoom.conditionNames[i]} 중에서 매수 추천 종목들 add")
        
        # CSV에 저장
        self._save_search_results(all_results)
        
        # 뉴스 분석 실행
        self._run_news_analysis(all_results)
    
    def _collect_stock_details(self, stock_codes, buy_index, condition_index):
        """
        종목 상세 정보 수집
        
        Args:
            stock_codes: 종목코드 리스트
            buy_index: 매수 조건 인덱스
            condition_index: 기타 조건 인덱스
            
        Returns:
            list: 종목 정보 리스트
        """
        results = []
        current_time = datetime.datetime.now().strftime("%Y/%m/%d/%H:%M")
        
        for stock_code in stock_codes:
            stock_name = self.kiwoom.get_master_code_name(stock_code)
            
            # 재무지표 및 가격 정보 조회
            self._request_stock_info(stock_code)
            time.sleep(API_CALL_DELAY)
            
            # 정보 수집
            stock_info = [
                current_time,
                self.kiwoom.conditionNames[buy_index],
                self.kiwoom.conditionNames[condition_index],
                stock_code,
                stock_name,
                self.kiwoom.opt10001_PER,
                self.kiwoom.opt10001_PBR,
                self.kiwoom.opt10001_ROE,
                self.kiwoom.opt10001_현재가,
                self.kiwoom.opt10001_연중최고,
                self.kiwoom.opt10001_연중최저
            ]
            
            results.append(stock_info)
        
        return results
    
    def _save_search_results(self, new_results):
        """
        검색 결과를 CSV 파일에 추가 저장
        
        Args:
            new_results: 새로운 검색 결과 데이터프레임
        """
        # 기존 파일 읽기
        existing_df = pd.read_csv(FILE_SEARCHED_ITEMS, encoding=ENCODING_EUCKR)
        
        # 새 결과 추가
        combined_df = pd.concat([existing_df, new_results], ignore_index=True)
        
        # 저장
        combined_df.to_csv(FILE_SEARCHED_ITEMS, encoding=ENCODING_EUCKR, index=False)
    
    def _run_news_analysis(self, results_df):
        """
        추출된 종목에 대한 뉴스 분석 프로그램 실행
        
        Args:
            results_df: 검색 결과 데이터프레임
        """
        # 종목명 추출
        stock_names = ' '.join(results_df['종목명'].values)
        
        # 디렉토리 변경 및 뉴스 분석 실행
        os.chdir('H:/급등주_bert')
        os.system(f'C:/Users/user/Anaconda3/envs/tensorflow-text/python 급등주추천_개별.py {stock_names}')
        os.chdir('H:/알고리즘트레이딩2')


def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    
    # 커맨드 라인 인자로 모드 결정
    mode = sys.argv[1] if len(sys.argv) > 1 else 0
    
    # 윈도우 생성 및 표시
    window = StockConditionManager(mode)
    window.show()
    
    # 이벤트 루프 실행
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
