import scrapy
import pyjson5
import urllib.parse
import json

from http.cookies import SimpleCookie

USER_AGENT = """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"""
TOKEN = "eJxd0V2PojAUBuD/0luJnAKF1mQvRtQRFnUUUWQyF6gEjXx0LIo62f++ZSKb3U1I+vT0bXsavtDZ2aMeBgADK+ianFEP4S50TaSgSsgVk1omY5SAZegK2v1TI7pOFbQ9rwao907kOtXwR1NYyPk7NgxQGMCH8hd1kF+TcWQEHaqKi56q1nXd3R/jgh+LtLsrc1UcSq6OcVVWqXW9ODN8dctItoTk1nzZbDWBKNjAskYYliKNTFkjTetEZwo2rUZYyvoWGAqmTc5gMse0RpRKWU9pAP+JtWLaH1lPETBb4TZHNFOexxoZ8l5Gv7vSWlnseVsr+ZxT8xw5xs+xaucT+StkVBzTQipxb0v/ZAg/0N888ww+vU0rX5/6kE3v9OYtVyPvcbzz/QQG9i0q3FmcRfdFnopwt7u5Hrg+IR0/K+uM8CqNPy9BHl02ZA4wtg/pdk243XfkcY+3BzX69uiwyaO8HHWSNV9s4zwWQdSZh7OJB+mA89XQHgaf0LfnsyA5HEPiJkUexetELaMsvGaLzfi1BqIKszhp/D4pxL3GjtWBWT8Qw5UbnV75efvzZfgyHmzDUPxAv34DwZys2A=="
UUID = "8d27eeb2-2ff9-6e23-623d-04db68af466f.1687576608"
COOKIE_STR = """fspop=test; s_ViewType=10; _lxsdk_cuid=188eb677635c8-0cec7b6a2bfa2a-1b525634-13c680-188eb677635c8; _lxsdk=188eb677635c8-0cec7b6a2bfa2a-1b525634-13c680-188eb677635c8; WEBDFPID=3u29955z86v8575uzzv8v7x21vz8y7v7811vy322157979582y45795y-2002936606867-1687576605393IKWMQSG75613c134b6a252faa6802015be905516671; _hc.v=8d27eeb2-2ff9-6e23-623d-04db68af466f.1687576608; dper=7e1ab37915101c8aa018afc7c5ef6ba1ae7b829238619fc6449100e4a5073b9ce126b1fff6e821ce4466826f1c47fe549d3184f874abb2381b53f7b86b1728df; qruuid=26b52a76-0445-4925-9f13-a3c9acdc39fc; cy=1; cye=shanghai; ll=7fd06e815b796be3df069dec7836c3df"""

cookies = SimpleCookie()
cookies.load(COOKIE_STR)

cookie_dict = {key: morsel.value for key, morsel in cookies.items()}
headers = {"User-Agent": USER_AGENT}


class BarItem(scrapy.Item):
    shop_id = scrapy.Field()
    shop_name = scrapy.Field()
    address = scrapy.Field()
    lat = scrapy.Field()
    long = scrapy.Field()
    avg_price = scrapy.Field()
    review_count = scrapy.Field()


class DianPingSpider(scrapy.Spider):
    name = "dianping"
    start_urls = ["https://www.dianping.com/shanghai/ch30/g133"]
    count = 0
    page = 5

    custom_delay = {
        'DOWNLOAD_SPEED': 3
    }

    def start_requests(self):
        yield self.make_request(
            "https://www.dianping.com/shanghai/ch30/g133",
            callback=self.parse_bar_listing,
        )

    def make_request(self, *args, **kwargs):
        return scrapy.Request(*args, cookies=cookie_dict, headers=headers, **kwargs)

    def parse_bar(self, response):
        scripts = response.css("script::text")
        for script in scripts:
            if "window.shop_config" in script.extract():
                bar_meta = script.extract()
                break
        config = pyjson5.loads(bar_meta[bar_meta.find("{") : bar_meta.rfind("}") + 1])
        item = BarItem()
        item["address"] = response.css("span#address ::text").extract_first()

        params = urllib.parse.urlencode(
            {
                "shopId": config["shopId"],
                "cityId": config["cityId"],
                "shopName": config["shopName"],
                "power": 5,
                "mainCategoryId": config["mainCategoryId"],
                "shopType": config["shopType"],
                "mainRegionId": config["mainRegionId"],
                "shopCityId": config["shopCityId"],
                "_token": TOKEN,
                "uuid": UUID,
                "platform": 1,
                "partner": 150,
                "optimusCode": 10,
                "originUrl": response.url,
            }
        )

        yield self.make_request(
            "https://www.dianping.com/ajax/json/shopDynamic/shopAside" + "?" + params,
            callback=self.process_bar_content,
            meta={
                "item": item,
                "params": params,
            },
        )

    def parse_bar_listing(self, response):
        links = response.css("div#shop-all-list ul li a[data-click-name='shop_title_click']::attr(href)").extract()
        for link in links:
            self.count += 1
            if self.count > 100:
                break
            yield self.make_request(link, callback=self.parse_bar)

        if self.count <= 100:
            self.page += 1
            yield self.make_request("https://www.dianping.com/shanghai/ch30/g133" + f"p{self.page}", callback=self.parse_bar_listing)

    def process_bar_content(self, response):
        item = response.meta["item"]
        params = response.meta["params"]
        data = json.loads(response.body)
        item["shop_id"] = data["shop"]["shopId"]
        item["shop_name"] = data["shop"]["shopName"]
        item["lat"] = data["shop"]["glat"]
        item["long"] = data["shop"]["glng"]

        yield self.make_request(
            "https://www.dianping.com/ajax/json/shopDynamic/reviewAndStar"
            + "?"
            + params,
            callback=self.process_bar_reviews,
            meta={"item": item},
        )

    def process_bar_reviews(self, response):
        item = response.meta["item"]
        data = json.loads(response.body)
        item["review_count"] = data["defaultReviewCount"]
        item["avg_price"] = data["avgPrice"]
        yield item
    
        

