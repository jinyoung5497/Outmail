import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random
import re

def find_emails(driver):
    page_source = driver.page_source
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = set(re.findall(email_pattern, page_source))
    filtered_emails = [e for e in emails if not e.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return filtered_emails

def find_contact_link(driver):
    keywords = ['contact', 'about', 'info', 'get in touch', 'reach us']
    links = driver.find_elements(By.TAG_NAME, "a")
    
    for link in links:
        try:
            href = link.get_attribute("href")
            text = link.text.lower()
            if href and any(key in text or key in href.lower() for key in keywords):
                return href
        except:
            continue
    return None

def get_current_page_data(driver):
    items = driver.find_elements(By.CSS_SELECTOR, "span.V9tjod")
    page_data = []
    
    for item in items:
        title = item.find_element(By.CSS_SELECTOR, "span.VuuXrf").text
        link = item.find_element(By.CSS_SELECTOR, "a.zReHs").get_attribute("href")  
        page_data.append({"title": title, "link": link})
        print(f"수집 성공: {title} - {link}")
    
    return page_data

def move_to_next_page(driver):
    try:
        next_button = driver.find_element(By.ID, "pnnext")
        next_button.click()
        time.sleep(random.uniform(2, 4))
        return True
    except:
        return False

def scrape_google_pages(search_query, max_pages=3):
    driver = uc.Chrome()
    all_data = []

    try:
        driver.get("https://www.google.com")
        time.sleep(random.uniform(2, 3))
        
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(search_query + Keys.ENTER)
        time.sleep(random.uniform(2, 3))

        for current_page in range(1, max_pages + 1):
            all_data.extend(get_current_page_data(driver))
            if current_page < max_pages:
                if not move_to_next_page(driver): break

        for data in all_data:
            try:
                driver.get(data['link'])
                time.sleep(random.uniform(2, 4))
                
                # [메인 페이지]에서 찾기
                found_emails = set(find_emails(driver))
                
                # 만약 메인에서 못 찾았다면 [Contact 페이지] 추적
                if not found_emails:
                    contact_url = find_contact_link(driver)
                    if contact_url and contact_url != data['link']:
                        print(f"   --> Contact 페이지 추적: {contact_url}")
                        driver.get(contact_url)
                        time.sleep(random.uniform(2, 3))
                        found_emails.update(find_emails(driver))

                data['emails'] = find_emails(driver) 
                print(f"[{data['title']}] 찾은 이메일: {data['emails']}")
            except:
                data['emails'] = []
                print(f"방문 실패: {data['link']}")

        print(f"\n총 {len(all_data)}건의 데이터를 수집했습니다.")

    except Exception as e:
        print(f"실행 중 에러 발생: {e}")

    finally:
        try:
            print("프로그램을 종료합니다.")
            driver.quit()
        except:
            pass # WinError 6 메시지를 무시하기 위해 통과시킴

       

if __name__ == "__main__":
    scrape_google_pages("London IV drips", max_pages=3)