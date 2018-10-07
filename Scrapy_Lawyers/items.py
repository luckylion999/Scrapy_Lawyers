import scrapy


class LawyersItem(scrapy.Item):
    FirstName = scrapy.Field()
    MiddleName = scrapy.Field()
    LastName = scrapy.Field()
    PhoneNumber = scrapy.Field()
    Fax = scrapy.Field()
    Website = scrapy.Field()
    Address = scrapy.Field()
    Description = scrapy.Field()
    Avatar = scrapy.Field()
    StarRating = scrapy.Field()
    url = scrapy.Field()
