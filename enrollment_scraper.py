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


URL = 'https://profiles.doe.mass.edu/statereport/gradsattendingcollege.aspx'
SUBGROUP_DROPDOWN_NAME = 'ddStudentGroup'
YEAR_DROPDOWN_NAME = 'ddYear'
ATTEND_RANGE_DROPDOWN_NAME = 'ddAttendRange'
DATA_TYPE_NAME = 'ddReportType'


SUBGROUP_DROPDOWN_VALUES = {
    "AI": "American Indian or Alaska Native",
    "AS": "Asian",
    "BL": "Black or African American",
    "HS": "Hispanic or Latino",
    "MR": "Multi-Race, Not Hispanic or Latino",
    "HP": "Native Hawaiian or Other Pacific Islander",
    "WH": "White",
    "HIGH": "High Needs",
    "LEP": "English Learners",
    "LOWINC": "Low Income",
    "ECODIS": "Economically Disadvantaged",
    "SPED": "Students with Disabilities",
    "F": "Female",
    "M": "Male"
}

YEAR_DROPDOWN_VALUES = {
    "2020": "2019-20",
    "2021": "2020-21",
    "2022": "2021-22",
    "2023": "2022-23",
    "2024": "2023-24"
}

ATTEND_RANGE_DROPDOWN_VALUES = {
    "MARCH": "March",
    "16_MONTH": "16 Months",
}

def reset_page_state(driver, data_type, year, attend_range=None, wait_timeout=30):
    """
    Reload the page and reset to the correct data type, year, and attend range.
    
    Args:
        driver: Selenium WebDriver instance
        data_type: 'school' or 'district'
        year: Year string (e.g., '2019-20')
        attend_range: Attend range value (e.g., 'MARCH' or '16_MONTH')
        wait_timeout: Maximum time to wait for elements (seconds)
    """
    wait = WebDriverWait[Any](driver, wait_timeout)
    
    print(f"  Reloading page and resetting to {data_type}, year {year}...")
    driver.refresh()
    
    # Wait for page to load
    wait.until(
        EC.presence_of_element_located((By.NAME, SUBGROUP_DROPDOWN_NAME))
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
        except Exception as e:
            print(f"  Warning: Could not reset data type: {e}")
    
    # Reset year if provided
    if year:
        try:
            select_element = wait.until(
                EC.presence_of_element_located((By.NAME, YEAR_DROPDOWN_NAME))
            )
            select = Select(select_element)
            select.select_by_visible_text(year)
            time.sleep(0.5)
        except Exception as e:
            print(f"  Warning: Could not reset year: {e}")
    
    # Reset attend range if provided
    if attend_range:
        try:
            select_element = wait.until(
                EC.presence_of_element_located((By.NAME, ATTEND_RANGE_DROPDOWN_NAME))
            )
            select = Select(select_element)
            select.select_by_value(attend_range)
            time.sleep(0.5)
        except Exception as e:
            print(f"  Warning: Could not reset attend range: {e}")

    # Click View Report to apply the changes
    try:
        view_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[text()="View Report"]'))
        )
        view_button.click()
        time.sleep(2)
    except Exception as e:
        print(f"  Warning: Could not click View Report: {e}")


def map_year(year):
    """
    Map year format from '2019-20' to '2020'.
    
    Args:
        year: Year string in format 'YYYY-YY'
    
    Returns:
        str: Year in format 'YYYY'
    """
    correct_year = '20' + str(int(year.split('-')[1]) + 1)
    return correct_year


def get_capture_period(attend_range):
    """
    Get the capture period string from attend range value.
    
    Args:
        attend_range: Attend range value code (e.g., 'MARCH' or '16_MONTH')
    
    Returns:
        str: Capture period string ('12 Month' or '16 Month')
    """
    attend_range_name = ATTEND_RANGE_DROPDOWN_VALUES.get(attend_range, '')
    
    if attend_range_name == 'March':
        return '12 Month'
    elif attend_range_name == '16 Months':
        return '16 Month'
    return 'Unknown'

def get_data(driver, value, year, attend_range, wait_timeout=30):
    """
    Extract data from the college enrollment table.
    
    Args:
        driver: Selenium WebDriver instance
        value: Subgroup value code
        year: Year string (e.g., '2019-20')
        attend_range: Attend range value code
        wait_timeout: Maximum time to wait for table to appear (seconds)
    
    Returns:
        list: List of dictionaries containing row data
    """
    wait = WebDriverWait[Any](driver, wait_timeout)
    data = []
    
    try:
        # Wait for the table to appear
        table = wait.until(
            EC.presence_of_element_located((By.ID, 'teacherprogram'))
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
                if len(cells) < 12:
                    continue
                
                result = {
                    'year': map_year(year),
                    'capture_period': get_capture_period(attend_range),
                    'entity_name': cells[0].text.strip() if cells[0].text else '',
                    'entity_code': cells[1].text.strip() if cells[1].text else '',
                    'breakdown': SUBGROUP_DROPDOWN_VALUES.get(value, value),
                    'High School Graduates (#)': cells[2].text.strip() if len(cells) > 2 and cells[2].text else '',
                    'Attending Coll./Univ. (#)': cells[3].text.strip() if len(cells) > 3 and cells[3].text else '',
                    'Attending Coll./Univ. (%)': cells[4].text.strip() if len(cells) > 4 and cells[4].text else '',
                    'Private Two-Year (%)': cells[5].text.strip() if len(cells) > 5 and cells[5].text else '',
                    'Private Four-Year (%)': cells[6].text.strip() if len(cells) > 6 and cells[6].text else '',
                    'Public Two-Year (%)': cells[7].text.strip() if len(cells) > 7 and cells[7].text else '',
                    'Public Four-Year (%)': cells[8].text.strip() if len(cells) > 8 and cells[8].text else '',
                    'MA Community College (%)': cells[9].text.strip() if len(cells) > 9 and cells[9].text else '',
                    'MA State University (%)': cells[10].text.strip() if len(cells) > 10 and cells[10].text else '',
                    'Univ.of Mass. (%)': cells[11].text.strip() if len(cells) > 11 and cells[11].text else ''
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
        print(f"Error: Table 'teacherprogram' did not appear within {wait_timeout} seconds for subgroup {value}")
        return []
    except Exception as e:
        print(f"Error extracting data for subgroup {value}: {e}")
        return []
    
    return data


def handle_subgroup(driver, value, data_type=None, year=None, attend_range=None, max_retries=2, wait_timeout=30):
    """
    Handle selecting a subgroup and retrieving its data with retry logic.
    
    Args:
        driver: Selenium WebDriver instance
        value: Subgroup value code to select
        data_type: 'school' or 'district' (for retry/reload)
        year: Year string (e.g., '2019-20')
        attend_range: Attend range value code
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
                    reset_page_state(driver, data_type, year, attend_range, wait_timeout)
                else:
                    driver.refresh()
                    wait.until(
                        EC.presence_of_element_located((By.NAME, SUBGROUP_DROPDOWN_NAME))
                    )
                    time.sleep(1)
            
            # Wait for and find the select element
            select_element = wait.until(
                EC.presence_of_element_located((By.NAME, SUBGROUP_DROPDOWN_NAME))
            )
            
            # Wait for the select to be clickable
            wait.until(EC.element_to_be_clickable((By.NAME, SUBGROUP_DROPDOWN_NAME)))
            
            # Create Select object and select the value
            select = Select(select_element)
            
            # Check if the value exists in the dropdown
            try:
                select.select_by_value(value)
                if attempt == 0:  # Only print on first attempt
                    print(f"Selected subgroup: {SUBGROUP_DROPDOWN_VALUES.get(value, value)}")
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
                    EC.presence_of_element_located((By.ID, 'teacherprogram'))
                )
                # Additional small wait for table content to fully render
                time.sleep(1)
                
                # Extract data
                data = get_data(driver, value, year, attend_range, wait_timeout)
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
    """
    Select 'School' from the data type dropdown.
    
    Args:
        driver: Selenium WebDriver instance
        wait_timeout: Maximum time to wait for elements (seconds)
    """
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
        print("Selected school")
    except NoSuchElementException:
        print("Warning: Value 'School' not found in dropdown. Reloading...")
        driver.refresh()
        return
    
    # Small delay to let the selection register
    time.sleep(0.5)

    # Wait for and find the View Report button
    view_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//button[text()="View Report"]'))
    )
    
    # Click the button
    view_button.click()

    time.sleep(5)


def select_year(driver, year, wait_timeout=30):
    """
    Select year from the year dropdown.
    
    Args:
        driver: Selenium WebDriver instance
        year: Year string (e.g., '2019-20')
        wait_timeout: Maximum time to wait for elements (seconds)
    """
    print(f"SELECTING YEAR: {year}")
    wait = WebDriverWait[Any](driver, wait_timeout)

    select_element = wait.until(
        EC.presence_of_element_located((By.NAME, YEAR_DROPDOWN_NAME))
    )
  
    # Wait for the select to be clickable
    wait.until(EC.element_to_be_clickable((By.NAME, YEAR_DROPDOWN_NAME)))
    
    # Create Select object and select the value
    select = Select(select_element)
    
    # Check if the value exists in the dropdown
    try:
        select.select_by_visible_text(year)
        print(f"Selected {year}")
    except NoSuchElementException:
        print(f"Warning: Value '{year}' not found in dropdown. Reloading...")
        driver.refresh()
        return
    
    # Small delay to let the selection register
    time.sleep(0.5)


def select_attend_range(driver, attend_range_value, wait_timeout=30):
    """
    Select attend range from the attend range dropdown.
    
    Args:
        driver: Selenium WebDriver instance
        attend_range_value: Attend range value code (e.g., 'MARCH' or '16_MONTH')
        wait_timeout: Maximum time to wait for elements (seconds)
    """
    attend_range_name = ATTEND_RANGE_DROPDOWN_VALUES.get(attend_range_value, attend_range_value)
    print(f"SELECTING ATTEND RANGE: {attend_range_name}")
    wait = WebDriverWait[Any](driver, wait_timeout)

    select_element = wait.until(
        EC.presence_of_element_located((By.NAME, ATTEND_RANGE_DROPDOWN_NAME))
    )
  
    # Wait for the select to be clickable
    wait.until(EC.element_to_be_clickable((By.NAME, ATTEND_RANGE_DROPDOWN_NAME)))
    
    # Create Select object and select the value
    select = Select(select_element)
    
    # Check if the value exists in the dropdown
    try:
        select.select_by_value(attend_range_value)
        print(f"Selected {attend_range_name}")
    except NoSuchElementException:
        print(f"Warning: Value '{attend_range_value}' not found in dropdown. Reloading...")
        driver.refresh()
        return
    
    # Small delay to let the selection register
    time.sleep(0.5)


def main():
    """
    Main function to scrape college enrollment data for all subgroups and attend ranges.
    """
    driver = None
    if len(sys.argv) < 3:
        print("Usage: python enrollment_scraper.py <data_type> <year>")
        print("  data_type: 'school' or 'district'")
        print("  year: '2019-20', '2020-21', '2021-22', '2022-23', or '2023-24'")
        sys.exit(1)

    try:
        data_type = sys.argv[1]
        year = sys.argv[2]

        if data_type not in ['school', 'district']:
            print('Unsupported data type. Please use "school" or "district" as an argument')
            sys.exit(1)
        
        if year not in ['2019-20', '2020-21', '2021-22', '2022-23', '2023-24']:
            print("The scraper supports only: '2019-20', '2020-21', '2021-22', '2022-23', '2023-24'")
            sys.exit(1)

        driver = webdriver.Chrome()
        
        # Navigate to the page
        print(f"Navigating to {URL}...")
        driver.get(URL)
        
        # Wait for page to load - wait for a key element to be present
        wait = WebDriverWait[WebDriver](driver, 30)
        wait.until(
            EC.presence_of_element_located((By.NAME, SUBGROUP_DROPDOWN_NAME))
        )
        print("Page loaded successfully.")

        # Set up initial page state
        if data_type == 'school':
            select_school(driver)  # This already clicks View Report
        
        # Select year (for both school and district)
        select_year(driver, year)
        
        # Click View Report to apply year selection
        # (Note: select_school already clicked View Report, but we need to apply year change)
        try:
            view_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="View Report"]'))
            )
            view_button.click()
            time.sleep(2)
        except Exception as e:
            print(f"Warning: Could not click View Report after selecting year: {e}")

        # Collect data for all subgroups and attend ranges
        final_data = []
        total_subgroups = len(SUBGROUP_DROPDOWN_VALUES)
        total_attend_ranges = len(ATTEND_RANGE_DROPDOWN_VALUES)
        total_combinations = total_subgroups * total_attend_ranges
        successful = 0
        failed = 0
        current_combination = 0

        # Process each attend range
        for attend_range_idx, (attend_range_value, attend_range_name) in enumerate(ATTEND_RANGE_DROPDOWN_VALUES.items(), 1):
            print(f"\n{'='*60}")
            print(f"[{attend_range_idx}/{total_attend_ranges}] Processing Attend Range: {attend_range_name} ({attend_range_value})")
            print(f"{'='*60}")
            
            # Select attend range (only need to change it if it's not the first one)
            if attend_range_idx > 1:
                select_attend_range(driver, attend_range_value)
                # Click View Report after changing attend range
                try:
                    view_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//button[text()="View Report"]'))
                    )
                    view_button.click()
                    time.sleep(2)
                except Exception as e:
                    print(f"Warning: Could not click View Report after selecting attend range: {e}")
            
            # Process each subgroup for this attend range
            for idx, (value, name) in enumerate(SUBGROUP_DROPDOWN_VALUES.items(), 1):
                current_combination += 1
                print(f"\n[{current_combination}/{total_combinations}] Processing: {name} ({value}) for {attend_range_name}")
                
                try:
                    data = handle_subgroup(driver, value, data_type=data_type, year=year, attend_range=attend_range_value)
                    
                    if data:
                        final_data.extend(data)
                        successful += 1
                        print(f"✓ Successfully extracted {len(data)} rows for {name} ({attend_range_name})")
                    else:
                        failed += 1
                        print(f"✗ No data extracted for {name} ({attend_range_name})")
                        
                except Exception as e:
                    failed += 1
                    print(f"✗ Error processing {name} ({attend_range_name}): {e}")
                
                # Small delay between requests to avoid overwhelming the server
                if current_combination < total_combinations:
                    time.sleep(2)

        
        # Create DataFrame and display results
        print(f"\n{'='*60}")
        print(f"Scraping complete!")
        print(f"Total combinations processed: {total_combinations}")
        print(f"Successful: {successful}/{total_combinations}")
        print(f"Failed: {failed}/{total_combinations}")
        print(f"Total rows collected: {len(final_data)}")
        print(f"{'='*60}")
        
        if final_data:
            df = pd.DataFrame(final_data)
            print(f"\nDataFrame shape: {df.shape}")
            print("\nFirst few rows:")
            print(df.head())
            
            # Save to CSV
            filename = f'MA_college_enrollment_{data_type}_{map_year(year)}.csv'
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
