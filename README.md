# Massachusetts Graduation Rate Scraper

A Python web scraper that collects graduation rate data from the Massachusetts Department of Education website. This tool automatically extracts comprehensive graduation statistics for schools or districts across multiple demographic subgroups and saves everything to a CSV file.

## What It Does

This scraper visits the Massachusetts DOE graduation rates report page and systematically collects data for 15 different demographic subgroups, including:

- **Racial/Ethnic Groups**: American Indian or Alaska Native, Asian, Black or African American, Hispanic or Latino, Multi-Race, Native Hawaiian or Pacific Islander, White
- **Special Populations**: High Needs, English Learners, Low Income, Students with Disabilities, Foster Care, Homeless
- **Gender**: Female, Male

For each subgroup, it extracts detailed statistics including:
- Entity name and code
- Number of students in cohort
- Percentage graduated
- Percentage still in school
- Percentage non-graduate completers
- Percentage with high school equivalency
- Percentage dropped out
- Percentage permanently excluded

## Requirements

- **Python 3.9+**
- **Google Chrome** browser (the scraper uses Chrome via Selenium)
- **ChromeDriver** (automatically managed by webdriver-manager)

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The scraper accepts a command-line argument to specify whether you want **school-level** or **district-level** data.

### Scrape School Data

```bash
python graduation_rate_scraper.py school
```

This will create a file named `MA_grad_rates_4yr_school_2024.csv`

### Scrape District Data

```bash
python graduation_rate_scraper.py district
```

This will create a file named `MA_grad_rates_4yr_district_2024.csv`

## How It Works

1. **Opens Chrome browser** and navigates to the Massachusetts DOE graduation rates page
2. **Selects the report type** (School or District) based on your command-line argument
3. **Iterates through each demographic subgroup**:
   - Selects the subgroup from the dropdown
   - Clicks "View Report" to generate the data
   - Waits for the table to load
   - Extracts all rows of data
4. **Combines all data** into a single pandas DataFrame
5. **Saves everything** to a CSV file

The scraper includes robust error handling and automatic retry logic. If a table doesn't appear after clicking "View Report", the scraper will automatically:
- Reload the page
- Reset the form to the correct data type (school or district)
- Retry the request up to 2 additional times

This means if one subgroup fails due to a temporary network issue or page load problem, it will automatically retry before giving up. If one subgroup ultimately fails after all retries, the scraper will continue with the others. You'll see progress messages and retry notifications as it works through each subgroup.

## Output Format

The CSV file contains the following columns:

- `entity_name`: Name of the school or district
- `entity_code`: Unique code for the school or district
- `breakdown`: Demographic subgroup name
- `# in Cohort`: Number of students in the graduation cohort
- `% Graduated`: Percentage who graduated
- `% Still in School`: Percentage still enrolled
- `% Non-Grad Completers`: Percentage who completed but didn't graduate
- `% H.S. Equiv`: Percentage with high school equivalency
- `% Dropped Out`: Percentage who dropped out
- `% Permanently Excluded`: Percentage permanently excluded

## Notes

- The scraper includes delays between requests to avoid overwhelming the server
- Processing all 15 subgroups typically takes few minutes
- The browser window will open and you can watch the scraper work (though you can modify the code to run headless if preferred)
- **Automatic retry system**: If a table doesn't load, the scraper will automatically reload the page and retry up to 2 times before moving on
- If the website structure changes, you may need to update the element selectors in the code

## Troubleshooting

**"ChromeDriver not found" error:**
- Make sure Google Chrome is installed
- The webdriver-manager package should automatically download ChromeDriver, but if it fails, you can manually install ChromeDriver and add it to your PATH

**"Element not found" errors:**
- The website may have changed its structure
- Check your internet connection
- The scraper will automatically retry if elements aren't found, so you may see retry messages in the console
- If errors persist, try running the script again (sometimes the website is slow to respond)

**Seeing "Retry attempt" messages:**
- This is normal! The scraper automatically retries when tables don't load
- It will reload the page and try again up to 2 times
- If you see multiple retries for the same subgroup, it might indicate a temporary issue with the website

**No data in output:**
- Make sure you're using the correct argument (school or district)
- Check that the website is accessible
- Review the console output for specific error messages
- The scraper will show which subgroups succeeded and which failed in the final summary


