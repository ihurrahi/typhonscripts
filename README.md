# typhonscripts
Scripts to help with dealing with Typhon

## download_case_logs.py
This was borne out of needing to download a large number of case logs.
1. Create Clinical Notes for the case logs that need to be downloaded
2. Go to "View/Edit Case Logs", enter the date range to filter.
3. Download the webpages for each page (Right click -> Save As)
4. Run the script for each downloaded webpage `python download_case_logs.py path/to/webpage`
The URL used for exporting to pdf's doesn't require a cookie, but requesting the webpage does, which is why downloading the webpage is required for this to work.

## verify_totals.py
This verifies some of the requirements that should exist between certain aspects of the case logs. Verification is done through the totals.
1. Go to "Case Log Totals (Graphical)", enter the date range to filter.
2. Download the webpage for the totals.
3. Scroll down to the ICD10 categories, click "View All Categories", and download that webpage.
4. Scroll down to the CPT codes, click "View All", and download that webpage.
5. Run the script `python verify_totals.py` in the same path as the downloaded pages.
The totals page doesn't include all ICD10 categories and CPT codes, so they must be downloaded separately. These webpages also require a cookie to work.

TODO: move to verifying things at the case log level rather than the totals. This will require providing a username/password and will execute a lot slower, but will be more complete in what it verifies and can tell you exactly which case logs are the problem ones.
