import os
import sys
import urllib
import base64
import requests 
import pymongo
from pymongo import MongoClient
import codecs
import unicodedata
import pprint
import time

def log(log_info):
    log_path = "/tmp/twitterapi.log"
    if(os.name == 'nt'): 
	    log_path = "C:\\temp\\twitterapi.log"
    with open(log_path, "a") as log_file:
        print(log_info)
        log_file.write(log_info)

def doUrlEncode(stringToEncode):
    tmp = urllib.urlencode( { 'x' : stringToEncode } )
    return tmp[2:] #Return just the encoded string e.g. [x][=][string...] 

def send_request(prepared_req):
    try:
        resp = requests.Session().send(prepared_req, timeout=5.0)
    except requests.exceptions.ConnectionError as e:
        resp = { "error": str(e) }
    except requests.exceptions.Timeout as e:
        resp = { "error": str(e) }
    except requests.exceptions.RequestException as e:
        resp = { "error": str(e) }
    if('error' in resp):
        log("\n\nERROR: " + resp['error'] + "\n\n")
    return resp

def get_bearer_token():
    api_key = doUrlEncode('KPkt9mbUGWP5MCl4gJkWlMYWQ')
    api_secret = doUrlEncode('MDr0Eiy7giEm5ajA1gPEmdU1jPw0nmyXLh5zF3noZAkSyl1737')
    b64_credential = base64.b64encode(api_key + ':' + api_secret)
    
    token_url = 'https://api.twitter.com/oauth2/token' 
    headers = {
        "Authorization"     :   "Basic " + b64_credential,
        "User-Agent"        :   "My Twitter App",
        "HOST"              :   "api.twitter.com",
        "Content-Type"      :   "application/x-www-form-urlencoded;charset=UTF-8",
        "Accept-Encoding"   :   "gzip"
    }
    data = "grant_type=client_credentials"
    log('* Sending twitter api request to get bearer token')
    resp = send_request(requests.Request('POST', token_url, headers = headers, data = data).prepare())
    if('error' in resp): 
        return 0
    else:
        return resp.json()['access_token']

def search_tweets(bearer_token, query):
    search_url = 'https://api.twitter.com/1.1/search/tweets.json?q=' + doUrlEncode(query)
    headers = {
        "Authorization"     :   "Bearer " + str(bearer_token),
        "User-Agent"        :   "My Twitter App",
        "HOST"              :   "api.twitter.com",
        "Accept-Encoding"   :   "gzip"
    }
    log("* Sending twitter api request to search tweets\n")
    resp = send_request(requests.Request('GET', search_url, headers = headers).prepare())
    return resp.json()['statuses']

def get_db_tweets():
    for dbrecord in db.tweetData.find().sort('created_at', pymongo.ASCENDING):
        log(dbrecord[u'text'])

def get_tweet_info(tweet):
	#pp = pprint.PrettyPrinter(indent=4)
	#pp.pprint(tweet)
    tweetInfo = str(tweet['id']) + " " + tweet['created_at'].encode('utf-8') + " " + tweet['text'].encode('utf-8')
    return tweetInfo[:100]

def check_db_connection(db_client):
    try:
        log("* Connecting to MongoDB.")
        db_client.server_info()
    except Exception: 
        log("Error connecting to MongoDB server on " + dbhost 
        + ".\nCheck server is installed and running.")
        exit()

def save_tweet_if_new(idx, tw):
    log( "[" + str(idx) + "] " + get_tweet_info(tw) )
    if db.tweetData.find({ 'id': tw['id'] }).count() <= 0:
        log("*** Saving tweet to DB: " + str(db.tweetData.insert( tw )))
    else:
        log("*** Already in database.")

#######################################################
# BEGIN SCRIPT
#######################################################

tweets =''
dbhost = "localhost"
db_client = MongoClient(dbhost, serverSelectionTimeoutMS=5)
check_db_connection(db_client)
db = db_client.test_database

bearer_token = 0 
bearer_token = get_bearer_token()
if(bearer_token == 0):
    log("\nproblem getting bearer_token\n")
	
#Periodically search for tweets containing key word e.g. "Barack Obama"
#Let the script run continuously until someone kills it
while True:
    tweets = search_tweets(bearer_token,"Barack Obama")
    log('* Found ' + str(len(tweets)) + ' tweets matching query.\n')

    #Print tweet info and save to database
    for idx, tw in enumerate(tweets):
        save_tweet_if_new(idx, tw)
    
    log("\n\n* Sleeping for 6 seconds...")
    time.sleep(6)
    log("* Total tweets in database: " + str(db.tweetData.find().count()))
