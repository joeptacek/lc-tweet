# lc-tweet

lc-tweet provides the underlying functionality for the [LC New Subjects](https://twitter.com/newSubjectsLC) Tweet bot.

`lambda_function.py` is designed to run as an AWS Lambda function (Python 3.9, x86_64). Every few hours, a new Tweet thread is retrieved from a JSON file located in an S3 bucket. JSON files are manually generated and uploaded using [lc-scrape](https://github.com/joeptacek/lc-scrape).

`python.zip` contains associated dependencies (boto3 and tweepy) to be uploaded as a Lambda layer.
