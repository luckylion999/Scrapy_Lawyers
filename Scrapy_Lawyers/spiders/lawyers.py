import scrapy
from Scrapy_Lawyers.items import LawyersItem
from urllib.parse import urljoin
from nameparser import HumanName
import re


TAG_RE = re.compile(r'<[^>]+>')


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
        item = LawyersItem()
        item['FirmSize'] = len(attorney_link)
        for attorney in attorney_link:
            if attorney not in self.unique_data:
                self.unique_data.add(attorney)
                yield scrapy.Request(
                    url=urljoin(response.url, attorney),
                    callback=self.parse_detail,
                    headers=self.HEADER,
                    dont_filter=True,
                    meta={'item': item}
                )

    def parse_detail(self, response):
        item = response.meta.get('item')
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
        website = response.xpath('//div[@class="row profile-contact-information"]'
                                         '//span[@class="pc-right"]/a/text()').extract()
        item['Website'] = get_separated(website)
        address = response.xpath('//*[@class="pc-address"]/span[2]//text()').extract()
        item['Address'] = ' '.join([add.strip().encode("cp1252").decode('utf_8', 'ignore') for add in address])
        desc_result = ''
        description = response.xpath('//div[@class="show-more-content"]/text()').extract()
        if not description:
            description = response.xpath('//div[@class="show-less-content"]/text()').extract()
        for desc in description:
            if desc.strip():
                desc_result += desc.strip() + ' '
        item['Description'] = desc_result
        avatar = response.xpath('//img[contains(@class, "ap-attorney-photo")]/@data-echo').extract()
        item['Avatar'] = 'https:' + avatar[0] if avatar else ''

        item['url'] = response.url

        law_firm_logo = response.xpath('//img[@itemprop="logo"]/@data-echo').extract()
        item['Law_Firm_Logo'] = 'https:' + law_firm_logo[0] if law_firm_logo else ''
        client_review = response.xpath('//a[@name="profile-client-reviews"]'
                                       '/following-sibling::div[@class="review-area"][1]'
                                       '//big/strong/text()').extract()
        client_review_num = response.xpath('//a[@name="profile-client-reviews"]'
                                           '/following-sibling::div[@class="review-area"][1]'
                                           '//big/span/text()').extract()
        item['Percentage_Recommended'] = client_review[0] if client_review else ''
        item['Client_Rating'] = client_review[1] if client_review else ''
        item['Client_Reviews_Number'] = client_review_num[1] if client_review_num else ''

        peer_rating = response.xpath('//a[@name="profile-peer-reviews"]'
                                     '/following-sibling::div[@class="review-area"][1]'
                                     '//big/strong/text()').extract()
        item['Peer_Rating'] = peer_rating[0] if peer_rating else ''

        selector = response.xpath('//div[@class="profile-detail-area"]/div[@class="row profile-detail-item"]')
        for sel in selector:
            title = sel.xpath('./div[contains(@class, "profile-sub-title-area")]/strong/text()').extract_first()
            if title == 'Position':
                item['Position'] = get_credential(sel, '')
            if title == 'Birth Information':
                item['BirthDate'] = get_credential(sel, 'birthdate')
            if title == 'Certifications':
                item['Certifications'] = get_credential(sel, '')
            if title == 'Languages':
                item['Languages'] = get_credential(sel, '')
            if title == 'Admission Details':
                item['Admission_Details'] = get_credential(sel, '')
            if title == 'Law School Attended':
                item['Law_School_Attented'] = get_credential(sel, 'low school')
            if title == 'Associations & Memberships':
                item['Association_Name'] = get_credential(sel, '')
        yield item


def get_credential(sel, param):
    data_list = sel.xpath('./div[contains(@class, "profile-credentials-content-area")]//text()').extract()
    if param == '':
        return get_separated(data_list)
    elif param == 'low school':
        data = sel.xpath('./div[contains(@class, "profile-credentials-content-area")]'
                         '/div[@class="truncate-text"]').extract_first()
        if not data:
            return ''
        law_school_result = ''
        list = data.split('<br><br>')
        for l in list:
            law_school_result += TAG_RE.sub('', l.replace('<br>', ' ')) + ' | '
        return law_school_result[:-3]
    elif param == 'birthdate':
        birth_result = ''
        for data in data_list:
            if data.strip():
                birth_result += data.strip() + ' '
        return birth_result


def get_separated(data_list):
    if not data_list:
        return ''
    result = ''
    for data in data_list:
        if data.strip():
            result += data + ' | '
    return result[:-3]
