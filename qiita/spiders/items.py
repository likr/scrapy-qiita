# -*- coding: utf-8 -*-
import os
import json
import scrapy
from datetime import date, timedelta


TOKEN = os.environ['QIITA_TOKEN']


def parse_links(links):
    items = [link.split('; ') for link in links.split(', ')]
    return {rel[5:-1]: url[1:-1] for url, rel in items}


class ItemsSpider(scrapy.Spider):
    name = 'items'
    allowed_domains = ['qiita.com']

    def start_requests(self):
        requests = []
        now = date.today()
        # now = date(2011, 10, 1)
        delta = timedelta(days=7)
        start_date = date(2011, 9, 1)
        stop_date = start_date + delta
        while start_date < now:
            base = 'http://qiita.com/api/v2/items'
            query = 'created%3A%3E%3D{}+created%3A%3C{}'.format(
                start_date.strftime('%Y-%m-%d'),
                stop_date.strftime('%Y-%m-%d'))
            url = '{}?per_page=100&query={}'.format(base, query)
            requests.append(scrapy.Request(url, self.parse, headers={
                'Authorization': 'Bearer {}'.format(TOKEN)
            }))
            start_date = stop_date
            stop_date = start_date + delta
        return requests

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
