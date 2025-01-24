import praw
from prawcore.exceptions import TooManyRequests, RequestException
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import re
import time
import logging
import os
from functools import wraps

logging.basicConfig(level=logging.INFO)

# Initialize PRAW with your Reddit application credentials
reddit = praw.Reddit(
    client_id='',     # Replace 'your_client_id' with your actual client ID
    client_secret='',  # Replace 'your_client_secret' with your actual client secret
    user_agent='{project} by /u/{username}'  # Replace with your application's name and Reddit username
)

# Shared set for tracking processed IDs, and a lock for thread-safe operations
processed_ids = set()
id_lock = threading.Lock()

request_semaphore = threading.Semaphore(50)
wait_time = 100


# Rate limiter decorator
def rate_limited(max_per_minute):
    min_interval = 60.0 / float(max_per_minute)

    def decorate(func):
        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            with request_semaphore:
                result = func(*args, **kwargs)
                time.sleep(min_interval)
                return result

        return rate_limited_function

    return decorate


@rate_limited(0.6)  # Delay set to maintain 100 queries per minute limit
def rate_limited_api_call():
    # Simulate an API call
    print(f"API call made by {threading.current_thread().name} at {time.time()}")


@rate_limited(wait_time)
def get_comments(comment, depth=0):
    comments_list = []
    if depth > 0:
        retry_delay = 5  # Initial backoff delay in seconds
        max_retries = 3  # Maximum number of retries

        for attempt in range(max_retries):
            try:
                with request_semaphore:  # Acquire semaphore before expanding comments
                    comment.refresh()  # This line makes a network call
                    # time.sleep(10)
                break  # If successful, exit the retry loop
            except TooManyRequests as e:
                logging.error(f"Rate limit exceeded while fetching comments: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            except Exception as e:
                logging.error(f"An unexpected error occurred while fetching comments: {e}")
                break  # Exit the loop on other exceptions

        # Proceed to process comments if the refresh was successful
        for reply in comment.replies:
            comments_list.append({
                'id': reply.id,
                'body': reply.body,
                'score': reply.score,
                'links': re.findall(r'https?://\S+', reply.body)
            })
            replies = get_comments(reply, depth - 1)
            if replies:
                comments_list[-1]['replies'] = replies
    return comments_list


# @rate_limited(wait_time)
def process_submission(submission_id, comment_depth, subreddit):
    # Fetch the submission by ID
    try:
        submission = reddit.submission(id=submission_id)
    except TooManyRequests as e:
        logging.error(f"Rate limit exceeded for getting the submission: {e}. Retrying...")
        time.sleep(1)  # Backoff before retrying
        return process_submission(submission_id, comment_depth, subreddit)  # Retry the function

    with id_lock:
        if submission.id in processed_ids:
            return None  # Skip duplicate
        processed_ids.add(submission.id)  # Mark as processed

    try:
        post_details = {
            'selftext': submission.selftext,
            'title': submission.title,
            'id': submission.id,
            'score': submission.score,
            'url': submission.url,
            'permalink': submission.permalink,
            'comments': []
        }
    except TooManyRequests as e:
        logging.error(f"Rate limit exceeded for loading attributes: {e}. Retrying...")
        time.sleep(1)  # Backoff before retrying
        return process_submission(submission_id, comment_depth, subreddit)  # Retry the function
    # Load all comments
    submission.comments.replace_more(limit=None)
    for top_level_comment in submission.comments:
        comment_details = {
            'id': top_level_comment.id,
            'body': top_level_comment.body,
            'score': top_level_comment.score,
            'replies': get_comments(top_level_comment, comment_depth)
        }
        post_details['comments'].append(comment_details)

    # Append post details to the subreddit's JSON file
    file_path = f'reddit_data_{subreddit}.json'
    # with threading.Lock():  # Ensure thread-safe write operation
    if os.path.exists(file_path):
        with open(file_path, 'r+') as file:
            # Load existing data and append the new post
            data = json.load(file)
            data.append(post_details)
            file.seek(0)
            json.dump(data, file, indent=4)
    else:
        with open(file_path, 'w') as file:
            json.dump([post_details], file, indent=4)

    return post_details


# Assuming the get_comments function and process_submission function are defined elsewhere in your script
def crawl_subreddit(subreddit, post_limit, comment_depth):
    reddit_data = {}
    submission_ids = []

    max_retries = 5  # Maximum number of retries
    backoff_factor = 1.5  # Backoff multiplier
    base_delay = 60  # Base delay in seconds (start with 60 seconds)

    # Consider adding a delay here to respect the rate limit when fetching submission IDs
    @rate_limited(wait_time)  # Adjust the wait_time as needed
    def fetch_submission_ids():
        return [submission.id for submission in reddit.subreddit(subreddit).hot(limit=post_limit)]

    for attempt in range(max_retries):
        try:
            submission_ids = fetch_submission_ids()
            break  # Exit the retry loop if successful
        except TooManyRequests as e:
            wait = base_delay * (backoff_factor ** attempt)
            logging.error(f"Rate limit exceeded while fetching submission IDs: {e}. Retrying in {wait} seconds...")
            time.sleep(wait)
        except RequestException as e:
            logging.error(f"Request exception occurred: {e}. Retrying...")
            time.sleep(base_delay)  # Simple backoff for other request-related exceptions
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            break  # Break the loop on other exceptions

    if not submission_ids:
        logging.error("Failed to fetch submission IDs after retries.")
        return reddit_data

    for sub_id in submission_ids:
        post_details = process_submission(sub_id, comment_depth, subreddit)
        if post_details:
            reddit_data[post_details['id']] = post_details
            logging.info(f"Processed post in {subreddit}: {post_details['id']}")

    # with ThreadPoolExecutor(max_workers=1) as executor2:  # Adjusted to respect the rate limit
    #     future_to_id = {executor2.submit(process_submission, sub_id, comment_depth, subreddit): sub_id for sub_id in submission_ids}
    #     print(subreddit)
    #     for future in as_completed(future_to_id):
    #         post_details = future.result()
    #         if post_details:  # Filter out skipped submissions
    #             reddit_data[post_details['id']] = post_details
    #             logging.info(f"Processed post in {subreddit}: {post_details['id']}")

    return reddit_data


def crawl_multiple_subreddits(subreddits, post_limit, comment_depth):
    all_data = {}

    with ThreadPoolExecutor(max_workers=3) as executor:  # Ensure this is reasonable
        futures = {executor.submit(crawl_subreddit, subreddit, post_limit, comment_depth): subreddit for subreddit in subreddits}

        for future in as_completed(futures):
            subreddit_data = future.result(timeout=300)
            subreddit_name = futures[future]  # Get the subreddit name associated with this future
            all_data[subreddit_name] = subreddit_data
            logging.info(f"Completed crawling for subreddit: {subreddit_name}")

    # Save the collected data
    with open('reddit_data_multiple.json', 'w') as outfile:
        json.dump(all_data, outfile, indent=4)

    return all_data


# List of subreddits to crawl
subreddits_to_crawl = []# ['books', 'ucr']
# Example usage: Crawl the specified subreddits, each with a limit of 10 posts and a comment depth of 2
print(crawl_multiple_subreddits(subreddits_to_crawl, 1200, 13))


