import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.keys import Keys

def scrape_herkey_mentorship(search_query):
    """
    Scrapes mentorship opportunities from Herkey search page using Selenium.
    Performs a search for 'mentorship' and fetches relevant details.
    Returns a list of dictionaries containing mentorship details.
    """
    url = "https://www.herkey.com/search"
    mentorship_list = []
    driver = None
    
    try:
        # Set up Selenium with headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        
        # Navigate to URL
        driver.get(url)
        
        # Dismiss any popups or modals
        try:
            close_buttons = driver.find_elements(By.CSS_SELECTOR, ".close, [aria-label='Close'], #btn_close_herkey, #btn_close_app_install_prompt")
            for btn in close_buttons:
                try:
                    btn.click()
                    print("Dismissed popup/modal")
                    time.sleep(1)
                except:
                    continue
        except:
            print("No popups/modals found or unable to dismiss")

        # Perform search for 'mentorship'
        try:
            search_bar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#keyword, input[class*='search'], input[type='text'], [class*='MuiInputBase-input']"))
            )
            search_bar.send_keys(search_query)
            search_bar.send_keys(Keys.RETURN)
            print(f"Performed search for: {search_query}")
            time.sleep(5)  # Wait for search results to load
        except TimeoutException:
            print("Search bar not found or not interactable. Proceeding without search.")

        # Wait for mentorship listings to load
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".card, .mentor-item, [class*='mentor'], [class*='MuiBox-root'], [data-test-id*='mentor'], [class*='result']"))
            )
            print("Mentorship listings loaded")
        except TimeoutException:
            print("Timeout: Mentorship listings did not load within 30 seconds.")
            with open('herkey_mentorship_page_source_initial.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Saved initial page source to 'herkey_mentorship_page_source_initial.html' for debugging.")
            return mentorship_list

        # Scroll to load more content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait for potential lazy-loaded content

        # Find mentorship listing containers
        mentorship_elements = driver.find_elements(By.CSS_SELECTOR, ".card, .mentor-item, [class*='mentor'], [class*='MuiBox-root'], [data-test-id*='mentor'], [class*='result']")
        if not mentorship_elements:
            print("No mentorship elements found.")
            with open('herkey_mentorship_page_source_final.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Saved final page source to 'herkey_mentorship_page_source_final.html' for debugging.")
            return mentorship_list

        print(f"Found {len(mentorship_elements)} mentorship elements.")
        for i, mentor in enumerate(mentorship_elements):
            try:
                print(f"Mentorship {i + 1} HTML: {mentor.get_attribute('outerHTML')[:200]}...")
            except:
                print(f"Error logging HTML for mentorship {i + 1}")

        for mentor in mentorship_elements:
            mentor_data = {}
            
            # Extract mentorship title or program name
            title_elem = mentor.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, [class*='title'], [class*='MuiTypography-root'], [data-test-id*='title'], span, p")
            mentor_data['title'] = title_elem[0].text.strip() if title_elem else 'N/A'
            
            # Extract mentor name
            mentor_name_elem = mentor.find_elements(By.CSS_SELECTOR, "[class*='mentor-name'], [class*='name'], [class*='MuiTypography-root'], [data-test-id*='mentor-name'], span, p")
            mentor_data['mentor_name'] = mentor_name_elem[0].text.strip() if mentor_name_elem else 'N/A'
            
            # Extract description
            desc_elem = mentor.find_elements(By.CSS_SELECTOR, "[class*='description'], [class*='MuiTypography-root'], [data-test-id*='description'], p, div")
            mentor_data['description'] = desc_elem[0].text.strip() if desc_elem else 'N/A'
            
            # Extract URL
            url_elem = mentor.find_elements(By.CSS_SELECTOR, "a[href], button[data-test-id*='register'], [class*='register'], [class*='link'], [class*='apply']")
            mentor_data['url'] = url_elem[0].get_attribute('href') if url_elem and url_elem[0].get_attribute('href') else 'N/A'
            
            # Only add mentorship if at least some data is present
            if any(value != 'N/A' for value in mentor_data.values()):
                if mentor_data not in mentorship_list:  # Avoid duplicates
                    mentorship_list.append(mentor_data)
                    print(f"Added mentorship: {mentor_data['title']}")
        
        if not mentorship_list:
            print("No mentorship opportunities found after scraping.")
            with open('herkey_mentorship_page_source_final.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Saved final page source to 'herkey_mentorship_page_source_final.html' for debugging.")
        
        # Save to JSON file
        with open('herkey_mentorship.json', 'w', encoding='utf-8') as f:
            json.dump(mentorship_list, f, indent=4, ensure_ascii=False)
        
    except WebDriverException as e:
        print(f"Error with WebDriver: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if driver:
            driver.quit()
    
    return mentorship_list

# # Example usage
# if __name__ == "__main__":
#     mentorships = scrape_herkey_mentorship()
#     print(f"Scraped {len(mentorships)} mentorship opportunities")
#     for mentor in mentorships[:5]:  # Print first 5 mentorships
#         print(json.dumps(mentor, indent=2))