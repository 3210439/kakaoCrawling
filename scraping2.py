from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import csv
import os
import re

# Function to normalize address
def normalize_address(address):
    # Remove "서울특별시", "부산광역시" etc., and extra spaces
    address = re.sub(r'^(서울특별시|부산광역시|경기도)\s*', '', address)
    address = re.sub(r'\s+', ' ', address).strip()
    return address

# Function to extract place ID from more_info URL
def get_place_id(more_info):
    # Extract place ID from URL like https://place.map.kakao.com/123456
    match = re.search(r'kakao\.com/(\d+)', more_info)
    return match.group(1) if match else None

# Function to wait for an element with a timeout
def time_wait(driver, num, code):
    try:
        return WebDriverWait(driver, num).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, code))
        )
    except:
        print(f"{code} 태그를 찾지 못하였습니다.")
        return None

# Function to scroll the place list to load all items
def scroll_place_list(driver):
    try:
        scroll_container = driver.find_element(By.CSS_SELECTOR, '#info\\.search\\.place')
        last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
        
        while True:
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_container)
            time.sleep(2)
            new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
            if new_height == last_height:
                break
            last_height = new_height
    except Exception as e:
        print(f"Error scrolling place list: {e}")

# Function to parse each item
def parsing_item(item):
    try:
        title = item.find('span', {'data-id': 'screenOutName'}).text
        info_item = item.find('div', {'class': 'info_item'})
        addr = info_item.find('div', {'class': 'addr'})
        contact = info_item.find('div', {'class': 'contact clickArea'})
        moreview = contact.find('a', {'class': 'moreview'})['href']
        address = addr.find('p', {'data-id': 'address'}).text
        contact_info = contact.find('span', {'class': 'phone'})
        contact_text = contact_info.text.strip() if contact_info else 'N/A'
        return {
            'name': title,
            'address': normalize_address(address),
            'more_info': moreview,
            'contact': contact_text,
            'place_id': get_place_id(moreview)
        }
    except AttributeError:
        return None

# Function to scrape CrossFit gyms for a given location
def scrape_crossfit(location, driver, writer, seen_places):
    print(f"Scraping CrossFit gyms in {location}...")
    
    driver.get("https://map.kakao.com/")
    
    search_box = time_wait(driver, 10, 'div.box_searchbar > input.query')
    if not search_box:
        print(f"Search box not found for {location}")
        return seen_places
    
    search_box.clear()
    search_box.send_keys(f"크로스핏 {location}")
    search_box.send_keys(Keys.ENTER)
    time.sleep(2)

    place_tab = time_wait(driver, 5, '#info\\.main\\.options > li.option1 > a')
    if place_tab:
        place_tab.send_keys(Keys.ENTER)
        time.sleep(1)

    page = 1
    page2 = 0
    error_cnt = 0
    max_errors = 5

    while True:
        page2 += 1
        print(f"** Page {page} **")

        scroll_place_list(driver)
        
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        info_search = soup.find('div', {'id': 'info.search.place'})
        
        if not info_search:
            print(f"No results found for {location}")
            break
            
        placelist = info_search.find('ul', {'class': 'placelist'})
        items = placelist.find_all('li', {'class': 'PlaceItem clickArea'}) if placelist else []
        
        for item in items:
            result = parsing_item(item)
            if result and result['place_id']:
                place_id = result['place_id']
                if place_id not in seen_places:
                    seen_places.add(place_id)
                    result['location'] = location
                    del result['place_id']  # Remove place_id from CSV output
                    writer.writerow(result)
                    print(f"Found: {result['name']} | {result['address']} | {result['contact']} | {result['more_info']}")
        
        try:
            if len(items) < 15:
                print(f"Less than 15 items found, likely last page for {location}")
                break
            
            if page2 % 5 == 0:
                next_button = driver.find_element(By.XPATH, '//*[@id="info.search.page.next"]')
                if 'disabled' in next_button.get_attribute('class'):
                    break
                next_button.send_keys(Keys.ENTER)
                page2 = 0
                time.sleep(2)
            else:
                page_button = driver.find_element(By.XPATH, f'//*[@id="info.search.page.no{page2 + 1}"]')
                page_button.send_keys(Keys.ENTER)
                time.sleep(2)
            
            page += 1
        except Exception as e:
            error_cnt += 1
            print(f"Error on page {page}: {e}")
            if error_cnt >= max_errors:
                print(f"Too many errors ({error_cnt}), stopping for {location}")
                break
            time.sleep(5)
    
    return seen_places


seoul_districts = [
    '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구', '노원구', '도봉구',
    '동대문구', '동작구', '서대문구', '성동구', '성북구', '양천구', '용산구', '은평구', '종로구', 
    '중구', '중랑구','역삼동', '삼성동', '청담동', '신사동', '논현동', '압구정동', '대치동',
    '서초동', '반포동', '잠원동', '방배동', '잠실동', '방이동', '석촌동', '가락동',
    '홍대동', '서교동', '연남동','여의도동', '영등포동', '당산동'
]

gyeonggi_cities = [
    '수원시', '성남시', '용인시', '고양시', '안산시', '안양시', '남양주시', '화성시', '부천시', '의정부시',
    '시흥시', '평택시', '광명시', '파주시', '군포시', '광주시', '김포시', '이천시', '오산시', '구리시',
    '안성시', '포천시', '양주시', '동두천시', '과천시', '하남시', '여주시', '양평군', '가평군', '연천군'
]

busan_districts = [
    '부산 중구', '부산 서구', '부산 동구', '부산 영도구', '부산진구', '부산 동래구', '부산 남구', 
    '부산 북구', '부산 해운대구', '부산 사하구', '부산 금정구', '부산 강서구', '부산 연제구', 
    '부산 수영구', '부산 사상구', '부산 기장군'
]

other_cities = [
    '대구광역시', '인천광역시', '광주광역시', '대전광역시', '울산광역시', '세종특별자치시',
    '강릉시', '춘천시', '원주시', '충주시', '제주시', '서귀포시', '창원시', '진주시', '통영시', '포항시',
    '경주시', '김해시', '여수시', '순천시', '목포시', '전주시', '군산시', '익산시', '청주시', '천안시',
    '아산시'
]

# Initialize CSV file with utf-8-sig encoding
output_file = 'crossfit_gyms_korea.csv'
file_exists = os.path.isfile(output_file)
with open(output_file, 'a', newline='', encoding='utf-8-sig') as csvfile:
    fieldnames = ['location', 'name', 'address', 'contact', 'more_info']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    if not file_exists:
        writer.writeheader()

    # Initialize WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    try:
        seen_places = set()  # Track unique places by place_id
        
        # Scrape for Seoul districts (excluding dongs to avoid overlap)
        for district in seoul_districts:
            seen_places = scrape_crossfit(district, driver, writer, seen_places)
        
        # Scrape for Gyeonggi-do
        for city in gyeonggi_cities:
            seen_places = scrape_crossfit(city, driver, writer, seen_places)
        
        # Scrape for Busan districts
        for district in busan_districts:
            seen_places = scrape_crossfit(district, driver, writer, seen_places)
        
        # Scrape for other regions
        for city in other_cities:
            seen_places = scrape_crossfit(city, driver, writer, seen_places)
    
    finally:
        driver.quit()

print(f"Data saved to {output_file}")
