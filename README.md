# lc-tweet

lc-tweet provides the underlying functionality for the [LC New Subjects](https://twitter.com/newSubjectsLC) Tweet bot.

`lambda_function.py` is intended to run on AWS Lambda (Python 3.9, x86_64). This is configured to accept incoming EventBridge events every few hours. Upon receiving an event, a new Tweet thread is retrieved from a JSON file located in an S3 bucket. JSON files are manually generated and uploaded using [lc-scrape](https://github.com/joeptacek/lc-scrape).

`python.zip` contains associated dependencies (boto3 and tweepy) to be uploaded as a Lambda layer.
