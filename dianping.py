import scrapy
import pyjson5
import urllib.parse
import json

from http.cookies import SimpleCookie

USER_AGENT = """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"""
TOKEN = "eJxVT11rgzAU/S/3OWjid3xzpGOu1LJqA6P0wdo2Oqt1idW2o/99ETbY4ML5uOfAvV8g4z2EBGPsEATDQUIIxMCGBwh6pTde4HvUIj5xLIqg+O9R20Wwk5xBuAmIhwKLbCdjpfWGOA5GFOMt+kNtrGfKxDoCZd93KjTNcRyNfZW3XdUKozg3pirPnfnBjuk9idlsxpmI7FifBLraZFPVtSkiLpmMejI05j/Y/+qFfkaXVCVazQ6v1yxVjvo8rhYq4+t5IIbsZt0SvpZ3JYYo6upL/vbMzZN7kZVXyqZeXjtfKM7mok937zg5RQwXTy9LeHwDiIBYsw=="
UUID = "760fb8e0-139f-0d8e-f387-9431bd3bca01.1687692011"
COOKIE_STR = """WEBDFPID=9z6z01u9x05x5v461x6w78836xv21w89811u751390697958w898977x-2003052009201-1687692008489WIAKIGQ75613c134b6a252faa6802015be905512902; _lxsdk_cuid=188f248663bc8-0f64569e9a3f25-1b525634-13c680-188f248663bc8; _lxsdk=188f248663bc8-0f64569e9a3f25-1b525634-13c680-188f248663bc8; _hc.v=760fb8e0-139f-0d8e-f387-9431bd3bca01.1687692011; qruuid=e083625f-bfbd-44a4-97e5-4010d7069ef8; dplet=2745fc9aed923f038798e2229555b39f; dper=9e6001edecd1bbfedd350b1a9a24263ac5c764d595b603c60444fcb0e4072cc3fc845acc0f6b3abfc10d80b445198acf98e6c15a1b936af5e4bd9984bf2c375e; ll=7fd06e815b796be3df069dec7836c3df; ua=Jason%E5%AD%A6%E7%90%9B; ctu=a2bef1fdb8c4754c01ba9a51f8967f3b72aa6d909a0d4cbf5d79907d68aa7dda; Hm_lvt_602b80cf8079ae6591966cc70a3940e7=1687692057; s_ViewType=10; _lxsdk_s=188f248663b-5d2-fc3-bea%7C%7C81; Hm_lpvt_602b80cf8079ae6591966cc70a3940e7=1687692120"""

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
    start_urls = ["https://www.dianping.com/shanghai/ch30/g133p5"]
    count = 0
    page = 5

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
    
        

