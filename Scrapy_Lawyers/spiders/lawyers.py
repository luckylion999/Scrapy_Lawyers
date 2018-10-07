import scrapy
import math
import re
from Scrapy_Lawyers.items import LawyersItem
from urllib.parse import urljoin
from nameparser import HumanName


class AlibabaCrawler(scrapy.Spider):
    name = 'lawyers_crawler'
    allowed_domains = ['lawyers.com']
    start_urls = ['https://www.lawyers.com/find-a-lawyer/']
    unique_data = set()
    HEADER = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36'
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            callback=self.parse,
            headers=self.HEADER
        )

    def parse(self, response):
        state_list = response.xpath('//h3[contains(text(), "Search by STATES")]'
                                    '/following-sibling::div[1]/ul/li/a/@href').extract()
        for state in state_list:
            yield scrapy.Request(
                url=urljoin(response.url, state),
                callback=self.parse_city,
                headers=self.HEADER,
                dont_filter=True
            )

    def parse_city(self, response):
        city_list = response.xpath('//div[@id="panelCities"]/div[@class="tabs-content"]'
                                   '//ul[@class="row popular_items"]/li/a/@href').extract()
        for city in city_list:
            yield scrapy.Request(
                url=urljoin(response.url, city),
                callback=self.parse_firmlink,
                headers=self.HEADER,
                dont_filter=True
            )

    def parse_firmlink(self, response):
        firm_link = response.xpath('//div[@id="old-design-mobile"]'
                                   '//h2[@class="srl-name"]/a/@href').extract()
        for firm in firm_link:
            yield scrapy.Request(
                url=urljoin(response.url, firm),
                callback=self.parse_firmprofile,
                headers=self.HEADER,
                dont_filter=True
            )

    def parse_firmprofile(self, response):
        attorney_link = response.xpath('//h3[contains(text(), "Attorneys at This Firm")]/'
                                       'following-sibling::div[1]'
                                       '//div[@class="fp-attorney-details"]/a/@href').extract()
        for attorney in attorney_link:
            yield scrapy.Request(
                url=urljoin(response.url, attorney),
                callback=self.parse_detail,
                headers=self.HEADER,
                dont_filter=True
            )

    def parse_detail(self, response):
        item = LawyersItem()
        name = response.xpath('//h1[@class="profile-summary-title"]/text()').extract_first()
        item['FirstName'] = HumanName(name).first
        item['MiddleName'] = HumanName(name).middle
        item['LastName'] = HumanName(name).last
        phone = response.xpath('//a[contains(@class, "webstats-phone-click")]/@data-phonenum').extract()
        if not phone:
            phone = response.xpath('//a[@class="fb-p-phone"]/text()').extract()
        item['PhoneNumber'] = phone[0] if phone else ''
        fax = response.xpath('//div[@class="row profile-contact-information"]//span[@class="pc-right"]/text()').extract_first()
        item['Fax'] = fax.strip() if fax else ''
        item['Website'] = response.xpath('//div[@class="row profile-contact-information"]'
                                         '//span[@class="pc-right"]/a/text()').extract()
        address = response.xpath('//*[@class="pc-address"]/span[2]//text()').extract()
        item['Address'] = ' '.join([add.strip() for add in address])
        description = response.xpath('//div[@class="show-more-content"]/text()').extract()
        if not description:
            description = response.xpath('//div[@class="show-less-content"]/text()').extract()
        item['Description'] = [desc.strip() for desc in description] if description else ''
        avatar = response.xpath('//img[contains(@class, "ap-attorney-photo")]/@data-echo').extract()
        item['Avatar'] = 'https:' + avatar[0] if avatar else ''
        rating = response.xpath('//div[@class="break-space"]/big/strong/text()').extract()
        item['StarRating'] = rating[0] if rating else ''
        item['url'] = response.url

        yield item