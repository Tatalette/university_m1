from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class CrawlingSpider(CrawlSpider):
    name= "imdb"
    allower_domains = ["www.imdb.com"]
    start_urls = ["https://www.imdb.com/"]
    rules = ( Rule(LinkExtractor()),)

    def parse_item(self,response):
        yield {
            "title":response.css(".product_main h1::text").get(),
            "price":response.css(".price_color::text").get(),
            "availability":response.css(".availability::text")[1].get().strip()   
        }