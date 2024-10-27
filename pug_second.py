import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from tkinter import messagebox
from selenium.common.exceptions import NoSuchElementException

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

                # 카테고리 필드 포함하여 제품 정보 저장
                all_products.append({
                    "category": category_name,  # 추가된 category 필드
                    "status": status_text,
                    "title": product_name,
                    "actual_price": actual_price,
                    "price": original_price,
                    "purchase_location": purchase_location,
                    "features": features
                })

        # 모든 제품 스크래핑 완료 후 즉시 표시
        display_products(all_products)
        messagebox.showinfo("완료", "모든 제품 스크래핑이 완료되었습니다.")
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

    category_name = category_list[selected_index[0]]
    selected_status = [status for status, var in status_vars.items() if var.get()]
    selected_purchases = [purchase for purchase, var in purchase_vars.items() if var.get()]

    # 메모리에서 필터링
    filtered_products = [
        product for product in all_products
        if (category_name == "전체" or product["category"] == category_name)
        and product["status"] in selected_status
        and product["purchase_location"] in selected_purchases
    ]

    display_products(filtered_products)


    # 선택한 카테고리, 상태, 구매처 가져오기
    category_name = category_list[selected_index[0]]
    selected_status = [status for status, var in status_vars.items() if var.get()]
    selected_purchases = [purchase for purchase, var in purchase_vars.items() if var.get()]

    # 필터링 조건: 선택한 카테고리, 상태, 구매처에 따라 필터링
    filtered_products = [
        product for product in all_products  # all_products에 있는 제품을 필터링
        if (category_name == "전체" or product["category"] == category_name) and product["status"] in selected_status and product["purchase_location"] in selected_purchases
    ]

    # 필터링 결과를 product_text에 표시
    display_products(filtered_products)


    # 선택한 필터 조건 가져오기
    category_name = category_list[selected_index[0]]
    selected_status = [status for status, var in status_vars.items() if var.get()]
    selected_purchases = [purchase for purchase, var in purchase_vars.items() if var.get()]

    # 메모리에 저장된 all_products에서 필터링
    filtered_products = [
        product for product in all_products
        if (category_name == "전체" or category_name in product["title"])
        and product["status"] in selected_status
        and product["purchase_location"] in selected_purchases
    ]

    # 필터링된 제품 목록 표시
    display_products(filtered_products)


# 필터링된 제품을 텍스트 영역에 출력
def display_products(products):
    product_text.delete(1.0, tk.END)
    product_text.tag_configure("red", foreground="red")
    product_text.tag_configure("blue", foreground="blue")
    
    for index, product in enumerate(products, start=1):
        if product["status"] == "마감 임박":
            status_color = "red"
        elif product["status"] in ["오픈 예정", "재오픈 예정"]:
            status_color = "blue"
        else:
            status_color = None

        product_text.insert(tk.END, f"{index}. 제품명: {product['title']}\n")
        product_text.insert(tk.END, "상태: ")
        if status_color:
            product_text.insert(tk.END, f"{product['status']}\n", status_color)
        else:
            product_text.insert(tk.END, f"{product['status']}\n")
        product_text.insert(tk.END, f"실제 구매가: {product['actual_price']}\n")
        product_text.insert(tk.END, f"가격: {product['price']}\n")
        product_text.insert(tk.END, f"구매처: {product['purchase_location']}\n")
        product_text.insert(tk.END, f"특징: {product['features']}\n\n")

# 주기적으로 업데이트하여 새로운 제품 목록과 변경 사항 반영
def update_products_periodically():
    scrape_all_products()  # 모든 카테고리 제품을 스크래핑하여 업데이트
    current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    update_log_text.insert(tk.END, f"업데이트 완료: {current_time}\n")
    update_log_text.see(tk.END)
    global update_job
    update_job = root.after(300000, update_products_periodically)  # 5분마다 업데이트

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

# GUI 설정
root = tk.Tk()
root.title("카테고리 선택 및 제품 정보 가져오기")
root.geometry("1200x900")

selection_frame = tk.Frame(root)
selection_frame.pack()

category_label = tk.Label(selection_frame, text="카테고리를 선택하세요:")
category_label.grid(row=0, column=0, sticky="w")

category_list = fetch_categories()

category_listbox = tk.Listbox(selection_frame, height=10)
category_listbox.grid(row=1, column=0, padx=10, pady=10)
for category in category_list:
    category_listbox.insert(tk.END, category)
category_listbox.select_set(0)

status_frame = tk.Frame(selection_frame)
status_frame.grid(row=1, column=1, padx=10)
status_label = tk.Label(status_frame, text="원하는 상태를 선택하세요:")
status_label.pack(anchor="w")
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

purchase_frame = tk.Frame(selection_frame)
purchase_frame.grid(row=1, column=2, padx=10)
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

# 필터링 및 스크래핑 버튼을 포함할 프레임 생성
button_frame = tk.Frame(selection_frame)
button_frame.grid(row=1, column=3, rowspan=2, padx=10, pady=5, sticky="ns")

# 필터링 및 스크래핑 버튼 배치
filter_button = tk.Button(button_frame, text="필터링", command=filter_products, width=15, height=2)
filter_button.grid(row=1, column=0, pady=(0, 5))

scraping_button = tk.Button(button_frame, text="스크래핑", command=scrape_all_products, width=15, height=2)
scraping_button.grid(row=2, column=0)

# 메인 키워드 및 업데이트 컨트롤 프레임
main_control_frame = tk.Frame(root)
main_control_frame.pack(pady=5)

# 키워드 입력 및 필터링 프레임
keyword_frame = tk.Frame(main_control_frame)
keyword_frame.grid(row=0, column=0, padx=10, sticky="nw")
keyword_label = tk.Label(keyword_frame, text="키워드를 입력하세요:")
keyword_label.grid(row=0, column=0, sticky="w")
keyword_entry = tk.Entry(keyword_frame, width=30)
keyword_entry.grid(row=0, column=1, padx=5, sticky="w")

filter_button = tk.Button(keyword_frame, text="키워드 필터링", command=apply_keyword_filter)
filter_button.grid(row=0, column=2, padx=(5, 2))
reset_button = tk.Button(keyword_frame, text="초기화", command=reset_keyword_filter)
reset_button.grid(row=0, column=3, padx=(2, 5))

# 키워드 목록창과 추가/삭제 버튼
keyword_listbox = tk.Listbox(keyword_frame, height=5, width=30, selectmode=tk.SINGLE)
keyword_listbox.grid(row=1, column=1, pady=5)

button_frame = tk.Frame(keyword_frame)
button_frame.grid(row=1, column=2, columnspan=2, pady=5, sticky="w")

add_keyword_button = tk.Button(button_frame, text="추가", command=add_keyword)
add_keyword_button.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))
delete_keyword_button = tk.Button(button_frame, text="삭제", command=delete_keyword)
delete_keyword_button.grid(row=1, column=0, sticky="w", padx=5)

update_button_frame = tk.Frame(main_control_frame)
update_button_frame.grid(row=0, column=1, padx=10, sticky="ne")
start_button = tk.Button(update_button_frame, text="업데이트 시작", command=start_updates, width=15, height=2)
start_button.pack(pady=(0, 5))
stop_button = tk.Button(update_button_frame, text="업데이트 정지", command=stop_updates, width=15, height=2, state="disabled")
stop_button.pack()

# 텍스트 영역 설정
text_frame = tk.Frame(root)
text_frame.pack()

product_text = tk.Text(text_frame, height=40, width=70, wrap="word")
scrollbar = tk.Scrollbar(text_frame, command=product_text.yview)
product_text.configure(yscrollcommand=scrollbar.set)
product_text.pack(side="left")
scrollbar.pack(side="right", fill="y")

update_log_text = tk.Text(text_frame, height=40, width=50, wrap="word")
update_log_text.pack(side="right", padx=10)

root.mainloop()
