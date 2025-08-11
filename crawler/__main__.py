from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from crawler.spiders.site_generic import SiteGenericSpider

if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())
    process.crawl(SiteGenericSpider)
    process.start()
