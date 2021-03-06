import os
from urlparse import urlparse
import unicodedata
import time

from datetime import datetime, date
from bs4 import BeautifulSoup
from urllib2 import urlopen
from ast import literal_eval
from flask import Flask, jsonify, render_template, request
from flask.ext import assets
# from flask.ext.pymongo
import pymongo

app = Flask(__name__)


MONGO_URL = os.environ.get('MONGOHQ_URL')


if MONGO_URL:
    # Get a connection
    mongo = pymongo.Connection(MONGO_URL)
    # Get the database
    db = mongo[urlparse(MONGO_URL).path[1:]]
    app.config['MONGO_USERNAME'] = 'luiz.neves7@gmail.com'
    app.config['MONGO_PASSWORD'] = 'Bigwave07'
    app.config['MONGO_DBNAME'] = 'app27873276'
else:
    # Not on an app with the MongoHQ add-on, do some localhost action
    mongo = pymongo.Connection('localhost', 27017)
    # mongo = pymongo(app)
    db = mongo['mongoData']


    env = assets.Environment(app)
    # print "past mongo"
    # Tell flask-assets where to look for our coffeescript and sass files.
    env.load_path = [
    	os.path.join(os.path.dirname(__file__), 'bootstrap/css'),
        os.path.join(os.path.dirname(__file__), 'sass'),
        os.path.join(os.path.dirname(__file__), 'coffee'),
        os.path.join(os.path.dirname(__file__), 'bower_components'),
    ]


    env.register(
        'js_all',
        assets.Bundle(
            'jquery/dist/jquery.min.js',
            'bootstrap.min.js',
            'd3.min.js',
            'dc.js',
            'crossfilter.js',
            'colorbrewer.js',
            assets.Bundle(
                'all.coffee',
                'chartFunctions.coffee',
                'helpers.coffee', 
                'listeners.coffee',
                'dashboardClass.coffee',
                'chartClass.coffee',
                #'three.coffee',
                #'map.coffee',
                #'all.coffee',
                filters=['coffeescript']
            ), 
            output='js_all.js'
        )
    )

    env.register(
        'css_all',
        assets.Bundle(
            'all.sass',
            filters=['sass','scss'],
            output='css_all.css'
        )
    )
print "right before app.route"
# print os.environ.get(__name__)

@app.route("/")
def index():
    print db
    print "in index"
    print os.getcwd()
    return render_template("/index.html")
    # return "HELLO PERSON"
@app.route("/newQuery")

def getQuery():
    queryString = request.args.get('query', 0, type=str).lower().strip()
    result = db.queries.find_one({'query':queryString},{'_id': False})
    if result is not None:
        return jsonify(result)
    else:
        finalArray = scrapeForQuery(queryString,True)
        return jsonify(query=queryString,dailyCounts=finalArray)
def scrapeForQuery(queryString, firstTry):
    response = urlopen("https://archive.org/details/tv?q="+queryString+"+AND+%28channel%3AWJLA+OR+channel%3AWRC+OR+channel%3AWTTG+OR+channel%3AWUSA+OR+channel%3AWBAL+OR+channel%3AWBFF+OR+channel%3AWJZ+OR+channel%3AWMAR+OR+channel%3AWNUV%29&rows=1")
    soup = BeautifulSoup(response,"html.parser")
    # print soup.diagnose()
    if soup.find(id="tvgraphclip") is not None:
        finalArray = parsePage(soup)
        print finalArray
        db.queries.save({'query':queryString,'dailyCounts':finalArray})
        return finalArray
    elif firstTry is True:
        print "##### trying again ######"
        time.sleep(3)
        scrapeForQuery(queryString, False)

    # print response
def parsePage(soup):
    stringScriptArray = unicode(soup.find(id="tvgraphclip").find("script").contents[0])
    parsedStringArray = "[[" + stringScriptArray.split("[[",1)[1].split("]]",1)[0] + "]]"
    numList = literal_eval(parsedStringArray)
    month_aggregate = dict()
    for [d,v] in numList:
        truncated = int(str(d)[:-3])    
        year_month = datetime.utcfromtimestamp(truncated).date().isoformat()[:-3]
        # If the entry was not present previously create one with the current value v
        if not month_aggregate.has_key(year_month):
            month_aggregate[year_month] = v
        else:
            # Otherwise add the value to the previous entry
            month_aggregate[year_month] += v

    # Create a JSON Array from the month_aggregate dictionary
    month_aggregate_json_list = [ {'value':v, 'key':k} for k, v in month_aggregate.iteritems() ]
    # print sorted(month_aggregate_json_list)
    return sorted(month_aggregate_json_list)

@app.route("/grabClips")

def getClips():
    print request.args
    year = request.args.get('year1',0, type=str)
    month = request.args.get('month1',0, type=str)
    day = request.args.get('day1',0, type=str)
    query = request.args.get('query',0, type=str).lower().strip()
    year2 = request.args.get('year2',0, type=str)
    month2 = request.args.get('month2',0, type=str)
    day2 = request.args.get('day2',0, type=str)
    print year,month,day,query
    # result = db.queries.find_one({'query':query},{'_id': False})

    clipObjects = parsePageForClips(year+month+day,year2+month2+day2,query)
    # queryString = request.args.get('date', 0, type=dict)
    # print datetime.isoformat(queryString)
    return jsonify(clips=clipObjects)

def parsePageForClips(firstDay,nextDay,query):
    print type(firstDay)
    # query="flood"
    # soup = BeautifulSoup(urlopen("https://archive.org/details/tv?q="+query+"+AND+%28channel%3AWJLA+OR+channel%3AWRC+OR+channel%3AWTTG+OR+channel%3AWUSA+OR+channel%3AWBAL+OR+channel%3AWBFF+OR+channel%3AWJZ+OR+channel%3AWMAR+OR+channel%3AWNUV%29+&rows=10&&time="+firstDay+"-"+nextDay+"))    
    soup = BeautifulSoup(urlopen('https://archive.org/details/tv?q='+query+'+AND+%28channel%3AWJLA+OR+channel%3AWRC+OR+channel%3AWTTG+OR+channel%3AWUSA+OR+channel%3AWBAL+OR+channel%3AWBFF+OR+channel%3AWJZ+OR+channel%3AWMAR+OR+channel%3AWNUV%29+&rows=10&&time='+firstDay+'-'+nextDay+''),"html.parser")
    # print soup
    clipObjects = []
    clips = soup.find_all("div",class_="sniptitle-search")
    for clip in clips:
        rawLink = clip.find('a')['href']
        parsedLink = rawLink.split('/details/')[1].split('?q=')[0]
        startTime = str(int(rawLink.split('start/')[1].split('/end')[0])-20)
        endTime = str(int(rawLink.split('/end/')[1])-20)
        srcLink = "https://archive.org/embed/"+parsedLink+"?start="+startTime+"&end="+endTime
        # print "##LINK##"
        # print srcLink
        # print "##SHOW##"
        show = clip.find('a').text
        # print "##STATION##"
        station = clip.find_all('div')[1].text
        # print "##DATE##"
        dte = clip.find_all('div')[2].text
        clipObjects.append({'station':station,'show':show,'link':srcLink,'date':dte})
        if len(clipObjects) > 20:
            break
    return clipObjects


if __name__ == "__main__":
    print "IN __main__"
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port,debug=True)