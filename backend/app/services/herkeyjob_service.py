import sys
import json
from pathlib import Path
# Add the backend directory to sys.path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
sys.path.append(str(backend_dir))
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

def scrape_herkey_jobs(search_query):
    """
    Scrapes job listings from Herkey jobs page using Selenium for dynamic content.
    Simulates a search query to trigger job listings.
    Returns a list of dictionaries containing job details.
    """
    url="https://www.herkey.com/jobs"
    jobs_list = []
    driver = None
    print("scraping herkey jobs",search_query)
    try:
        # Set up Selenium with headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to URL
        driver.get(url)
        
        # Interact with the search bar
        try:
            search_bar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[class*='search'], input[type='text'], [class*='MuiInputBase-input']"))
            )
            search_bar.send_keys(search_query)
            search_bar.send_keys(Keys.RETURN)
            print(f"Performed search for: {search_query}")
        except TimeoutException:
            print("Search bar not found or not interactable. Proceeding without search.")

        # Wait for job listings to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='job-details']"))
            )
        except TimeoutException:
            print("Timeout: Job listings did not load within 20 seconds.")
            with open('herkey_page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Saved page source to 'herkey_page_source.html' for debugging.")
            return []

        # Scroll to load more jobs (handle lazy loading)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for potential lazy-loaded content

        # Find job listing containers
        job_elements = driver.find_elements(By.CSS_SELECTOR, "[data-test-id='job-details']")

        if not job_elements:
            print("No job elements found. Check if jobs require additional filters or login.")
            with open('herkey_page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Saved page source to 'herkey_page_source.html' for debugging.")
        
        for job in job_elements:
            job_data = {}
            
            # Extract job title
            title_elem = job.find_elements(By.CSS_SELECTOR, "[data-test-id='job-title']")
            job_data['title'] = title_elem[0].text.strip() if title_elem else 'N/A'
            
            # Extract company name
            company_elem = job.find_elements(By.CSS_SELECTOR, "[data-test-id='company-name']")
            job_data['company'] = company_elem[0].text.strip() if company_elem else 'N/A'
            
            # Extract location and details
            details_elem = job.find_elements(By.CSS_SELECTOR, "p[class*='capitalize css-y9sg3k']")
            job_data['details'] = details_elem[0].text.strip() if details_elem else 'N/A'
            
            # Extract skills
            skills_elem = job.find_elements(By.CSS_SELECTOR, "span[class*='capitalize css-2wpeo8']")
            job_data['skills'] = skills_elem[0].text.strip() if skills_elem else 'N/A'
            
            # Extract apply URL (from the Apply button)
            apply_button = job.find_elements(By.CSS_SELECTOR, "[data-test-id='apply-job']")
            job_data['apply_url'] = apply_button[0].get_attribute('href') if apply_button and apply_button[0].get_attribute('href') else 'N/A'
            
            # Extract salary (not explicitly present in HTML, so default to 'Not disclosed')
            job_data['salary'] = 'Not disclosed'
            
            # Only add job if at least some data is present
            if any(value != 'N/A' and value != 'Not disclosed' for value in job_data.values()):
                jobs_list.append(job_data)
        
        # Save to JSON file
        with open('data/herkey_jobs.json', 'w', encoding='utf-8') as f:
            json.dump(jobs_list, f, indent=4, ensure_ascii=False)
        
    except WebDriverException as e:
        print(f"Error with WebDriver: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if driver:
            driver.quit()
    
    return jobs_list,url

# # Example usage
# if __name__ == "__main__":
#     jobs = scrape_herkey_jobs()
#     print(f"Scraped {len(jobs)} jobs")
#     for job in jobs[:10]:  # Print first 5 jobs
#         print(json.dumps(job, indent=2))