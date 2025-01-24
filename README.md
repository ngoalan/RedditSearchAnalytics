# Reddit Data Crawler

## Overview of the System

### a. Architecture
The system's architecture is designed around a Python script (`reddit_crawler.py`) controlled through a Bash shell script (`crawler.sh`). The Python script leverages the **PRAW library** (Python Reddit API Wrapper) to interact with Reddit's API in a structured manner, enabling easy adjustments and scalability. 

- **Multithreading:** Enhances data fetching efficiency by processing multiple threads in parallel.  
- **Rate-Limiting:** Implemented using semaphores to manage API calls and prevent exceeding Reddit's API usage limits, ensuring compliance with the terms of service.

---

### b. Crawling or Data Collection Strategy
The data collection process involves the following steps:
1. **Command-Line Argument Parsing:** The target subreddits, the number of posts to fetch per subreddit, and the depth of comment threads to explore are specified as arguments.
2. **Fetching Posts:** The script fetches top posts from the specified subreddits using Reddit's API.  
3. **Exploring Comments:** Iteratively explores comments for each post up to the specified depth, structuring the data to preserve the context and threading of discussions.  
4. **Data Output:** The structured data is saved into JSON files for further analysis.

---

### c. Methodology
- The subreddits to scrape, post limits, and comment depth are passed as parameters to the shell script.
- **Functions:**
  - `crawl_multiple_subreddits`: Fetches data from multiple subreddits simultaneously.
  - `crawl_subreddit`: Handles data fetching for a single subreddit.  

#### Process:
1. Retrieve post IDs for the subreddit and store them in `submission_ids`.
2. Loop through each post ID and fetch details such as:
   - `selftext`, `title`, `id`, `score`, `permalink`, and comments up to the specified depth.
3. Use `process_submission` to gather and structure this data.
4. Save the collected data into a JSON file.

---

### d. Data Structures Employed
The script utilizes the following data structures:
- **Set:** Keeps track of already processed post IDs to avoid duplicates.
- **Semaphore:** Controls concurrency levels for API requests to balance speed and compliance with rate limits.
- **Dictionaries:** Manage dynamic data access and manipulation.
- **JSON Files:** Efficiently handle large datasets and ensure data persistence during the collection process.

---

## How to Use
1. Clone this repository.
2. Update the required parameters (subreddits, post limits, comment depth) in the shell script `crawler.sh`.
3. Run the crawler using:
   ```bash
   bash crawler.sh


<img width="773" alt="Screenshot 2025-01-24 at 2 16 55 AM" src="https://github.com/user-attachments/assets/98a96632-9e87-4398-ab74-c820667e7123" />
<img width="778" alt="Screenshot 2025-01-24 at 2 16 44 AM" src="https://github.com/user-attachments/assets/09d73cfa-3a03-469d-b3d1-4a8193f6011d" />
<img width="831" alt="Screenshot 2025-01-24 at 2 18 18 AM" src="https://github.com/user-attachments/assets/b2b0f40d-f188-440b-a043-53cd614f84eb" />
