from typing import Any
from selenium.webdriver.chrome.webdriver import WebDriver
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import sys


URL = 'https://profiles.doe.mass.edu/statereport/gradrates.aspx'
DROPDOWN_NAME = 'ctl00$ContentPlaceHolder1$ddSubgroup'
DATA_TYPE_NAME = 'ctl00$ContentPlaceHolder1$ddReportType'

DROPDOWN_VALUES = {
    "AI": "American Indian or Alaska Native",
    "AS": "Asian",
    "AA": "Black or African American",
    "HI": "Hispanic or Latino",
    "MR": "Multi-Race, Not Hispanic or Latino",
    "NH": "Native Hawaiian or Other Pacific Islander",
    "WH": "White",
    "HN": "High Needs",
    "LEP": "English Learners",
    "FL": "Low Income",
    "SWD": "Students with Disabilities",
    "FOS": "Foster Care",
    "HML": "Homeless",
    "FE": "Female",
    "MA": "Male"
}



def get_data(driver, value, wait_timeout=30):
    """
    Extract data from the graduation rates table.
    
    Args:
        driver: Selenium WebDriver instance
        value: Subgroup value code
        wait_timeout: Maximum time to wait for table to appear (seconds)
    
    Returns:
        list: List of dictionaries containing row data
    """
    wait = WebDriverWait(driver, wait_timeout)
    data = []
    
    try:
        # Wait for the table to appear
        table = wait.until(
            EC.presence_of_element_located((By.ID, 'tblStateReport'))
        )
        
        # Find tbody within the table (not the entire page)
        # Try to find tbody, if not found, use table directly
        try:
            tbody = table.find_element(By.TAG_NAME, 'tbody')
            rows = tbody.find_elements(By.TAG_NAME, 'tr')
        except NoSuchElementException:
            # If no tbody, get rows directly from table
            rows = table.find_elements(By.TAG_NAME, 'tr')
        
        # Skip header row if present (first row might be header)
        for idx, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, 'td')
                
                # Skip rows that don't have enough cells (likely headers or empty rows)
                if len(cells) < 9:
                    continue
                
                result = {
                    'entity_name': cells[0].text.strip() if cells[0].text else '',
                    'entity_code': cells[1].text.strip() if cells[1].text else '',
                    'breakdown': DROPDOWN_VALUES.get(value, value),
                    '# in Cohort': cells[2].text.strip() if len(cells) > 2 and cells[2].text else '',
                    '% Graduated': cells[3].text.strip() if len(cells) > 3 and cells[3].text else '',
                    '% Still in School': cells[4].text.strip() if len(cells) > 4 and cells[4].text else '',
                    '% Non-Grad Completers': cells[5].text.strip() if len(cells) > 5 and cells[5].text else '',
                    '% H.S. Equiv': cells[6].text.strip() if len(cells) > 6 and cells[6].text else '',
                    '% Dropped Out': cells[7].text.strip() if len(cells) > 7 and cells[7].text else '',
                    '% Permanently Excluded': cells[8].text.strip() if len(cells) > 8 and cells[8].text else ''
                }
                
                # Only add rows with actual data (entity_name should not be empty)
                if result['entity_name']:
                    data.append(result)
                    
            except (IndexError, NoSuchElementException) as e:
                # Skip rows that cause errors
                print(f"Warning: Skipping row {idx} due to error: {e}")
                continue
        
        if not data:
            print(f"Warning: No data found for subgroup {value}")
            
    except TimeoutException:
        print(f"Error: Table 'tblStateReport' did not appear within {wait_timeout} seconds for subgroup {value}")
        return []
    except Exception as e:
        print(f"Error extracting data for subgroup {value}: {e}")
        return []
    
    return data



def reset_page_state(driver, data_type, wait_timeout=30):
    """
    Reload the page and reset to the correct data type (school or district).
    
    Args:
        driver: Selenium WebDriver instance
        data_type: 'school' or 'district'
        wait_timeout: Maximum time to wait for elements (seconds)
    """
    wait = WebDriverWait[Any](driver, wait_timeout)
    
    print(f"  Reloading page and resetting to {data_type}...")
    driver.refresh()
    
    # Wait for page to load
    wait.until(
        EC.presence_of_element_located((By.NAME, DROPDOWN_NAME))
    )
    time.sleep(1)
    
    # Reset data type if needed
    if data_type == 'school':
        try:
            select_element = wait.until(
                EC.presence_of_element_located((By.NAME, DATA_TYPE_NAME))
            )
            select = Select(select_element)
            select.select_by_value("School")
            time.sleep(0.5)
            
            # Click View Report to apply the change
            view_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="View Report"]'))
            )
            view_button.click()
            time.sleep(2)
        except Exception as e:
            print(f"  Warning: Could not reset data type: {e}")


def handle_subgroup(driver, value, data_type=None, max_retries=2, wait_timeout=30):
    """
    Handle selecting a subgroup and retrieving its data with retry logic.
    
    Args:
        driver: Selenium WebDriver instance
        value: Subgroup value code to select
        data_type: 'school' or 'district' (for retry/reload)
        max_retries: Maximum number of retry attempts
        wait_timeout: Maximum time to wait for elements (seconds)
    
    Returns:
        list: List of dictionaries containing row data, or empty list on error
    """
    wait = WebDriverWait[Any](driver, wait_timeout)
    
    for attempt in range(max_retries + 1):
        try:
            # On retry attempts, reload the page
            if attempt > 0:
                print(f"  Retry attempt {attempt}/{max_retries}...")
                if data_type:
                    reset_page_state(driver, data_type, wait_timeout)
                else:
                    driver.refresh()
                    wait.until(
                        EC.presence_of_element_located((By.NAME, DROPDOWN_NAME))
                    )
                    time.sleep(1)
            
            # Wait for and find the select element
            select_element = wait.until(
                EC.presence_of_element_located((By.NAME, DROPDOWN_NAME))
            )
            
            # Wait for the select to be clickable
            wait.until(EC.element_to_be_clickable((By.NAME, DROPDOWN_NAME)))
            
            # Create Select object and select the value
            select = Select(select_element)
            
            # Check if the value exists in the dropdown
            try:
                select.select_by_value(value)
                if attempt == 0:  # Only print on first attempt
                    print(f"Selected subgroup: {DROPDOWN_VALUES.get(value, value)}")
            except NoSuchElementException:
                print(f"Warning: Value '{value}' not found in dropdown. Skipping...")
                return []
            
            # Small delay to let the selection register
            time.sleep(0.5)
            
            # Wait for and find the View Report button
            view_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="View Report"]'))
            )
            
            # Click the button
            view_button.click()
            
            # Wait for the table to appear with a longer timeout
            try:
                # Wait for table to be present and stable
                wait.until(
                    EC.presence_of_element_located((By.ID, 'tblStateReport'))
                )
                # Additional small wait for table content to fully render
                time.sleep(1)
                
                # Extract data
                data = get_data(driver, value, wait_timeout)
                if data:
                    return data
                else:
                    # If table appeared but no data, try again
                    if attempt < max_retries:
                        continue
                    return []
                    
            except TimeoutException:
                if attempt < max_retries:
                    print(f"  Table did not appear, will retry...")
                    continue
                else:
                    print(f"Warning: Table did not appear after {max_retries + 1} attempts for {value}")
                    return []
        
        except TimeoutException as e:
            if attempt < max_retries:
                print(f"  Timeout error, will retry...")
                continue
            print(f"Error: Timeout waiting for elements for subgroup {value}: {e}")
            return []
        except NoSuchElementException as e:
            if attempt < max_retries:
                print(f"  Element not found, will retry...")
                continue
            print(f"Error: Element not found for subgroup {value}: {e}")
            return []
        except Exception as e:
            if attempt < max_retries:
                print(f"  Error occurred, will retry: {e}")
                continue
            print(f"Error handling subgroup {value}: {e}")
            return []
    
    return []


def select_school(driver, wait_timeout=30):
    print("SELECTING SCHOOL")
    wait = WebDriverWait[Any](driver, wait_timeout)

    select_element = wait.until(
            EC.presence_of_element_located((By.NAME, DATA_TYPE_NAME))
        )
  
    # Wait for the select to be clickable
    wait.until(EC.element_to_be_clickable((By.NAME, DATA_TYPE_NAME)))
    
    # Create Select object and select the value
    select = Select(select_element)
    
    # Check if the value exists in the dropdown
    try:
        select.select_by_value("School")
        print(f"Selected school")
    except NoSuchElementException:
        print(f"Warning: Value school not found in dropdown. Reloading...")
        driver.refresh()
        
    
    # Small delay to let the selection register
    time.sleep(0.5)

      # Wait for and find the View Report button
    view_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//button[text()="View Report"]'))
    )
    
    # Click the button
    view_button.click()

    time.sleep(5)


def main():
    """
    Main function to scrape graduation rate data for all subgroups.
    """
    driver = None
    if len(sys.argv) < 2:
        print("Usage: python graduation_rate_scraper.py <data_type> [district | school]")
        sys.exit(1)

    try:
        data_type = sys.argv[1]

        if data_type not in ['school', 'district']:
            print('Unsupported data type Please use school or district as an argument')
            sys.exit(1)

        driver = webdriver.Chrome()
        
        # Navigate to the page
        print(f"Navigating to {URL}...")
        driver.get(URL)
        
        # Wait for page to load - wait for a key element to be present
        wait = WebDriverWait[WebDriver](driver, 30)
        wait.until(
            EC.presence_of_element_located((By.NAME, DROPDOWN_NAME))
        )
        print("Page loaded successfully.")

        

        if data_type == 'school':
            select_school(driver)
        # Collect data for all subgroups
        final_data = []
        total_subgroups = len(DROPDOWN_VALUES)
        successful = 0
        failed = 0
        
        for idx, (value, name) in enumerate[tuple[str, str]](DROPDOWN_VALUES.items(), 1):
            print(f"\n[{idx}/{total_subgroups}] Processing: {name} ({value})")
            
            try:
                data = handle_subgroup(driver, value, data_type=data_type)
                
                if data:
                    final_data.extend(data)
                    successful += 1
                    print(f"✓ Successfully extracted {len(data)} rows for {name}")
                else:
                    failed += 1
                    print(f"✗ No data extracted for {name}")
                    
            except Exception as e:
                failed += 1
                print(f"✗ Error processing {name}: {e}")
            
            # Small delay between requests to avoid overwhelming the server
            if idx < total_subgroups:
                time.sleep(2)
        
        # Create DataFrame and display results
        print(f"\n{'='*60}")
        print(f"Scraping complete!")
        print(f"Successful: {successful}/{total_subgroups}")
        print(f"Failed: {failed}/{total_subgroups}")
        print(f"Total rows collected: {len(final_data)}")
        print(f"{'='*60}")
        
        if final_data:
            df = pd.DataFrame(final_data)
            print(f"\nDataFrame shape: {df.shape}")
            print("\nFirst few rows:")
            print(df.head())
            
            # Save to CSV
            filename = f'MA_grad_rates_4yr_{data_type}_2024.csv'
            df.to_csv(filename, index=False)
            print(f"\n✓ Data saved to '{filename}'")
        else:
            print("\nWarning: No data was collected!")
            
    except Exception as e:
        print(f"Fatal error in main: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()
            print("Done.")

if __name__ == '__main__':
    main()