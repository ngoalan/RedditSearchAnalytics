Overview of system
a. Architecture:
The system's architecture is designed around a Python script (reddit_crawler.py)
which is controlled through a Bash shell script (crawler.sh). The Python script is powered
by the PRAW library (Python Reddit API Wrapper), which interacts with Reddit's API in
a structured manner. This allows for easy adjustments and scalability. The script supports
multithreading, which enhances the efficiency of data fetching by processing multiple
threads in parallel. Rate-limiting is implemented using semaphores to manage API calls
and prevent exceeding Reddit's API usage limits, ensuring the crawler operates within the
terms of service.
b. Crawling or Data Collection Strategy:
The data collection process begins by parsing command-line arguments to
determine the target subreddits, the number of posts to fetch per subreddit, and the depth
of comment threads to explore. The script fetches top posts from the specified subreddits
using the Reddit API and then iteratively explores the comments of each post up to the
specified depth. Each post and its comments are processed in real-time, and the data is
structured to preserve the context and threading of discussions.
c. Methodology:
The subreddits we want to scrape, the post and comment limits, are passed as
parameters to shell script. We created two functions, crawl_multiple_subreddits to get the
data from multiple subreddits simultaneously and crawl_subreddit function to get the
data from a single subreddit. Firstly we get the ids of all the posts of that subreddit and
have stored it in submission_ids. We loop through each of the post ids and get the post
CS172 Project
details using the process_submission function. In this function process_submission, we
get the ‘selftext’, ‘title’, ‘id’, ‘score’, ‘permalink’ and ‘comments’ till the comment depth
which was passed as a parameter to the shell script for each post. Once the collection is
done for all the post ids in the submission_ids list, we dump the data into a json file.
d. Data Structures Employed:
The script uses data structures for efficient data management. A set is used to
keep track of already processed IDs, ensuring no duplicate data processing. A Semaphore
controls the concurrency level of network requests, to maintain a balance between speed
and compliance with API rate limits. Data is stored in dictionaries, which allows for
dynamic data access and manipulation before being saved to JSON files to efficiently
handle large data while preventing data loss during the collection process.
