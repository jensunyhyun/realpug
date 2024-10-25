import time
import json
import os
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import schedule
import tkinter as tk
from tkinter import ttk
import threading

# 설정 변수
BASE_URL = "https://pugshop.co.kr/main-page/?tab=shopping"  # 새로운 BASE URL
CHROME_DRIVER_PATH = "./chromedriver.exe"  # ChromeDriver 경로
CHECK_INTERVAL = 3600  # 제품 체크 주기 (초 단위로 설정)

# 이메일 설정 (자신의 이메일로 수정)
SMTP_SERVER = "smtp.gmail.com"  # Gmail을 사용할 경우
SMTP_PORT = 587
SENDER_EMAIL = "appleoy2@gmail.com"  # 자신의 이메일
SENDER_PASSWORD = "WPSL9Rjdi8@"  # 자신의 이메일 비밀번호
RECEIVER_EMAIL = "appleoy2@gmail.com"  # 알림을 받을 이메일

# 데이터 저장 파일
DATA_FILE = "products.json"

# 카테고리 선택 기능
def select_category():
    categories = {
        '0201': '화장품/미용',
        '0202': '패션 의류',
        '0203': '식품',
        '0204': '가구/인테리어',
        '0205': '출산/육아',
        '0206': '반려동물',
        '0207': '디지털/가전',
        '0208': '생활/건강',
        '0209': '스포츠/취미/레저',
        '0210': '건강기능식품',
        '0211': '자동차',
        '0212': '패션 잡화',
        '0299': '기타'
    }
    
    print("카테고리를 선택하세요:")
    for key, value in categories.items():
        print(f"{key}: {value}")
    
    selected = input("카테고리 번호를 입력하세요 (예: 0201): ")
    
    if selected in categories:
        return selected, categories[selected]
    else:
        print("잘못된 선택입니다. 기본 카테고리로 이동합니다.")
        return '0201', categories['0201']  # 기본 카테고리로 설정

# 제품 목록 스크래핑 함수
def get_product_list(selected_category_value):
    # Selenium WebDriver 설정
    service = Service(CHROME_DRIVER_PATH)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 브라우저 창을 띄우지 않고 실행
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(BASE_URL)
        
        # 페이지가 로드될 때까지 대기
        wait = WebDriverWait(driver, 10)
        
        # 카테고리 선택 버튼이 나타날 때까지 기다림
        category_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'button[value="{selected_category_value}"]')))
        category_button.click()
        
        # 페이지 로딩 대기
        time.sleep(3)
        
        # 페이지 소스 가져오기
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # 제품 정보가 포함된 'campaign-card' 클래스를 가진 div 태그 찾기
        product_elements = soup.find_all('div', class_='campaign-card')
        product_list = []

        # 제품 정보 추출
        for product in product_elements:
            # 브랜드명 추출
            brand_element = product.find('div', class_='text-gray-3')
            brand = brand_element.text.strip() if brand_element else "브랜드 정보 없음"
            
            # 제품 이름 추출 (클래스명 일부만 사용하여 찾기)
            product_name_element = product.find('div', class_=lambda x: x and 'text-md' in x)
            product_name = product_name_element.text.strip() if product_name_element else "제품명 없음"
            
            # 실제 구매가 추출
            actual_price_element = product.find('span', class_='campaign-point')
            actual_price = actual_price_element.text.strip() if actual_price_element else "가격 정보 없음"
            
            # 할인 전 가격 추출
            original_price_element = product.find('p', class_='text-xs text-gray-4 font-bold line-through')
            original_price = original_price_element.text.strip() if original_price_element else None
            
            # 남은 시간 추출
            remaining_time_element = product.find('div', class_='flex items-center gap-x-1')
            remaining_time_span = remaining_time_element.find('span') if remaining_time_element else None
            remaining_time = remaining_time_span.text.strip() if remaining_time_span else None

            # 제품 상태 추출
            status_element = product.find('div', class_='close-text')
            status = status_element.text.strip() if status_element else "진행중"
            
            # 제품 정보를 딕셔너리 형태로 저장 (값이 None일 경우 출력하지 않음)
            product_info = {
                '브랜드': brand,
                '제품명': product_name,
                '실제 구매가': actual_price
            }
            if original_price:
                product_info['할인 전 가격'] = original_price
            if remaining_time:
                product_info['남은 시간'] = remaining_time
            if status:
                product_info['상태'] = status
            
            product_list.append(product_info)
        
        return product_list
    
    except Exception as e:
        print(f"오류 발생: {e}")
        return []
    
    finally:
        driver.quit()

# 이전 제품 목록을 불러오는 함수
def load_previous_products():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return []

# 현재 제품 목록을 저장하는 함수
def save_current_products(products):
    with open(DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(products, file, ensure_ascii=False, indent=4)

# 제품 변동 사항 감지
def detect_changes(new, old):
    added = list(set(tuple(p.items()) for p in new) - set(tuple(p.items()) for p in old))
    removed = list(set(tuple(p.items()) for p in old) - set(tuple(p.items()) for p in new))
    return added, removed

# 이메일 알림 전송 함수
def send_email_alert(added, removed):
    subject = "제품 변경 알림"
    body = ""
    
    if added:
        body += "새로운 제품이 추가되었습니다:\n" + "\n".join([f"{dict(item)}" for item in added]) + "\n\n"
    if removed:
        body += "다음 제품이 삭제되었습니다:\n" + "\n".join([f"{dict(item)}" for item in removed]) + "\n\n"
    
    if not body:
        body = "변경 사항이 없습니다."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("이메일 알림이 성공적으로 전송되었습니다.")
    
    except Exception as e:
        print(f"이메일 전송 실패: {e}")

# 업데이트 확인 함수
def check_for_updates(selected_category_value):
    print(f"카테고리 '{selected_category_value}'의 제품 목록을 확인하는 중...")
    current_products = get_product_list(selected_category_value)
    
    if not current_products:
        print("제품 목록을 가져오지 못했습니다.")
        return
    
    # 현재 카테고리의 제품 목록 출력
    print("\n현재 카테고리의 제품 목록:")
    for product in current_products:
        print(product)
    
    previous_products = load_previous_products()
    added, removed = detect_changes(current_products, previous_products)
    
    if added or removed:
        print("\n변경 사항이 감지되었습니다.")
        print("추가된 제품:", added)
        print("삭제된 제품:", removed)
        send_email_alert(added, removed)
        save_current_products(current_products)
    else:
        print("변경 사항이 없습니다.")

def scroll_to_load_all_products(driver):
    # 현재 페이지의 높이를 가져옵니다.
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # 페이지 끝까지 스크롤합니다.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # 페이지 로딩을 기다립니다.
        time.sleep(2)
        
        # 새로 로드된 페이지의 높이를 가져옵니다.
        new_height = driver.execute_script("return document.body.scrollHeight")

        # 새로 로드된 높이가 이전 높이와 같다면, 스크롤이 끝난 것이므로 반복을 중단합니다.
        if new_height == last_height:
            break

        last_height = new_height

"""
# 메인 함수
def main():
    # 카테고리 선택
    selected_category_value, selected_category_name = select_category()
    
    # 현재 제품 목록을 출력
    # 출력 예시
    current_products = get_product_list(selected_category_value)
    for idx, product in enumerate(current_products, start=1):
        print(f"{idx}.")
        for key, value in product.items():
            print(f"{key}: {value}")
        print("\n" + "-" * 40 + "\n")  # 각 제품을 구분하는 줄바꿈과 구분선 추가


    
    # 첫 실행 시 현재 제품 목록 저장
    if not os.path.exists(DATA_FILE):
        save_current_products(current_products)
        print("초기 제품 목록을 저장했습니다.")
    
    # 주기적으로 제품 목록을 확인
    schedule.every(CHECK_INTERVAL).seconds.do(check_for_updates, selected_category_value)
    
    print(f"\n'{selected_category_name}' 카테고리 모니터링을 시작합니다...")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()

"""

# GUI 창을 띄우는 함수
def start_gui():
    # 창 생성
    root = tk.Tk()
    root.title("제품 모니터링 프로그램")
    root.geometry("600x600")

    # 카테고리 이름과 코드 매핑
    categories = {
        '0201': '화장품/미용',
        '0202': '패션 의류',
        '0203': '식품',
        '0204': '가구/인테리어',
        '0205': '출산/육아',
        '0206': '반려동물',
        '0207': '디지털/가전',
        '0208': '생활/건강',
        '0209': '스포츠/취미/레저',
        '0210': '건강기능식품',
        '0211': '자동차',
        '0212': '패션 잡화',
        '0299': '기타'
    }

    def run_program():
        selected_category_name = category_var.get()
        # 카테고리 이름에 해당하는 코드를 가져옴
        selected_category_value = next(key for key, value in categories.items() if value == selected_category_name)
        if selected_category_value:
            output_text.insert(tk.END, f"\n카테고리 '{selected_category_name}' 선택됨\n")
            # 웹 스크래핑 작업을 시작하는 함수 호출 (멀티스레딩으로 실행)
            threading.Thread(target=scrape_products, args=(selected_category_value,)).start()

    def scrape_products(selected_category_value):
        # 웹 스크래핑 함수 호출 후 결과를 출력
        current_products = get_product_list(selected_category_value)
        for idx, product in enumerate(current_products, start=1):
            output_text.insert(tk.END, f"\n{idx}.\n")
            for key, value in product.items():
                output_text.insert(tk.END, f"{key}: {value}\n")
            output_text.insert(tk.END, "\n" + "-" * 40 + "\n")
    
    # 프로그램 시작 버튼
    start_button = tk.Button(root, text="프로그램 시작", command=run_program)
    start_button.pack(pady=10)

    # 카테고리 선택 라벨
    category_label = tk.Label(root, text="카테고리를 선택하세요:")
    category_label.pack()

    # 카테고리 선택 콤보박스 (카테고리 이름을 보여줌)
    category_var = tk.StringVar()
    category_combo = ttk.Combobox(root, textvariable=category_var)
    category_combo['values'] = list(categories.values())  # 사용자에게 이름만 보여줌
    category_combo.pack(pady=10)

    # 출력 창
    output_text = tk.Text(root, height=35, width=100)
    output_text.pack(pady=10)

    # 프로그램 창 실행
    root.mainloop()

# GUI 실행
start_gui()