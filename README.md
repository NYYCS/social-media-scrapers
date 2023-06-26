The repository contains two scrapers
- one fully functional scrapy spider for Dianping
- one partially functional requests based spider for Xiaohongshu

## To Run:
### For the Dianping Spider:
1. Go to Dianping site and Login, get cookies on any request and put it in `COOKIE_STR`.
2. Go to a specific a shop webpage and get `_token` and `uuid` from request payload from `shopAside` AJAX request, put it in `TOKEN` and `UUID` respectively.
3. Run `scrapy runspider dianping.py -o dianping.csv`
4. `dianping.csv` will be created and it will contain all the data scraped.

### Dianping Spider Limitations
1. Need to change cookie often
    - This can be mitigated by rotating cookies
2. Will sometimes by IP blocked due to high frequency of requests
    - This can be avoided by implementing rate-limit

### For the XiaoHongShu Spider:
1. Go to XiaoHongSHu site and Login, get two specific cookies `a1` and `websession` and put it in `a1` and `websession` respectively.
2. Run `python xhs_testing.py`

### XiaoHongShu Spider Limitations
1. Doesn't scrape author related data
    - Converting the script to its scrapy spider form and using playwright can populate author data on page content paint.
    - After getting the initial note data, do another scrape specifically for getting author data using playwright.

## Questions:
### Question 1
A data engineer should have an overview of the whole data sourcing process. They have to decide what kind of approach is the most appropriate for each case. We would like for you to design a data sourcing pipeline and explain how we can store the resulting data for next step processing

We would like for you to create a schema on how we can source data from one of the three platforms mentioned in the introduction.:
1. What would the sourcing process look like from crawling the raw data to storing the data in the database?
2. What ant-scraping technology could be used for crawling the data?
3. What database technology should be used for storing the resulting data?
4. How should the processes that we use to go from the raw data to the
database be run? You can talk about what technologies you think we should use, how they should be run, how they are linked, etc.

```
For Dianping:
Due to Dianping being mostly an SSR-generated application and not having too much anti-bot measures. Thus, it doesn't really require a headless browser to overcome said anti-bot measure, Dianping can easily be scraped using the typical Scrapy pipeline, which is:
    - extract data from html page
    - cleaning and validating data
    - save data to DB
Dianping data is relatively unstrict, so using a NoSQL DB such as MongoDB may be better accommodate when encountering some exception to scraped data, an example of this is the `avg_price` currently is only per person but based on the returned data, it could change in the future.

For XiaoHongShu:
XiaoHongShu has a lot of anti-bot measures, a lot of the anti-bot measure needs to reversed-engineered in order to scrape data from the site. Thus, a headless browser such as playwright would be best to scrape XiaoHongShu. However, the current version XiaoHongShu anti-bot measure is reversed-engineered therefore in this implementation it is used to scrape JSON-based data from XiaoHongShu API endpoints.

XiaoHongShu data is also very nested compared to other websites, so NoSQL DB like MongoDB is suited for storing scraped XiaoHongShu data, XiaoHongShu interaction data is also constantly being updated, so MongoDB also offers much better flexibility for updating nested interaction values.

Thus an ideal scraping pipeline for XiaoHongShu would be:

[playwright-headless-browser] -- scrape data -> [scrapy - validation and clean item] -- pipeline -> [storing cleaned data to MongoDB]

However due to time - constraints I have currently implemented the bare-minimum of a spider capable of scraping xiaohongshu note related data at a very high speed.
```