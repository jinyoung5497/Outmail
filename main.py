import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random
import re
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_individual_gmail(sender_email, to_email, company_name, subject, body_template):
    app_password = "xxaw ckae rlvk gylq" # 앱 비밀번호 (보안 주의)
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)

        # 업체명 개인화 적용
        personalized_body = body_template.replace("{company_name}", company_name)

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(personalized_body, 'plain'))

        server.sendmail(sender_email, to_email, msg.as_string())
        print(f"발송 성공: {company_name} ({to_email})")

        server.quit()
    except Exception as e:
        print(f"메일 발송 중 에러 발생 ({to_email}): {e}")

def send_gmail(sender_email, bcc_emails, subject, body):
    app_password = "xxaw ckae rlvk gylq" 
    
    if not bcc_emails:
        print("발송할 BCC 대상 이메일이 없습니다.")
        return

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = sender_email  
        msg['Subject'] = subject
        
        # 1. Bcc 헤더를 일단 추가하여 수신자 리스트를 만듭니다.
        msg['Bcc'] = ", ".join(bcc_emails) 
        msg.attach(MIMEText(body, 'plain'))

        # 2. [추가 권장] 실제 전송 메시지 복사본에서 Bcc 헤더만 제거 (개인정보 보호)
        # 이렇게 하면 수신자들이 서로의 이메일을 절대 볼 수 없습니다.
        del msg['Bcc']

        # 3. 발송 (Bcc 헤더는 지웠지만, recipients 인자를 명시하거나 
        # 처음부터 리스트를 합쳐서 전달하는 것이 가장 확실합니다.)
        recipients = [sender_email] + bcc_emails
        server.sendmail(sender_email, recipients, msg.as_string())
        
        print(f"메일 발송 완료! (To: {sender_email}, Bcc: {len(bcc_emails)}명)")

        server.quit()
    except Exception as e:
        print(f"메일 발송 중 에러 발생: {e}")


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
    query = "New York IV drips distributor"
    results = scrape_google_pages(query, start_page=1, max_pages=3)

    if results:
        my_email = "jinyoung@nexus-pharma.com"
        mail_subject = "[Nexus Pharma] Direct Source: Korean Medical Aesthetics & IV Injections"
        mail_template = """Hello {company_name}, 

This is Jin from Nexus Pharma.

We are a Korean wholesale pharmaceutical distributor specializing in medical-grade products.

Our portfolio includes:
 • IV Injections & Vitamin Injections
 • Dermal Fillers & Botulinum Toxins
 • Skin Boosters & Mesotherapy
 • Oral Pharmaceutical Products
 • Premium Skincare Cosmetics

We believe our products could be a valuable addition to your portfolio. 
If you are interested, please let me know and I will provide our full catalog and wholesale price list.

For faster communication, you can click to chat directly via WhatsApp:
https://wa.me/821073435497

Looking forward to hearing from you.

Kind regards,
Jinyoung Choi"""

        print("\n--- 개별 메일 발송 시작 ---")
        
        for item in results:
            company = item.get('title', '') # 업체명이 없으면 공백으로 대체
            emails = item.get('emails', [])
            
            for target_email in emails:
                if "@" in target_email:
                    # 1:1 발송 호출
                    send_individual_gmail(my_email, target_email, company, mail_subject, mail_template)
                    
                    # 스팸 방지를 위해 발송 사이 간격을 충분히 둠 (15~30초 추천)
                    wait_time = random.uniform(10, 15)
                    print(f"다음 발송까지 {wait_time:.1f}초 대기 중...")
                    time.sleep(wait_time)

        print("\n--- 모든 메일 발송 작업이 완료되었습니다. ---")