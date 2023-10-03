from ebaysdk.finding import Connection as finding
import json
import mysql.connector

api = finding (appid ='68bba84e8-9a4c6126', config_file=None)
savesrawfile = open("eBayAutoDataRaw.txt", "a", encoding = "utf-8")
PullAPartList = open("PullAPartList.txt", "r")
saveseBayAPIlogfile = open("eBayAPIlogfile.txt", "a", encoding = "utf-8")

mydb = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    passwd = 'XXXXXXX',
    database = 'eBayAutoListings',
    )
my_cursor = mydb.cursor()

#Slices the results from eBay.com query results, sets data elements to variables, and then adds them to mysql table 'eBayAutoListings'
data_response = ''
Make = ''
Model = ''
Metadata = ''


def Call_eBay():
    pagecount = 1
    global Make
    global Model
    global Metadata
    global data_response  
    for everyline in PullAPartList:
        Make = everyline[:everyline.index("|")]
        Model = everyline[everyline.index("|")+1:everyline.index("|",everyline.index("|")+1)]
        Metadata = everyline[everyline.index("$")+1:everyline.index("$",everyline.index("$")+1)]
        Keywords = everyline[everyline.rindex("|")+1:]
        api.execute("findCompletedItems", {
            "keywords" : "%s %s %s %s" %(Make , Model, Metadata, Keywords),
            "categoryId" : "6000",
            "itemFilter" : [
                {"name" : "EndTimeFrom", "value" : "2018-02-25T19:09:02.768Z"},
                {"name" : "Condition", "value" : "Used"},
                {"name" : "SoldItemsOnly", "value" : "True"}],
            "paginationInput" : [
                {"entriesPerPage" : "100"},
                {"pageNumber" : "%s" %(pagecount)}]
        })
        data_response = api.response.dict()
        if int(data_response["paginationOutput"]["totalEntries"]) == 0:
            skipped = ("Skipped: %s %s %s %s" %(Make , Model, Metadata, Keywords))
            print (skipped)
            saveseBayAPIlogfile.write(skipped + "\n")
            continue
        total_pages = int(data_response["paginationOutput"]["totalPages"])
        stats = data_response["paginationOutput"].items()
        Write_To_Database()
        # increments pagecount to pull down each subsequent page of results       
        while pagecount < 101:
            if total_pages > 1:
                if total_pages > pagecount:
                    pagecount = pagecount + 1
                    api.execute("findCompletedItems", {
                    "keywords" : "%s %s %s %s" %(Make , Model, Metadata, Keywords),
                    "categoryId" : "6000",
                    "itemFilter" : [
                        {"name" : "EndTimeFrom", "value" : "2018-02-25T19:09:02.768Z"},
                        {"name" : "Condition", "value" : "Used"},
                        {"name" : "SoldItemsOnly", "value" : "True"}],
                    "paginationInput" : [
                        {"entriesPerPage" : "100"},
                        {"pageNumber" : "%s" %(pagecount)}]
                    })
                    data_response = api.response.dict()
                    Write_To_Database()
                else:
                    pagecount = 101
            else:
                print ("%s %s %s %s %s" %(Make , Model, Metadata, Keywords, stats) + "\n")
                saveseBayAPIlogfile.write("%s %s %s %s %s" %(Make , Model, Metadata, Keywords, stats) + "\n")
                break
        if pagecount == 101:
            print ("%s %s %s %s %s" %(Make , Model, Metadata, Keywords, stats) + "\n")
            saveseBayAPIlogfile.write("%s %s %s %s %s" %(Make , Model, Metadata, Keywords, stats) + "\n")
            pagecount = 1

def Write_To_Database():
    for eachline in data_response["searchResult"]["item"]:
        itemId = str(eachline["itemId"])
        title = str(eachline["title"])
        soldprice = str(eachline["sellingStatus"]["currentPrice"]["value"])
        starttime = eachline["listingInfo"]["startTime"]
        starttimeonly = starttime[0:10]
        endtime = eachline["listingInfo"]["endTime"]
        endtimeonly = endtime[0:10]
        listingtype = str(eachline["listingInfo"]["listingType"])
        savesrawfile.write(str(data_response))
        add_command = 'INSERT INTO results (Make, Model, Metadata, ItemID, Price, Listed_Date, Sold_Date, Listing_Style, Title) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        add_data = (Make, Model, Metadata, itemId, soldprice, starttimeonly, endtimeonly, listingtype, title)
        my_cursor.execute(add_command,add_data)
        mydb.commit()

Call_eBay()
print ("Success")

#dkeys = data["searchResult"]["item"][0]["listingInfo"]["startTime"].keys()
#print (dkeys)
