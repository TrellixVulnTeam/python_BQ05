#pylint: skip-file
'''settings'''
from funclib.iolib import wait_key
import fuckit
BOT_NAME = 'imgscrape'
SPIDER_MODULES = ['imgscrape.spiders']
NEWSPIDER_MODULE = 'imgscrape.spiders'



#SQL SERVER EXPORT
ITEM_PIPELINES = {'imgscrape.pipelines.UGCWriter': 10}
MSSQL_DUPLICATE_CHECK = False
MIN_BODY_LENGTH = 30

#IMAGE - DIDNT WORK
#IMAGES_STORE = 'C:/development/python/imgscrape/images'
#IMAGES_MIN_HEIGHT = 300
#IMAGES_MIN_WIDTH = 300

#FILE STORE
#ITEM_PIPELINES = {'scrapy.pipelines.files.FilesPipeline': 1}
#FILES_STORE = '/path/to/valid/dir'


#EASY CSV FEED
#ITEM_PIPELINES = {'scrapy.pipelines.files.FilesPipeline': 1}
#FEED_FORMAT = 'csv'
#FEED_URI = 'file:.c:/temp/test_feed.csv'


with fuckit:
    if  ITEM_PIPELINES == {'imgscrape.pipelines.UGCWriter': 10}:
        print('\nconnecting to mssql ....')
        import mmodb as _
        print('\nMSSQL:%s' %  _.ENGINE)
    else:
        print('\nFile:%s%s' % (FEED_URI, FILES_STORE))

    if wait_key('\nPress Q to quit, or any other key to start\n').lower() == 'q':
        exit()


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0'
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 8

#Throttling
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 4
CONCURRENT_REQUESTS_PER_IP = 4

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.2
AUTOTHROTTLE_MAX_DELAY = 8
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
