import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random
import re

def find_emails(driver):
    all_found = set()
    page_source = driver.page_source
    
    # 1. 정규표현식으로 텍스트에서 추출
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    regex_emails = re.findall(email_pattern, page_source)
    exclude_keywords = ['sentry.io', 'ingest', 'gitbook', 'wix', 'example', 'test']

    for e in regex_emails:
        # [순서 수정] 먼저 정제부터 진행
        email = e.lower()
        email = re.sub(r'^[uU][0-9a-fA-F]{4}', '', email) 
        email = email.lstrip('>').lstrip('<').strip()

        # 필터링 로직 후 추가
        if not any(key in email for key in exclude_keywords):
            if not email.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                if len(email.split('@')[0]) < 30:
                    all_found.add(email)

   # 2. mailto: 태그에서 직접 추출
    try:
        mailto_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
        for link in mailto_links:
            href = link.get_attribute("href")
            clean_email = href.replace("mailto:", "").split("?")[0].strip().lower()
            if clean_email and not any(key in clean_email for key in exclude_keywords):
                all_found.add(clean_email)
    except:
        pass

    return list(all_found)

def find_contact_link(driver):
    keywords = ['contact', 'about', 'get in touch', 'reach us', 'enquiry']
    links = driver.find_elements(By.TAG_NAME, "a")
    
    for link in links:
        try:
            href = link.get_attribute("href")
            text = link.text.lower()
            
            # [수정 포인트] href에 'mailto:'가 들어있으면 무조건 패스!
            if href and "mailto:" in href:
                continue
                
            if href and any(key in text or key in href.lower() for key in keywords):
                # 실제 웹 페이지 주소(http)인 경우에만 리턴
                if href.startswith("http"):
                    return href
        except: continue
    return None

def get_current_page_data(driver):
    # 구글 검색 결과 아이템 추출
    items = driver.find_elements(By.CSS_SELECTOR, "div.g")
    if not items:
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

def scrape_google_pages(search_query, start_page=1, max_pages=3):
    driver = uc.Chrome()
    all_data = []

    try:
        # 1. 시작 페이지로 바로 접속
        start_value = (start_page - 1) * 10
        search_url = f"https://www.google.com/search?q={search_query}&start={start_value}"        
        driver.get(search_url)
        time.sleep(random.uniform(2, 4))

        # 2. 구글 검색 결과 리스트 수집
        for i in range(max_pages):            
            all_data.extend(get_current_page_data(driver))
            
            # 다음 페이지 이동 (마지막 루프가 아닐 때만)
            if i < max_pages - 1:
                if not move_to_next_page(driver):
                    print("더 이상 다음 페이지가 없습니다.")
                    break

        # 3. 개별 웹사이트 방문 및 이메일 추출
        print(f"\n--- 상세 방문 시작 ({len(all_data)}건) ---")
        for data in all_data:
            try:
                print(f"방문 중: {data['link']}")
                driver.get(data['link'])
                time.sleep(random.uniform(3, 5))
                
                # [메인 페이지] 수집
                found_emails = set(find_emails(driver))
                
                # 이메일이 적으면 [Contact 페이지] 추적
                if len(found_emails) < 2:
                    contact_url = find_contact_link(driver)
                    if contact_url and contact_url != data['link']:
                        print(f"   --> Contact 페이지 이동: {contact_url}")
                        driver.get(contact_url)
                        time.sleep(random.uniform(2, 3))
                        # 찾은 정보를 기존 세트에 추가 (update 사용)
                        found_emails.update(find_emails(driver))

                # [중요] 변수에 저장된 최종 세트를 리스트로 변환하여 저장
                data['emails'] = list(found_emails) 
                print(f"결과: [{data['title'][:15]}] 찾은 이메일: {data['emails']}")
                
            except Exception as e:
                data['emails'] = []
                print(f"방문 실패: {data['link']}")

    except Exception as e:
        print(f"실행 중 에러 발생: {e}")

    finally:
        print("\n모든 수집 작업이 완료되었습니다.")
        driver.quit()
        return all_data

       

if __name__ == "__main__":
    query = "London IV drips"
    results = scrape_google_pages(query, start_page=2, max_pages=1)

    print("\n" + "="*70)
    print(f"  [수집 결과 보고서] - 검색어: {query}")
    print("="*70)
    
    if not results:
        print("수집된 데이터가 없습니다.")
    else:
        for i, item in enumerate(results, 1):
            print(f"[{i}] 업체명: {item['title']}")
            print(f"    링크: {item['link']}")
            if item['emails']:
                # 이메일 리스트를 쉼표로 연결해서 출력
                print(f"    이메일: {', '.join(item['emails'])}")
            else:
                print(f"    이메일: (수집 실패 또는 없음)")
            print("-" * 70)
    
    print(f"\n총 {len(results)}건의 업체 정보를 확인했습니다.")