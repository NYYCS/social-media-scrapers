import requests
import execjs
import json
import pandas as pd

import time
import random
import math


def F():
    timestamp = str(math.floor(time.time() * 1000))
    if len(timestamp) < 13:
        timestamp = timestamp.ljust(13, "0")
    return timestamp


def J():
    t = int(F())
    r = random.randint(1, 2147483646)
    t <<= 64
    t += r
    return base36encode(t)


def base36encode(number):
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base36 = ""
    while number:
        number, i = divmod(number, 36)
        base36 = digits[i] + base36
    return base36.lower()


def get_notes(keyword, web_session, a1, *, page):
    headers = {
        "accept": "application/json, text/plain, */*",
        "cache-control": "no-cache",
        "content-type": "application/json;charset=UTF-8",
        "cookie": f"a1={a1}; web_session={web_session};",
        "origin": "https://www.xiaohongshu.com",
        "referer": "https://www.xiaohongshu.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "x-b3-traceid": "a31fffc0ee4f5d8f",
        "x-s-common": "",
    }

    data = {
        "keyword": keyword,
        "page": page,
        "page_size": 20,
        "search_id": J(),
        "sort": "general",
        "note_type": 0,
    }
    exc = execjs.compile(open("antispam.js", "r", encoding="utf-8").read())
    xs_xt = exc.call("get_xs", "/api/sns/web/v1/search/notes", data, a1)
    xs_xt["X-t"] = str(xs_xt["X-t"])
    headers.update(xs_xt)
    feed = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
    response = requests.post(
        url=feed,
        data=json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        ),
        headers=headers,
    )

    return response.json().get("data").get("items")


def feed(source_note_id, web_session, a1):
    headers = {
        "accept": "application/json, text/plain, */*",
        "cache-control": "no-cache",
        "content-type": "application/json;charset=UTF-8",
        "cookie": f"a1={a1}; web_session={web_session};",
        "origin": "https://www.xiaohongshu.com",
        "referer": "https://www.xiaohongshu.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "x-b3-traceid": "a31fffc0ee4f5d8f",
        "x-s-common": "",
    }
    data = {"source_note_id": source_note_id}
    exc = execjs.compile(open("antispam.js", "r", encoding="utf-8").read())
    xs_xt = exc.call("get_xs", "/api/sns/web/v1/feed", data, a1)
    xs_xt["X-t"] = str(xs_xt["X-t"])
    headers.update(xs_xt)
    feed = "https://edith.xiaohongshu.com/api/sns/web/v1/feed"
    response = requests.post(
        url=feed, data=json.dumps(data, separators=(",", ":")), headers=headers
    )
    payload = response.json()
    if payload["success"] is False:
        return None
    return response.json().get("data").get("items")[0]


def get_user(user_id, a1, websession):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "cookie": f"a1={a1}; web_session={websession}",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "macOS",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "x-b3-traceid": "9ac6343913834a97",
    }

    url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
    response = requests.get(url=url, headers=headers)


if __name__ == "__main__":
    web_session = "040069b3531057123c8fd56ead364bc00ebfb5"
    a1 = "18558141ceecja46nhwhntzx35cg4vis9fx0u13dr00000225083"

    dataset = {
        "note_id": [],
        "timestamp": [],
        "title": [],
        "content": [],
        "like_nr": [],
        "star_nr": [],
        "comment_nr": [],
        "user_id": [],
        "author_name": [],
        "user_url": [],
        "images": [],
    }

    for i in range(1, 6):
        notes = get_notes("上海酒吧", web_session, a1, page=i)

        for note in notes:
            note_id = note["id"]
            details = feed(note_id, web_session, a1)
            if details is None:
                continue
            details = details["note_card"]

            timestamp = details["time"]
            title = details["title"]
            content = details["desc"]
            interact = details["interact_info"]
            like_nr = interact["liked_count"]
            star_nr = interact["collected_count"]
            comment_nr = interact["comment_count"]
            user = details["user"]
            user_id = user["user_id"]
            author_name = user["nickname"]
            user_url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
            images = details["image_list"]
            images = [image["url"] for image in images]

            dataset["note_id"].append(note_id)
            dataset["timestamp"].append(timestamp)
            dataset["title"].append(title)
            dataset["content"].append(content)
            dataset["like_nr"].append(like_nr)
            dataset["star_nr"].append(star_nr)
            dataset["comment_nr"].append(comment_nr)
            dataset["user_id"].append(user_id)
            dataset["author_name"].append(author_name)
            dataset["user_url"].append(user_url)
            dataset["images"].append(images)

    df = pd.DataFrame(dataset)
    df.to_csv("xiaohongshu.csv")
