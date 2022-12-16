from nested_lookup import nested_lookup
from googleapiclient.discovery import build
import pprint
import json
from urllib.request import urlopen
from bs4 import BeautifulSoup
import mysql.connector as mysql

def connect_to_db():
    HOST='127.0.0.1'
    DATABASE = "DBname"
    USER = "username"
    PASSWORD='password'
    db_connection = mysql.connect(host=HOST ,database=DATABASE, user=USER, password=PASSWORD)
    return db_connection

mysql_connection = connect_to_db()
mysql_cursor = mysql_connection.cursor()
mysql_cursor.execute('CREATE TABLE IF NOT EXISTS sg_mentions (link varchar(500), title varchar(500), snippet MEDIUMTEXT,                     outlet varchar(200), metatags JSON, page_text MEDIUMTEXT)')

my_api_key = "AIzaSyCrfyjeEfZDCYdug1JvMuf3dSSefJZbpbA"
my_cse_id = "632d5aeab601406f2"

# my_api_key = "AIzaSyDUy8NI5hlwiWAz36fRihK6Sh46Q0G0UiI"
# my_cse_id = "d7ca4c4f0e64877f7"

def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res

results = google_search('startup genome', my_api_key, my_cse_id, num=10, dateRestrict = 'd1',
                        exactTerms= "startup genome",safe = "active")

# with open("SG_current_1.json", "w") as outfile:
#     json.dump(results, outfile)

data= results.get("items")
for i in data:
    link= i.get("link")
    title= i.get("title")
    snippet = i.get("snippet")
    outlet = i.get("displayLink")
    meta = i.get("pagemap")
    metatags = meta.get("metatags")[0]
    
    page_text = None
    try:
        url = link
        html = urlopen(url).read()
        soup = BeautifulSoup(html)

        for script in soup(["script", "style"]):
            script.decompose()

        strips = list(soup.stripped_strings)
        page_text = ' '.join(map(str, strips))

    except BaseException as e:
        page_text = str(e)
        
    mysql_cursor.execute('insert into sg_mentions (link,title,snippet,outlet,metatags,page_text) values(%s,%s,%s,%s,%s,%s)',(link,title,
                    snippet, outlet, json.dumps(metatags), page_text))
    mysql_connection.commit()
        

def next_pages(loop_count,result_count):    
    for i in range(1,loop_count+1):
        results= None
        start_count = None
        start_count = (10*i)+1
        if start_count < result_count:
            results = google_search('startup genome', my_api_key, my_cse_id,start= start_count, num=10, 
                                    dateRestrict = 'd1',exactTerms= "startup genome",safe = "active")
            
#             with open(f"SG_next{start_count}.json", "w") as outfile:
#                 json.dump(results, outfile)
                
            search_count = int(results.get("searchInformation").get("totalResults"))
            if search_count !=0:
                data = results.get("items")
                for i in data:
                    link= i.get("link")
                    title= i.get("title")
                    snippet = i.get("snippet")
                    outlet = i.get("displayLink")
                    meta = i.get("pagemap")
                    metatags = meta.get("metatags")[0]

                    page_text = None
                    try:
                        url = link
                        html = urlopen(url).read()
                        soup = BeautifulSoup(html)

                        for script in soup(["script", "style"]):
                            script.decompose()

                        strips = list(soup.stripped_strings)
                        page_text = ' '.join(map(str, strips))

                    except BaseException as e:
                        page_text = str(e)

                    mysql_cursor.execute('insert into sg_mentions (link,title,snippet,outlet,metatags,page_text) values(%s,%s,%s,%s,%s,%s)',(link,title,
                                    snippet, outlet, json.dumps(metatags), page_text))
                    mysql_connection.commit()
                else:
                    break 
            
        else:
            pass



result_count = int(results.get("queries")["request"][0].get("totalResults"))
print("results for today", result_count)
if result_count > 10:
    loop_count= int(result_count/10)
    next_pages(loop_count,result_count)
else:
    pass

