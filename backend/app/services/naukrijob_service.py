import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

def scrape_naukri_jobs(search_query):
    """
    Scrapes job listings from Naukri.com using Selenium in headless mode for background execution.
    Simulates a search query and handles pagination to fetch job details across multiple pages.
    Returns a list of dictionaries containing job details.

    Args:
        url (str): Base URL of Naukri.com
        search_query (str): Search term (e.g., "software engineer")
        max_pages (int): Maximum number of pages to scrape
    """
    url="https://www.naukri.com/"
    max_pages=2
    jobs_list = []
    driver = None
    
    try:
        # Set up Selenium with headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")  # Disable extensions for performance
        chrome_options.add_argument("--disable-images")  # Optional: Disable images to reduce load
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        
        # Navigate to URL
        print(f"Navigating to {url}")
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        print("Page title:", driver.title)
        # Save screenshot (optional, for debugging; headless mode still supports this)
        # driver.save_screenshot("naukri_debug.png")
        
        # Interact with the search bar
        try:
            search_bar = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "input.sugInp, input[keyword], input[placeholder*='skills'], input[id*='qsb-keyword']"
                ))
            )
            search_bar.clear()
            search_bar.send_keys(search_query)
            search_bar.send_keys(Keys.RETURN)
            print(f"Performed search for: {search_query}")
            time.sleep(5)  # Allow search results to load
        except TimeoutException:
            print("Search bar not found or not interactable. Proceeding without search.")
        
        # Process job listings across pages
        page_count = 0
        while page_count < max_pages:
            # Wait for job listings to load
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR, 
                        "article.jobTuple, div.jobTuple, div.srp-jobtuple-wrapper"
                    ))
                )
            except TimeoutException:
                print(f"Timeout: Job listings did not load on page {page_count + 1}.")
                with open('naukri_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print("Saved page source to 'naukri_page_source.html' for debugging.")
                break
            
            # Scroll to load more jobs (handle lazy loading)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Wait for lazy-loaded content
            
            # Find job listing containers
            job_elements = driver.find_elements(
                By.CSS_SELECTOR, 
                "article.jobTuple, div.jobTuple, div.srp-jobtuple-wrapper"
            )
            
            if not job_elements:
                print(f"No job elements found on page {page_count + 1}. Check if jobs require filters or login.")
                with open('naukri_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print("Saved page source to 'naukri_page_source.html' for debugging.")
                break
            
            for job in job_elements:
                job_data = {}
                
                # Extract job title
                title_elem = job.find_elements(By.CSS_SELECTOR, "a.title, a.job-title, .jobTupleHeader a")
                job_data['title'] = title_elem[0].text.strip() if title_elem else 'N/A'
                
                # Extract company name
                company_elem = job.find_elements(By.CSS_SELECTOR, "a.subTitle, .company-name, .subTitle a")
                job_data['company'] = company_elem[0].text.strip() if company_elem else 'N/A'
                
                # Extract location
                location_elem = job.find_elements(By.CSS_SELECTOR, ".location, .loc-info, .job-location")
                job_data['location'] = location_elem[0].text.strip() if location_elem else 'N/A'
                
                # Extract salary
                salary_elem = job.find_elements(By.CSS_SELECTOR, ".salary, .sal-info, .salary-info")
                job_data['salary'] = salary_elem[0].text.strip() if salary_elem else 'Not disclosed'
                
                # Extract experience
                exp_elem = job.find_elements(By.CSS_SELECTOR, ".experience, .exp-info, .exp")
                job_data['experience'] = exp_elem[0].text.strip() if exp_elem else 'N/A'
                
                # Extract skills
                skills_elem = job.find_elements(By.CSS_SELECTOR, ".tags, .skills, .key-skills")
                job_data['skills'] = skills_elem[0].text.strip() if skills_elem else 'N/A'
                
                # Extract apply URL
                link_elem = job.find_elements(By.CSS_SELECTOR, "a.title, a.job-title, .jobTupleHeader a")
                job_data['link'] = link_elem[0].get_attribute('href') if link_elem and link_elem[0].get_attribute('href') else 'N/A'
                
                # Only add job if at least some data is present
                if any(value != 'N/A' and value != 'Not disclosed' for value in job_data.values()):
                    jobs_list.append(job_data)
            
            # Move to the next page
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a.fright.fs14.btn-secondary.br2, .pagination a.next")
                if next_button.is_enabled() and next_button.is_displayed():
                    next_button.click()
                    print(f"Moving to page {page_count + 2}")
                    time.sleep(5)  # Wait for next page to load
                    page_count += 1
                else:
                    print("Next button disabled or not found. Stopping pagination.")
                    break
            except:
                print("No more pages available.")
                break
        
        # Save to JSON file
        with open('data/naukri_jobs.json', 'w', encoding='utf-8') as f:
            json.dump(jobs_list, f, indent=4, ensure_ascii=False)
        
        print(f"Scraped {len(jobs_list)} jobs across {page_count + 1} page(s)")
        
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
#     jobs = scrape_naukri_jobs()
#     print(f"Scraped {len(jobs)} jobs")
#     for job in jobs[:5]:  # Print first 5 jobs
#         print(json.dumps(job, indent=2))