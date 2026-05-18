from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
import html5lib

service = Service(r"C:\Users\ACER\Desktop\BTN_DataScience\chromedriver.exe") 

driver = webdriver.Chrome(service=service)

driver.get("https://moso.vn/tim-kiem-nha-dat/trang-thai-tin--dang-ban")

time.sleep(10)

propertys = []

for page in range(1,20):
    time.sleep(5)
    # Lấy danh sách link bất động sản
    links = driver.find_elements(By.XPATH, r'/html/body/section/section/section[2]/div/div[2]/div[2]//a')
    all_address = driver.find_elements(By.CSS_SELECTOR, ".text-base.tracking-\\[-0\\.32px\\].line-clamp-1.overflow-hidden")
    for i in range(len(links)):
        try:
            url = links[i].get_attribute('href')
            html = requests.get(url).text
            soup = BeautifulSoup(html, "html5lib")
            price = soup.find("h4", class_ ="font-bold text-black text-h3 pr-2 whitespace-nowrap").text
            ps = soup.find_all("p", class_="py-3 xs:py-2 flex justify-between items-center text-base xs:text-lg border-b border-gray-200")
            spans = {}
            for p in ps:
                key = p.find("span").get_text(strip=True)
                value = p.find("span",class_="font-bold").get_text(strip=True)
                spans[key] = value
            description = soup.find("div", class_="text-md xs:text-lg leading-7 text-black line-clamp-9 md:line-clamp-5").text
            width = spans.get("Chiều ngang", None)
            length = spans.get("Chiều dài", None)
            type = spans.get("Loại hình", None)
            area = spans.get("Diện tích đất công nhận", None)
            floors = spans.get("Số tầng", None)
            bathrooms = spans.get("Số phòng tắm", None)
            bedrooms = spans.get("Số phòng ngủ", None)
            legal_documents = spans.get("Giấy tờ pháp lý", None)
            furniture = spans.get("Nội thất", None)
            data = {
                "address": all_address[i].text,
                "price": price,
                "type": type,
                "width": width,
                "length": length,
                "area": area,
                "floors": floors,
                "bathrooms": bathrooms,
                "bedrooms": bedrooms,
                "legal_documents": legal_documents,
                "furniture": furniture,
                "description": description
            }
            print(data)
            propertys.append(data)
            print(f"Đã thu thập được {len(propertys)} bất động sản.")
        except Exception as e:
            continue
    time.sleep(5)
    # Ấn nút sang trang tiếp theo
    try:
        next_btn1 = driver.find_element(By.XPATH, "/html/body/section/section/section[2]/div/div[2]/div[3]/div/div/button[8]")
        next_btn1.click()
    except NoSuchElementException:
        try:
            next_btn2 = driver.find_element(By.XPATH, "/html/body/section/section/section[2]/div/div[2]/div[3]/div/div/button[7]")
            next_btn2.click()
        except NoSuchElementException:
            print("Không tìm thấy nút next nào cả.")
driver.quit()
# Lưu dữ liệu vào DataFrame và xuất ra file CSV
propertys_df = pd.DataFrame(propertys)
propertys_df.to_csv("propertys_moso.csv", index=False, encoding='utf-8-sig')
driver.quit()