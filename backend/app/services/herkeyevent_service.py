import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.keys import Keys

def scrape_herkey_events(search_query):
    """
    Scrapes event listings from Herkey events page using Selenium for dynamic content.
    Interacts with the calendar and handles dynamic loading to fetch events.
    Returns a list of dictionaries containing event details.
    """
    url="https://events.herkey.com/events"
    events_list = []
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
        
        # Dismiss any popups or modals (e.g., app install prompt)
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

        # Perform search if query is provided
        if search_query:
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

        # Wait for calendar or event listings to load
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".calendar-container, .card, .event-item, [class*='event'], [class*='MuiBox-root'], [data-test-id*='event']"))
            )
            print("Calendar or event listings loaded")
        except TimeoutException:
            print("Timeout: Calendar or event listings did not load within 30 seconds.")
            with open('herkey_events_page_source_initial.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Saved initial page source to 'herkey_events_page_source_initial.html' for debugging.")

        # Scroll to load more content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait for potential lazy-loaded content

        # Interact with calendar to load events for marked dates
        try:
            marked_dates = driver.find_elements(By.CSS_SELECTOR, ".calendar-container li[data-calendar-day] i.dot")
            if marked_dates:
                print(f"Found {len(marked_dates)} marked dates in calendar.")
                for index, date_elem in enumerate(marked_dates):
                    try:
                        # Get parent <li> element to click
                        parent_li = date_elem.find_element(By.XPATH, "./parent::li")
                        date_value = parent_li.get_attribute("data-calendar-day")
                        driver.execute_script("arguments[0].scrollIntoView(true);", parent_li)
                        parent_li.click()
                        print(f"Clicked calendar date: {date_value}")
                        time.sleep(5)  # Wait longer for events to load

                        # Wait for event listings to appear
                        try:
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".card, .event-item, [class*='event'], [class*='MuiBox-root'], [data-test-id*='event']"))
                            )
                            print(f"Event listings loaded for date: {date_value}")
                        except TimeoutException:
                            print(f"No event listings loaded for date: {date_value}")
                            continue

                        # Save page source after clicking
                        with open(f'herkey_events_page_source_date_{index + 1}_{date_value.replace("/", "-")}.html', 'w', encoding='utf-8') as f:
                            f.write(driver.page_source)
                        print(f"Saved page source to 'herkey_events_page_source_date_{index + 1}_{date_value.replace('/', '-')}.html'")

                        # Find event listing containers
                        event_elements = driver.find_elements(By.CSS_SELECTOR, ".card, .event-item, [class*='event'], [class*='MuiBox-root'], [data-test-id*='event']")
                        if not event_elements:
                            print(f"No event elements found for date: {date_value}")
                            continue

                        # Log DOM structure for debugging
                        print(f"Found {len(event_elements)} event elements for date: {date_value}")
                        for i, event in enumerate(event_elements):
                            try:
                                print(f"Event {i + 1} HTML: {event.get_attribute('outerHTML')[:200]}...")  # Log first 200 chars
                            except:
                                print(f"Error logging HTML for event {i + 1}")

                        for event in event_elements:
                            event_data = {}
                            
                            # Extract event title
                            title_elem = event.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, [class*='title'], [class*='MuiTypography-root'], [data-test-id*='title'], span, p")
                            event_data['title'] = title_elem[0].text.strip() if title_elem else 'N/A'
                            
                            # Extract event date
                            date_elem = event.find_elements(By.CSS_SELECTOR, "time, [class*='date'], [class*='MuiTypography-root'], [data-test-id*='date'], span, p")
                            event_data['date'] = date_elem[0].text.strip() if date_elem else 'N/A'
                            
                            # Extract event location
                            location_elem = event.find_elements(By.CSS_SELECTOR, "[class*='location'], [class*='MuiTypography-root'], [data-test-id*='location'], span, p")
                            event_data['location'] = location_elem[0].text.strip() if location_elem else 'N/A'
                            
                            # Extract event description
                            desc_elem = event.find_elements(By.CSS_SELECTOR, "[class*='description'], [class*='MuiTypography-root'], [data-test-id*='description'], p, div")
                            event_data['description'] = desc_elem[0].text.strip() if desc_elem else 'N/A'
                            
                            # Extract event URL
                            url_elem = event.find_elements(By.CSS_SELECTOR, "a[href], button[data-test-id*='register'], [class*='register'], [class*='link']")
                            event_data['url'] = url_elem[0].get_attribute('href') if url_elem and url_elem[0].get_attribute('href') else 'N/A'
                            
                            # Only add event if at least some data is present
                            if any(value != 'N/A' for value in event_data.values()):
                                if event_data not in events_list:  # Avoid duplicates
                                    events_list.append(event_data)
                                    print(f"Added event: {event_data['title']}")
                    
                    except Exception as e:
                        print(f"Error processing calendar date {date_value}: {e}")
                        continue
            else:
                print("No marked dates found in calendar.")
        except Exception as e:
            print(f"Error interacting with calendar: {e}")

        # Try finding events without calendar interaction (e.g., default or carousel events)
        try:
            event_elements = driver.find_elements(By.CSS_SELECTOR, ".card, .event-item, [class*='event'], [class*='MuiBox-root'], [data-test-id*='event']")
            if event_elements:
                print(f"Found {len(event_elements)} event elements without calendar interaction.")
                for event in event_elements:
                    event_data = {}
                    
                    # Extract event title
                    title_elem = event.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, [class*='title'], [class*='MuiTypography-root'], [data-test-id*='title'], span, p")
                    event_data['title'] = title_elem[0].text.strip() if title_elem else 'N/A'
                    
                    # Extract event date
                    date_elem = event.find_elements(By.CSS_SELECTOR, "time, [class*='date'], [class*='MuiTypography-root'], [data-test-id*='date'], span, p")
                    event_data['date'] = date_elem[0].text.strip() if date_elem else 'N/A'
                    
                    # Extract event location
                    location_elem = event.find_elements(By.CSS_SELECTOR, "[class*='location'], [class*='MuiTypography-root'], [data-test-id*='location'], span, p")
                    event_data['location'] = location_elem[0].text.strip() if location_elem else 'N/A'
                    
                    # Extract event description
                    desc_elem = event.find_elements(By.CSS_SELECTOR, "[class*='description'], [class*='MuiTypography-root'], [data-test-id*='description'], p, div")
                    event_data['description'] = desc_elem[0].text.strip() if desc_elem else 'N/A'
                    
                    # Extract event URL
                    url_elem = event.find_elements(By.CSS_SELECTOR, "a[href], button[data-test-id*='register'], [class*='register'], [class*='link']")
                    event_data['url'] = url_elem[0].get_attribute('href') if url_elem and url_elem[0].get_attribute('href') else 'N/A'
                    
                    # Only add event if at least some data is present
                    if any(value != 'N/A' for value in event_data.values()):
                        if event_data not in events_list:  # Avoid duplicates
                            events_list.append(event_data)
                            print(f"Added event: {event_data['title']}")
        except Exception as e:
            print(f"Error scraping default events: {e}")

        if not events_list:
            print("No events found after all attempts.")
            with open('herkey_events_page_source_final.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Saved final page source to 'herkey_events_page_source_final.html' for debugging.")
        
        # Save to JSON file
        with open('herkey_events.json', 'w', encoding='utf-8') as f:
            json.dump(events_list, f, indent=4, ensure_ascii=False)
        
    except WebDriverException as e:
        print(f"Error with WebDriver: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if driver:
            driver.quit()
    
    return events_list

# Example usage
if __name__ == "__main__":
    events = scrape_herkey_events()
    print(f"Scraped {len(events)} events")
    for event in events[:5]:  # Print first 5 events
        print(json.dumps(event, indent=2))