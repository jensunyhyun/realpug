import time
import urllib.request
import io
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from tkinter import messagebox
from tkinter import font
from selenium.common.exceptions import NoSuchElementException
from PIL import Image, ImageTk
import requests
from io import BytesIO
import urllib.request

# 업데이트 시간별 제품 저장 구조
update_records = {}  # {업데이트 완료 시간: 제품 목록}

# URL 설정
url = "https://pugshop.co.kr/main-page/?tab=shopping"
all_products = []  # 모든 제품을 저장할 메모리 공간
update_job = None

# 스크롤 함수
def scroll_to_load_all(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# 카테고리 목록
def fetch_categories():
    return ["전체", "화장품/미용", "패션 의류", "식품", "가구/인테리어", "출산/육아", "반려동물", "디지털/가전", "생활/건강", "스포츠/취미/레저", "건강기능식품", "자동차", "패션 잡화", "기타"]

# 요소 찾기 함수
def find_element_if_exists(element, by, value):
    try:
        return element.find_element(by, value)
    except NoSuchElementException:
        return None
    
def fetch_products_by_category(category_name="전체"):
    driver = webdriver.Chrome()
    try:
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.category-bar-container .category-btn'))
        )
        category_buttons = driver.find_elements(By.CSS_SELECTOR, '.category-bar-container .category-btn')

        for button in category_buttons:
            if category_name == "전체" or category_name in button.text:
                driver.execute_script("arguments[0].click();", button)
                time.sleep(5)
                break

        scroll_to_load_all(driver)
        product_elements = driver.find_elements(By.CSS_SELECTOR, '.campaign-card')

        product_list = []
        for product in product_elements:
            # 상태 및 다른 필드 수집
            if product.find_elements(By.CSS_SELECTOR, '.close-text.close'):
                status_text = "모집 마감"
            elif product.find_elements(By.CSS_SELECTOR, '.close-text.pause'):
                status_text = "재오픈 예정"
            elif product.find_elements(By.CSS_SELECTOR, '.state-badge.open .state-name'):
                status_text = "오픈 예정"
            elif product.find_elements(By.CSS_SELECTOR, '.state-badge.deadlineImminent .state-name'):
                status_text = "마감 임박"
            else:
                status_text = "진행중"

            product_name_element = find_element_if_exists(product, By.CSS_SELECTOR, 'div.text-md')
            product_name = product_name_element.text.strip() if product_name_element else "제품명 없음"

            actual_price_element = find_element_if_exists(product, By.CSS_SELECTOR, 'span[style*="color: rgb(79, 21, 255)"]')
            actual_price = actual_price_element.text.strip() if actual_price_element else "실제 구매가 없음"

            original_price_element = find_element_if_exists(product, By.CSS_SELECTOR, 'span.text-xs.text-gray-4.font-bold.md\\:ml-2\\.5.line-through.leading-\\[18px\\].tracking-tight')
            original_price = original_price_element.text.strip() if original_price_element else "가격 정보 없음"

            tags = product.find_elements(By.CSS_SELECTOR, 'span.ant-tag')
            if tags:
                purchase_location = tags[0].text.strip()
                features = ', '.join(tag.text.strip() for tag in tags[1:])
            else:
                purchase_location = "구매처 정보 없음"
                features = "특징 정보 없음"

            # 카테고리 필드 추가
            product_list.append({
                "category": category_name,  # 카테고리를 저장
                "status": status_text,
                "title": product_name,
                "actual_price": actual_price,
                "price": original_price,
                "purchase_location": purchase_location,
                "features": features
            })

        return product_list

    finally:
        driver.quit()


# 스크래핑 기능 - 모든 카테고리 제품 스크래핑
def scrape_all_products():
    driver = webdriver.Chrome()
    try:
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.category-bar-container .category-btn'))
        )
        category_buttons = driver.find_elements(By.CSS_SELECTOR, '.category-bar-container .category-btn')

        all_products.clear()  # 이전 스크래핑 결과 초기화

        for button in category_buttons:
            category_name = button.text.strip()  # 각 버튼의 카테고리 이름 추출
            driver.execute_script("arguments[0].click();", button)
            time.sleep(5)

            scroll_to_load_all(driver)
            product_elements = driver.find_elements(By.CSS_SELECTOR, '.campaign-card')

            for product in product_elements:
                # 상태 및 기타 필드 수집
                if product.find_elements(By.CSS_SELECTOR, '.close-text.close'):
                    status_text = "모집 마감"
                elif product.find_elements(By.CSS_SELECTOR, '.close-text.pause'):
                    status_text = "재오픈 예정"
                elif product.find_elements(By.CSS_SELECTOR, '.state-badge.open .state-name'):
                    status_text = "오픈 예정"
                elif product.find_elements(By.CSS_SELECTOR, '.state-badge.deadlineImminent .state-name'):
                    status_text = "마감 임박"
                else:
                    status_text = "진행중"

                product_name_element = find_element_if_exists(product, By.CSS_SELECTOR, 'div.text-md')
                product_name = product_name_element.text.strip() if product_name_element else "제품명 없음"

                actual_price_element = find_element_if_exists(product, By.CSS_SELECTOR, 'span[style*="color: rgb(79, 21, 255)"]')
                actual_price = actual_price_element.text.strip() if actual_price_element else "실제 구매가 없음"

                original_price_element = find_element_if_exists(product, By.CSS_SELECTOR, 'span.text-xs.text-gray-4.font-bold.md\\:ml-2\\.5.line-through.leading-\\[18px\\].tracking-tight')
                original_price = original_price_element.text.strip() if original_price_element else "가격 정보 없음"

                tags = product.find_elements(By.CSS_SELECTOR, 'span.ant-tag')
                if tags:
                    purchase_location = tags[0].text.strip()
                    features = ', '.join(tag.text.strip() for tag in tags[1:])
                else:
                    purchase_location = "구매처 정보 없음"
                    features = "특징 정보 없음"
                
                # 이미지 URL 가져오기
                img_element = find_element_if_exists(product, By.CSS_SELECTOR, 'img')
                img_url = img_element.get_attribute('src') if img_element else None

                # 카테고리 필드 포함하여 제품 정보 저장
                all_products.append({
                    "category": category_name,
                    "status": status_text,
                    "title": product_name,
                    "actual_price": actual_price,
                    "price": original_price,
                    "purchase_location": purchase_location,
                    "features": features,
                    "img_url": img_url  # 이미지 URL 필드 추가
                })

        # 모든 제품 스크래핑 완료 후 즉시 표시
        display_products(all_products)
        #messagebox.showinfo("완료", "모든 제품 스크래핑이 완료되었습니다.")
    finally:
        driver.quit()


# 상태 정보 추출 함수
def get_status(product):
    if product.find_elements(By.CSS_SELECTOR, '.close-text.close'):
        return "모집 마감"
    elif product.find_elements(By.CSS_SELECTOR, '.close-text.pause'):
        return "재오픈 예정"
    elif product.find_elements(By.CSS_SELECTOR, '.state-badge.open .state-name'):
        return "오픈 예정"
    elif product.find_elements(By.CSS_SELECTOR, '.state-badge.deadlineImminent .state-name'):
        return "마감 임박"
    else:
        return "진행중"

# 제품명 추출 함수
def get_product_name(product):
    product_name_element = find_element_if_exists(product, By.CSS_SELECTOR, 'div.text-md')
    return product_name_element.text.strip() if product_name_element else "제품명 없음"

# 실제 구매가 추출 함수
def get_actual_price(product):
    actual_price_element = find_element_if_exists(product, By.CSS_SELECTOR, 'span[style*="color: rgb(79, 21, 255)"]')
    return actual_price_element.text.strip() if actual_price_element else "실제 구매가 없음"

# 원래 가격 추출 함수
def get_original_price(product):
    original_price_element = find_element_if_exists(product, By.CSS_SELECTOR, 'span.text-xs.text-gray-4.font-bold.md\\:ml-2\\.5.line-through.leading-\\[18px\\].tracking-tight')
    return original_price_element.text.strip() if original_price_element else "가격 정보 없음"

# 구매처 및 특징 태그 추출 함수
def get_tags(product):
    tags = product.find_elements(By.CSS_SELECTOR, 'span.ant-tag')
    if tags:
        purchase_location = tags[0].text.strip()  # 첫 번째 태그는 구매처
        features = ', '.join(tag.text.strip() for tag in tags[1:])  # 나머지 태그는 특징
    else:
        purchase_location = "구매처 정보 없음"
        features = "특징 정보 없음"
    return purchase_location, features
    
def filter_products():
    selected_index = category_listbox.curselection()
    if not selected_index:
        messagebox.showwarning("카테고리 선택", "카테고리를 선택하세요!")
        return

    # 선택한 필터 조건 불러오기
    category_name = category_list[selected_index[0]]
    selected_status = [status for status, var in status_vars.items() if var.get()]
    selected_purchases = [purchase for purchase, var in purchase_vars.items() if var.get()]

    # 필터링 조건에 따라 제품 필터링
    filtered_products = [
        product for product in all_products
        if (category_name == "전체" or category_name == product["category"])
        and product["status"] in selected_status
        and product["purchase_location"] in selected_purchases
    ]

    print(f"필터링된 제품 개수: {len(filtered_products)}")  # 필터링 후 제품 개수 확인
    display_products(filtered_products)

# 제품 목록을 표시하고 텍스트 클릭 이벤트 추가
def display_products(products):
    product_listbox.delete(0, tk.END)  # 기존 목록 삭제
    
    for index, product in enumerate(products, start=1):
        # 제품 정보 문자열 생성
        product_info = (
            f"{index}. 제품명: {product['title']} | 상태: {product['status']} | "
            f"실제 구매가: {product['actual_price']} | 가격: {product['price']} | "
            f"구매처: {product['purchase_location']} | 특징: {product['features']}"
        )
        
        # 제품 상태에 따라 색상 설정
        if product["status"] == "마감 임박":
            color = "red"
        elif product["status"] in ["오픈 예정", "재오픈 예정"]:
            color = "blue"
        else:
            color = "black"  # 기본 색상
        
        # Listbox에 제품 정보 추가
        product_listbox.insert(tk.END, product_info)
        product_listbox.itemconfig(tk.END, foreground=color)  # 항목 색상 설정

    # 제품 정보 클릭 이벤트 바인딩
    product_listbox.bind("<<ListboxSelect>>", on_product_select)


# 제품 정보 선택 시 호출되는 함수 업데이트
def on_product_select(event):
    # Listbox에서 선택된 항목 확인
    selected_index = product_listbox.curselection()
    if not selected_index:
        return

    # 선택된 제품의 첫 번째 줄(예: "1. 제품명: ...")의 인덱스를 기준으로 항목 묶기
    product_start_index = selected_index[0] // 7 * 7
    selected_product = {
        "title": product_listbox.get(product_start_index).split(": ", 1)[1],
        "status": product_listbox.get(product_start_index + 1).split(": ", 1)[1],
        "actual_price": product_listbox.get(product_start_index + 2).split(": ", 1)[1],
        "price": product_listbox.get(product_start_index + 3).split(": ", 1)[1],
        "purchase_location": product_listbox.get(product_start_index + 4).split(": ", 1)[1],
        "features": product_listbox.get(product_start_index + 5).split(": ", 1)[1],
        "image_url": product_listbox.get(product_start_index + 6).split(": ", 1)[1]  # 이미지 URL
    }

    # 선택된 제품의 이미지 로드 함수 호출
    load_image(selected_product["image_url"])

    # 선택된 제품의 정보만 info_text에 표시
    info_text.delete("1.0", tk.END)  # 이전 내용 삭제
    info_text.tag_configure("red", foreground="red")
    info_text.tag_configure("blue", foreground="blue")
    
    # 제품 정보를 info_text에 추가
    info_text.insert(tk.END, f"제품명: {selected_product['title']}\n")
    status_color = "red" if selected_product["status"] == "마감 임박" else "blue" if selected_product["status"] in ["오픈 예정", "재오픈 예정"] else "black"
    info_text.insert(tk.END, f"상태: {selected_product['status']}\n", (status_color,))
    info_text.insert(tk.END, f"실제 구매가: {selected_product['actual_price']}\n")
    info_text.insert(tk.END, f"가격: {selected_product['price']}\n")
    info_text.insert(tk.END, f"구매처: {selected_product['purchase_location']}\n")
    info_text.insert(tk.END, f"특징: {selected_product['features']}\n")

# 주기적으로 업데이트하여 새로운 제품 목록과 변경 사항 반영
def update_products_periodically():
    global all_products
    
    # 스크래핑을 통해 제품 목록 업데이트
    scrape_all_products()  # scrape_all_products 함수가 all_products를 업데이트함
    
    # 현재 시간을 기록하고 업데이트된 제품 목록을 저장
    current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    update_records[current_time] = list(all_products)  # 현재 제품 목록 복사하여 저장

    # 업데이트 로그에 기록 추가
    update_log_text.configure(state="normal")
    update_log_text.insert(tk.END, f"업데이트 완료: {current_time}\n")
    update_log_text.configure(state="disabled")
    update_log_text.see(tk.END)

    # 다음 5분 단위의 시간을 계산
    now = datetime.now()
    next_interval = (now + timedelta(minutes=5)).replace(second=0, microsecond=0)
    next_interval = next_interval - timedelta(minutes=now.minute % 5)

    # 다음 업데이트까지 남은 시간 계산
    delay = (next_interval - now).total_seconds()

    # 5분 단위로 반복 실행
    update_job = root.after(int(delay * 1000), update_products_periodically)

# 업데이트 시작과 정지
def start_updates():
    global update_job
    if update_job is None:
        update_products_periodically()
        start_button.config(state="disabled")
        stop_button.config(state="normal")

def stop_updates():
    global update_job
    if update_job:
        root.after_cancel(update_job)
        update_job = None
        start_button.config(state="normal")
        stop_button.config(state="disabled")

# 업데이트 로그에서 특정 항목을 클릭했을 때 해당 제품 목록을 불러오는 함수
def on_update_time_select(event):
    try:
        # 선택한 업데이트 시간을 읽어옴
        selected_time = update_log_text.get("insert linestart", "insert lineend").strip("업데이트 완료: ")
        
        # 해당 시간의 제품 목록을 product_listbox에 표시
        if selected_time in update_records:
            display_products(update_records[selected_time])
        else:
            messagebox.showerror("오류", "선택한 시간에 대한 업데이트 정보를 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

# 키워드 필터링 함수
def apply_keyword_filter():
    keywords = [keyword_listbox.get(i) for i in range(keyword_listbox.size())]
    filtered_products = [
        product for product in all_products
        if any(keyword.lower() in product["title"].lower() for keyword in keywords)
    ]
    display_products(filtered_products)

def reset_keyword_filter():
    keyword_listbox.delete(0, tk.END)
    display_products(all_products)

# 키워드 추가 및 삭제 함수
def add_keyword():
    keyword = keyword_entry.get().strip()
    if keyword and keyword not in keyword_listbox.get(0, tk.END):
        keyword_listbox.insert(tk.END, keyword)
        keyword_entry.delete(0, tk.END)

def delete_keyword():
    selected_index = keyword_listbox.curselection()
    if selected_index:
        keyword_listbox.delete(selected_index)

def load_image(image_url):
    # 이미지 창 초기화
    for widget in image_frame.winfo_children():
        widget.destroy()

    # 이미지 URL이 있는 경우에만 로드
    if image_url:
        try:
            # URL에서 이미지 데이터 가져오기
            response = requests.get(image_url)
            img_data = response.content
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((250, 250), Image.LANCZOS)  # 이미지 크기 조정
            photo = ImageTk.PhotoImage(img)

            # 이미지 라벨 생성 및 표시
            image_label = tk.Label(image_frame, image=photo)
            image_label.image = photo  # 참조 유지
            image_label.pack()
        except Exception as e:
            print(f"이미지 불러오기 실패: {e}")  # 콘솔에 오류 메시지 출력
            error_label = tk.Label(image_frame, text="이미지 불러오기 실패")
            error_label.pack()
    else:
        # 이미지 URL이 없는 경우 메시지 표시
        error_label = tk.Label(image_frame, text="이미지가 없습니다")
        error_label.pack()

def on_product_select(event):
    # 기본 텍스트 제거 후 새로운 텍스트 추가
    info_text.configure(state="normal")  # 텍스트를 변경할 수 있도록 해제
    info_text.delete("1.0", tk.END)      # 기존 텍스트 삭제

    # Listbox에서 선택된 항목 확인
    selected_index = product_listbox.curselection()
    if not selected_index:
        return

    # 선택된 제품 정보 가져오기
    selected_product = all_products[selected_index[0]]

    # 선택된 제품의 이미지 로드 함수 호출
    load_image(selected_product["img_url"])

    # 제품 정보 텍스트를 구성하여 info_text에 표시
    info_text.delete("1.0", tk.END)  # 이전 내용 삭제
    info_text.tag_configure("red", foreground="red")
    info_text.tag_configure("blue", foreground="blue")
    
    # 제품 정보를 색상 태그와 함께 삽입
    info_text.insert(tk.END, f"제품명: {selected_product['title']}\n")
    info_text.insert(tk.END, "상태: ", ("status_color",))

    # 상태에 따라 색상 적용
    status_color = "red" if selected_product["status"] == "마감 임박" else "blue" if selected_product["status"] in ["오픈 예정", "재오픈 예정"] else None
    if status_color:
        info_text.insert(tk.END, f"{selected_product['status']}\n", status_color)
    else:
        info_text.insert(tk.END, f"{selected_product['status']}\n")
    
    info_text.insert(tk.END, f"실제 구매가: {selected_product['actual_price']}\n")
    info_text.insert(tk.END, f"가격: {selected_product['price']}\n")
    info_text.insert(tk.END, f"구매처: {selected_product['purchase_location']}\n")
    info_text.insert(tk.END, f"특징: {selected_product['features']}\n")

# GUI 설정
root = tk.Tk()
root.tk.call('tk', 'scaling', 1.5)  # 배율을 2배로 높이기
root.title("제품 목록 및 이미지 표시")
root.geometry("1100x900")

outer_frame = tk.Frame(root, width=300, height=200)
outer_frame.pack(padx=10, pady=10, fill="both", expand=True)
outer_frame.grid_propagate(False)  # 내부 위젯에 의해 크기가 변경되지 않도록 설정

# outer_frame에 좌우 여백을 주어 중앙 정렬 유지
outer_frame.grid_rowconfigure(0, weight=1)
outer_frame.grid_columnconfigure(0, weight=1)

# top_frame - center frame, update log text
top_frame = tk.Frame(outer_frame, width=900, height=330)
top_frame.grid(row=0, column=0, sticky="nsew")
top_frame.grid_propagate(False)  # 내부 위젯 크기에 의해 top_frame 크기가 변경되지 않도록 설정

# top_frame의 행과 열 가중치 설정
top_frame.grid_rowconfigure(0, weight=1)
top_frame.grid_columnconfigure(0, weight=1)  # center_frame이 0열에서 중앙에 위치
top_frame.grid_columnconfigure(1, weight=0)  # update_log_text가 1열에서 중앙에 위치

# 고정 크기의 bottom_frame 생성 및 grid 배치
bottom_frame = tk.Frame(outer_frame, width=5, height=150)
bottom_frame.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")  # pady를 0으로 설정
bottom_frame.grid_propagate(False)

# top_frame 안에 0열 center_frame, 1열 update_log_text 배치
center_frame = tk.Frame(top_frame, bg="lightpink")
center_frame.grid(row=0, column=0, sticky="nsew")
center_frame.grid_rowconfigure(0, weight=1)  # selection_frame이 0행에서 확장
center_frame.grid_rowconfigure(1, weight=1)  # main_control_frame이 1행에서 확장
center_frame.grid_columnconfigure(0, weight=1)  # 열 중앙 정렬 유지

# selection_frame 설정
selection_frame = tk.Frame(center_frame)
selection_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

# selection_frame 내부 열 가중치 설정
selection_frame.grid_columnconfigure(0, weight=1)  # category 열
selection_frame.grid_columnconfigure(1, weight=1)  # status 열
selection_frame.grid_columnconfigure(2, weight=1)  # purchase 열
selection_frame.grid_columnconfigure(3, weight=1)  # button 열

# category_label과 category_listbox를 같은 열에 배치
category_label = tk.Label(selection_frame, text="카테고리를 선택하세요:")
category_label.grid(row=0, column=0, sticky="nw", pady=0)

category_listbox = tk.Listbox(selection_frame, height=15)
category_listbox.grid(row=1, column=0, sticky="nsew")  # nsew로 확장
category_list = fetch_categories()
for category in category_list:
    category_listbox.insert(tk.END, category)
category_listbox.select_set(0)

# 상태 선택 프레임
status_frame = tk.Frame(selection_frame)
status_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 5))  # 좌우 여백 최소화
status_label = tk.Label(status_frame, text="원하는 상태를 선택하세요:")
status_label.pack(anchor="w", pady=(0, 5))
status_vars = {
    "진행중": tk.BooleanVar(value=True),
    "마감 임박": tk.BooleanVar(value=True),
    "오픈 예정": tk.BooleanVar(value=True),
    "재오픈 예정": tk.BooleanVar(value=True),
    "모집 마감": tk.BooleanVar(value=True)
}
for status, var in status_vars.items():
    cb = tk.Checkbutton(status_frame, text=status, variable=var)
    cb.pack(anchor="w")

# 구매처 선택 프레임
purchase_frame = tk.Frame(selection_frame)
purchase_frame.grid(row=1, column=2, sticky="nsew", padx=(5, 5))  # 좌우 여백 최소화
purchase_label = tk.Label(purchase_frame, text="원하는 구매처를 선택하세요:")
purchase_label.pack(anchor="w")
purchase_vars = {
    "쿠팡": tk.BooleanVar(value=True),
    "온라인편집샵": tk.BooleanVar(value=True),
    "네이버쇼핑": tk.BooleanVar(value=True),
    "드럭스토어": tk.BooleanVar(value=True)
}
for purchase, var in purchase_vars.items():
    cb = tk.Checkbutton(purchase_frame, text=purchase, variable=var)
    cb.pack(anchor="w")

# 필터링 및 스크래핑 버튼 프레임
button_frame = tk.Frame(selection_frame)
button_frame.grid(row=1, column=3, sticky="nsew")  # 버튼 프레임을 최대한 확장

# 필터링 및 스크래핑 버튼 배치
filter_button = tk.Button(button_frame, text="필터링", command=filter_products, width=15, height=2)
filter_button.grid(row=0, column=0, pady=(0, 5))

scraping_button = tk.Button(button_frame, text="스크래핑", command=scrape_all_products, width=15, height=2)
scraping_button.grid(row=1, column=0)

# main_control_frame 배치와 확장 설정
main_control_frame = tk.Frame(center_frame)
main_control_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

# main_control_frame 내부 구성 설정
main_control_frame.grid_rowconfigure(1, weight=1)  # keyword_listbox가 있는 행 확장 가능
main_control_frame.grid_columnconfigure(0, weight=1)

# 키워드 입력 및 필터링 프레임
keyword_frame = tk.Frame(main_control_frame, width=400, height=300)
keyword_frame.grid(row=0, column=0, padx=10, sticky="nw")
keyword_frame.grid_columnconfigure(1, weight=1)  # Entry와 Listbox 확장 설정

# 키워드 입력 라벨과 엔트리
keyword_label = tk.Label(keyword_frame, text="키워드를 입력하세요:", width=40)
keyword_label.grid(row=0, column=0, sticky="w")
keyword_entry = tk.Entry(keyword_frame, width=30)
keyword_entry.grid(row=0, column=1, padx=0, sticky="w")

# 필터링과 초기화 버튼
filter_button = tk.Button(keyword_frame, text="필터링", command=apply_keyword_filter)
filter_button.grid(row=0, column=2, padx=(5, 2))
reset_button = tk.Button(keyword_frame, text="초기화", command=reset_keyword_filter)
reset_button.grid(row=0, column=3, padx=(2, 5))

# keyword_listbox를 담을 Frame 생성 (스크롤바와 함께 배치하기 위함)
keyword_listbox_frame = tk.Frame(keyword_frame, height=100)
keyword_listbox_frame.grid(row=1, column=1, pady=5, sticky="nsew")  # (1,1) 위치 설정
keyword_frame.grid_rowconfigure(1, weight=1)  # Listbox Frame이 확장되도록 설정
keyword_frame.grid_columnconfigure(1, weight=1)  # 열 확장 설정

# Frame 내부에 Listbox와 Scrollbar 생성
keyword_listbox = tk.Listbox(keyword_listbox_frame, height=15, width=30, selectmode=tk.SINGLE)
keyword_listbox.pack(side="left", fill="both", expand=True)

# Scrollbar 설정 및 Listbox에 연결
scrollbar = tk.Scrollbar(keyword_listbox_frame, orient="vertical", command=keyword_listbox.yview)
scrollbar.pack(side="right", fill="y")  # 오른쪽에 스크롤바 배치
keyword_listbox.configure(yscrollcommand=scrollbar.set)

# keyword_listbox_frame이 Listbox와 Scrollbar를 담을 공간을 확장
keyword_listbox_frame.pack_propagate(False)

#추가/삭제 버튼
button_frame = tk.Frame(keyword_frame)
button_frame.grid(row=1, column=2, pady=5, sticky="nw")

add_keyword_button = tk.Button(button_frame, text="추가", command=add_keyword)
add_keyword_button.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))
delete_keyword_button = tk.Button(button_frame, text="삭제", command=delete_keyword)
delete_keyword_button.grid(row=1, column=0, sticky="w", padx=5)

#업데이트 시작/정지 버튼
update_button_frame = tk.Frame(keyword_frame, bg="red")
update_button_frame.grid(row=0, column=4, padx=10, rowspan=2, sticky="ne")
start_button = tk.Button(update_button_frame, text="업데이트 시작", command=start_updates, width=15, height=2)
add_keyword_button.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))
start_button.pack(pady=(0, 5))
stop_button = tk.Button(update_button_frame, text="업데이트 정지", command=stop_updates, width=15, height=2, state="disabled")
stop_button.pack()

# 오른쪽 업데이트 로그 텍스트
update_log_text = tk.Text(top_frame, wrap="word", width=25, height=50)
update_log_text.grid(row=0, column=1, sticky="nsew", padx=(10,0), pady=(10, 180))
update_log_text.configure(state="disabled")  # 초기 비활성화 설정
update_log_text.grid_propagate(False)

# 업데이트 로그 클릭 이벤트 바인딩
update_log_text.bind("<Button-1>", on_update_time_select)

# 왼쪽 패널 생성 (이미지 프레임용)
left_panel = tk.Frame(bottom_frame, width=300, height=400)  # 원하는 고정 크기 지정
left_panel.pack(side="left", padx=10, pady=10, fill="y")
left_panel.pack_propagate(False)  # 내부 위젯 크기에 맞춰 확장되지 않도록 설정

# 이미지 표시 프레임 생성 및 배경색 설정
image_frame = tk.Frame(left_panel, bg="white", width=250, height=250)
image_frame.pack(anchor="n", pady=10)
image_frame.pack_propagate(False)  # 내부 요소 크기로 프레임 크기 변경 방지

# 이미지 레이블 생성
image_label = tk.Label(image_frame, bg="white")
image_label.pack()

# info_text 전용 폰트 설정 (기본 폰트를 사용하되 크기만 키움)
custom_font = font.nametofont("TkDefaultFont").copy()
custom_font.configure(size=11)  # 원하는 글씨 크기 설정

# 제품 정보 텍스트 출력 프레임 설정 (이미지 바로 아래에 위치)
info_text = tk.Text(left_panel, height=15, width=30, wrap="word")
info_text.pack(anchor="n", pady=10)  
info_text.insert("1.0", "========정보 없음========")  # 기본 텍스트 설정
info_text.configure(state="disabled", font=custom_font)  # 사용자 수정 방지

# 오른쪽 패널 생성 (제품 목록)
right_panel = tk.Frame(bottom_frame, width=600, height=400)  # 원하는 고정 크기 지정
right_panel.pack(side="left", padx=10, pady=10, fill="both", expand=True)
right_panel.pack_propagate(False)

# 텍스트 출력 위젯 대신 Listbox로 변경
product_listbox = tk.Listbox(right_panel, height=40, width=90) 
product_listbox.pack(side="left", fill="both", expand=True)
product_listbox.bind("<<ListboxSelect>>", on_product_select)

# 스크롤바 설정
scrollbar = tk.Scrollbar(right_panel, command=product_listbox.yview)
product_listbox.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="left", fill="y")

root.update_idletasks()  # 업데이트 후 정확한 위젯 크기 반환
print("Category Listbox Height:", category_listbox.winfo_height())
print("Status Frame Height:", status_frame.winfo_height())
print("Purchase Frame Height:", purchase_frame.winfo_height())
print("Button Frame Height:", button_frame.winfo_height())

print("Category Listbox Width:", category_listbox.winfo_width())
print("Status Frame Width:", status_frame.winfo_width())
print("Purchase Frame Width:", purchase_frame.winfo_width())
print("Button Frame Width:", button_frame.winfo_width())
print(category_listbox.winfo_width()+status_frame.winfo_width()+purchase_frame.winfo_width()+button_frame.winfo_width())

print("Top Frame Height:", top_frame.winfo_height())
print("Top Frame Width:", top_frame.winfo_width())

root.mainloop()
