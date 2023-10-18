import boto3
import sys
import json
import string
import requests
import datetime
from urllib.parse import quote

loc = 'Manhattan, NY'
CUISINES = ["indian", "italian", "ethiopian", "american", "mexican", "japanese", "french", "spanish", "chinese"]
limit = 50

API_KEY = '2GzY81wdyHH2o4lc8Ts8mImXTQwpJzsuR8VQldAg0t11bZhtXSZJkTnnZ7uG7UQ2rxKCcN-zbij9HKlhB8yqEpfl9YS1PASViZpgsp9DYeIHrZfEuO2k4Jl6xRT5Y3Yx'
API_HOST = 'https://api.yelp.com'
searchaddr = '/v3/businesses/search'

def getresponse(cuisine, offset):
    urlparams = {
        'term': "{} restaurant".format(cuisine),
        'location': loc,
        'limit': limit,
        'offset': offset
    }
    headers = {
        'Authorization': 'Bearer %s' % API_KEY,
    }
    response = requests.get(API_HOST + searchaddr, headers=headers, params=urlparams)
    return response.json()

def getrestos(cuisine):
    offset = 0
    restolist = []
    tot = 1000
    while len(restolist) <= 1000:
        response = getresponse(cuisine, offset)
        if tot > response.get('total', 1000):
            tot = response.get('total', 1000)
        result = response.get('businesses', None)
        if result is None:
            break
        if len(result) == 0:
            break
        restolist += result
        offset = offset + limit
        print("Got {0}/{1} restaurants for cuisine {2}".format(len(restolist), tot, cuisine))
    return restolist

if __name__ == '__main__':
    for c in CUISINES:
        resto = getrestos(c)
        with open("./newdata_{}.json".format(c), "w") as f:
            for r in resto:
                data = {
                    "Business ID": r['id'],
                    "Name": r['name'],
                    "Address": r['location']['address1'],
                    "Coordinates": {
                        "Latitude": r['coordinates']['latitude'],
                        "Longitude": r['coordinates']['longitude']
                    },
                    "Number of Reviews": r['review_count'],
                    "Rating": r['rating'],
                    "Zip Code": r['location']['zip_code'],
                    "CuisineType": {
                        "S": c
                    },
                    "InsertedAtTimestamp": {
                        "N": str(datetime.datetime.now().timestamp())
                    }
                }
                f.write(json.dumps(data, indent=4) + ',' +'\n')
        print("{0}: {1} entries".format(c, len(resto)))
