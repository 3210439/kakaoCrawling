# kakaoCrawling
카카오 맵에 특정 키워드로 검색을 한후 나타나는 리스트의 정보를 추출하여 타이틀, 주소, url을 나타내는 코드입니다.

# 소스코드
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import datetime
from bs4 import BeautifulSoup

def parsing_item(item):
    title = item.find('span',{'data-id':'screenOutName'}).text
    info_item = item.find('div',{'class':'info_item'})
    addr = info_item.find('div', {'class': 'addr'})
    contact = info_item.find('div', {'class':'contact clickArea'})
    moreview = contact.find('a', {'class':'moreview'})['href']
    address = addr.find('p',{'data-id':'address'}).text

    print("이름: {}".format(title))
    print("주소: {}".format(address))
    print("상세정보: {}".format(moreview))
    print("-"*50)


#Chrome WebDriver를 이용해 Chrome을 실행합니다.
driver = webdriver.Chrome(executable_path='C:/Users/kimde/downloads/chromedriver_win32/chromedriver.exe')

#카카오 맵으로 이동하기
driver.get("https://map.kakao.com/")
time.sleep(1)
#검색창 가져오기
search_box = driver.find_element_by_css_selector('#search\.keyword\.query')
#검색창에 검색하기
search_box.send_keys("광안대교")
time.sleep(1)
#검색버튼 누르기
search_box.send_keys(Keys.ENTER)
time.sleep(1)
#크롬에 키워드로 검색한 html 소스 받아오기
html = driver.page_source

soup = BeautifulSoup(html, "html.parser")
infoSearch = soup.find('div', {'id':'info.search.place'})
placelist = infoSearch.find('ul', {'class':'placelist'})
items = soup.find_all('li',{'class':'PlaceItem clickArea'})

for i in items:
    parsing_item(i)

# 결과
![image](https://user-images.githubusercontent.com/47379176/159160036-dc2069c4-8e71-48ba-816a-9f4d0eb33f59.png)
