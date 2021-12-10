import os
import json
import random
import tweepy
import boto3

def lambda_handler(event, context):
    s3 = boto3.resource("s3")

    bucketName = "lc-new-subjects"
    bucket = s3.Bucket(bucketName)

    # gets all objects in input folder + the folder object itself
    inputObjsAll = bucket.objects.filter(Prefix="input/")

    # gets keys for all input objects, excluding folder object
    inputKeys = [inputObj.key for inputObj in inputObjsAll if inputObj.key.split(".")[-1] == "json"]

    # terminate program if no input keys
    if len(inputKeys) == 0:
        raise RuntimeError("No input available from lc-new-subjects bucket.")

    # get input object with lowest-value key
    inputKey = min(inputKeys)
    inputObj = s3.Object(bucket_name=bucketName, key=inputKey)
    inputLst = json.loads(inputObj.get()["Body"].read())

    # get first tweet thread, remove from list
    tweetThread = inputLst.pop(random.randrange(len(inputLst)))

    # either write updated list back to bucket object, or delete bucket object if updated list is empty
    if len(inputLst) > 0:
        inputObj.put(Body=(json.dumps(inputLst, indent=2, default=str).encode('UTF-8')), ContentType="application/json")
    else:
        inputObj.delete()

    # initialize output object
    outputKey = inputKey.replace("input", "output")
    outputObj = s3.Object(bucket_name=bucketName, key=outputKey)

    # get output list if it already exists, otherwise create new
    if bool(list(bucket.objects.filter(Prefix=outputKey))):
        outputLst = json.loads(outputObj.get()["Body"].read())
    else:
        outputLst = []

    # tweepy setup
    twitterConsumerKey = os.environ.get("TWITTER_CONSUMER_KEY")
    twitterConsumerSecret = os.environ.get("TWITTER_CONSUMER_SECRET")
    twitterAccessToken = os.environ.get("TWITTER_ACCESS_TOKEN")
    twitterAccessTokenSecret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    auth = tweepy.OAuthHandler(twitterConsumerKey, twitterConsumerSecret)
    auth.set_access_token(twitterAccessToken, twitterAccessTokenSecret)
    api = tweepy.API(auth)

    # init results
    tweetThreadResults = []

    # begin tweet thread
    tweet = tweetThread[0]
    try:
        response = api.update_status(status=tweet)
    except tweepy.errors.HTTPException as err:
        result = {
            "success": False,
            "details": {
                "tweetAttempted": tweet,
                "error": err,
                "abortThread": True
            }
        }
        tweetThreadResults.append(result)

        # don't attempt other tweets in thread if intial tweet fails
        outputLst.append(tweetThreadResults)
        outputObj.put(Body=(json.dumps(outputLst, indent=2, default=str).encode('UTF-8')), ContentType="application/json")
        raise RuntimeError(f"Error occurred at the beginning of a Tweet thread. Thread aborted. See Tweet thread results: {tweetThreadResults}")
    else:
        lastId = response.id
        result = {
            "success": True,
            "details": {
                "tweetSucceeded": response.text,
                "tweetTime": str(response.created_at)
            }
        }
        tweetThreadResults.append(result)

    # continue tweet thread
    midThreadError = False
    for tweet in tweetThread[1:]:
        try:
            response = api.update_status(status=tweet, in_reply_to_status_id=lastId)
        except tweepy.errors.HTTPException as err:
            result = {
                "success": False,
                "details": {
                    "tweetAttempted": tweet,
                    "error": err,
                    "abortThread": False
                }
            }
            midThreadError = True
        else:
            result = {
                "success": True,
                "details": {
                    "tweetSucceeded": response.text,
                    "tweetTime": str(response.created_at)
                }
            }
        lastId = response.id
        tweetThreadResults.append(result)

    # append tweetThreadResults to output list and write back to bucket object
    outputLst.append(tweetThreadResults)
    outputObj.put(Body=(json.dumps(outputLst, indent=2, default=str).encode('UTF-8')), ContentType="application/json")
    if midThreadError:
        raise RuntimeError(f"Error occurred in the middle of a Tweet thread. Thread continued. See Tweet thread results: {tweetThreadResults}")
    else:
        print(tweetThreadResults)
        return "Success"
