from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import datetime
from bs4 import BeautifulSoup
import csv
import os

# Function to parse each item
def parsing_item(item):
    try:
        title = item.find('span', {'data-id': 'screenOutName'}).text
        info_item = item.find('div', {'class': 'info_item'})
        addr = info_item.find('div', {'class': 'addr'})
        contact = info_item.find('div', {'class': 'contact clickArea'})
        moreview = contact.find('a', {'class': 'moreview'})['href']
        address = addr.find('p', {'data-id': 'address'}).text
        # Extract contact info (phone number)
        contact_info = contact.find('span', {'class': 'phone'})
        contact_text = contact_info.text.strip() if contact_info else 'N/A'
        return {
            'name': title,
            'address': address,
            'more_info': moreview,
            'contact': contact_text
        }
    except AttributeError:
        return None

# Function to scrape CrossFit gyms for a given location
def scrape_crossfit(location, driver, writer):
    print(f"Scraping CrossFit gyms in {location}...")
    
    # Navigate to Kakao Map
    driver.get("https://map.kakao.com/")
    
    # Wait for search box and enter query
    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#search\\.keyword\\.query'))
        )
        search_box.clear()
        search_box.send_keys(f"크로스핏 {location}")
        search_box.send_keys(Keys.ENTER)
        time.sleep(2)  # Wait for results to load
    except Exception as e:
        print(f"Error searching for {location}: {e}")
        return

    # Scrape all pages
    page = 1
    while True:
        # Get page source and parse
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
            if result:
                result['location'] = location
                writer.writerow(result)
                print(f"Found: {result['name']} | {result['address']} | {result['contact']} | {result['more_info']}")
        
        # Check for next page
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, '#info\\.search\\.page\\.next')
            if 'disabled' in next_button.get_attribute('class'):
                break
            next_button.click()
            page += 1
            time.sleep(2)  # Wait for next page to load
        except:
            break

# Administrative divisions
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

other_cities = [
    '부산광역시', '대구광역시', '인천광역시', '광주광역시', '대전광역시', '울산광역시', '세종특별자치시',
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
        # Scrape for Seoul
        for district in seoul_districts:
            scrape_crossfit(district, driver, writer)
        
        # Scrape for Gyeonggi-do
        for city in gyeonggi_cities:
            scrape_crossfit(city, driver, writer)
        
        # Scrape for other regions
        for city in other_cities:
            scrape_crossfit(city, driver, writer)
    
    finally:
        driver.quit()

print(f"Data saved to {output_file}")
