from scrapy.cmdline import execute
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # 得到目录
# execute(["scrapy", "crawl", "jobbole"])
execute(["scrapy", "crawl", "zhihu"])

