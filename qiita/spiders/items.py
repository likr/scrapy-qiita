# -*- coding: utf-8 -*-
import os
import json
import scrapy
import requests
from datetime import date, datetime, timedelta


TOKEN = os.environ.get('QIITA_TOKEN', '')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')


def parse_links(links):
    items = [link.split('; ') for link in links.split(', ')]
    return {rel[5:-1]: url[1:-1] for url, rel in items}


class ItemsSpider(scrapy.Spider):
    name = 'items'
    allowed_domains = ['qiita.com']

    def __init__(self, target_date=None, *args, **kwargs):
        super(ItemsSpider, self).__init__(*args, **kwargs)
        if target_date:
            self.target_date = target_date
        else:
            self.target_date = date.today().strftime('%y-%m-%d')

    @ classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ItemsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.engine_stopped,
                                signal=scrapy.signals.engine_stopped)
        return spider

    def start_requests(self):
        delta = timedelta(days=1)
        start_date = datetime.strptime(self.target_date, '%Y-%m-%d').date()
        stop_date = start_date + delta

        base = 'http://qiita.com/api/v2/items'
        query = 'created%3A%3E%3D{}+created%3A%3C{}'.format(
            start_date.strftime('%Y-%m-%d'),
            stop_date.strftime('%Y-%m-%d'))
        url = '{}?per_page=100&query={}'.format(base, query)
        yield scrapy.Request(url, self.parse, headers={
            'Authorization': 'Bearer {}'.format(TOKEN)
        })

    def parse(self, response):
        print(response.url)
        result = json.loads(response.body.decode())
        for item in result:
            yield item

        links = response.headers.get('Link').decode()
        links = parse_links(links)
        if 'next' in links:
            yield scrapy.Request(links['next'], self.parse, headers={
                'Authorization': 'Bearer {}'.format(TOKEN)
            })

    def engine_stopped(self):
        requests.post(WEBHOOK_URL, json={
            'content': f'''scraped
https://storage.cloud.google.com/vdslab-qiita/jsonl/qiita{self.target_date}.jsonl
```shellsession
gsutil cp gs://vdslab-qiita/jsonl/qiita{self.target_date}.jsonl .
```
'''
        })
