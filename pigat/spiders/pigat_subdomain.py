import os
import re
import time
import scrapy
from bs4 import BeautifulSoup
from pigat.items import PigatItem_subdomain


class pigat_subdomain(scrapy.Spider):
	name = 'pigat_subdomain'
	handle_httpstatus_list = [500]

	def start_requests(self):
		url = self.url  # 待爬取 URL
		# 子域名查询
		subdoamin_url = 'https://www.dnsscan.cn/dns.html'
		subdoamin_data = {'ecmsfrom': '', 'show': '', 'classid': '1', 'keywords': url}
		subdomain_headers = {'Content-Type': 'application/x-www-form-urlencoded',
		                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'}
		yield scrapy.FormRequest(subdoamin_url, headers=subdomain_headers, meta={'url': url, 'temp_num': 1},
		                         formdata=subdoamin_data,
		                         callback=self.sub_subdomain)

	def sub_subdomain(self, response):
		url = response.meta['url']
		if response.status == 500:
			print(
				'\n\033[1;31;40m[{}]  {} 在第三方子域名查询网站上响应 500 ，无法进行 {} 的子域名信息查询\n\033[0m'.format(
					time.strftime('%Y-%m-%d %H:%M:%S'),
					url, url))
		else:
			temp_num = response.meta['temp_num']
			subdomain_soup = BeautifulSoup(response.text, 'html.parser')
			subdomain_amount = subdomain_soup.select('caption')[0].text  # 获取查询结果数量
			try:
				sub_pages_raw = subdomain_soup.select('#page')[0].select('a')
				sub_pages_total = int(sub_pages_raw[len(sub_pages_raw) - 2].text)  # 获取总共页数
			except:
				sub_pages_total = 1
				pass

			for i in subdomain_soup.select('span'):
				try:
					sub_pages_current = int(re.search('.*<span>(\d+)<.*', str(i)).group(1))  # 获取当前页数
				except:
					pass
			if temp_num == 1:
				print('\n\033[1;33;40m[{}] 正在被动收集 {} 的子域信息……\033[0m'.format(time.strftime('%Y-%m-%d %H:%M:%S'), url))
				print('\033[1;33;40m[{}] {}，搜索结果共 {} 页\033[0m'.format(time.strftime('%Y-%m-%d %H:%M:%S'),
				                                                      subdomain_amount, sub_pages_total))

			subdomain_element = subdomain_soup.select('td')
			for i in range(len(subdomain_element)):
				if (i - 1) % 5 == 0:
					subdomain_url = subdomain_element[i].text  # 获取当前页面子域url
				if (i - 3) % 5 == 0:
					subdomain_title = subdomain_element[i].text  # 获取当前页面子域标题
				if (i - 4) % 5 == 0:
					subdomain_status_code = subdomain_element[i].text  # 获取当前子域响应码

					print(
						'\033[1;32;40m[{}] {}\t{}\t{}\033[0m'.format(time.strftime('%Y-%m-%d %H:%M:%S'), subdomain_url,
						                                             subdomain_title,
						                                             subdomain_status_code))
					item = PigatItem_subdomain(
						url=url,
						subdomain_url=subdomain_url,
						subdomain_title=subdomain_title,
						subdomain_status_code=subdomain_status_code
					)
					yield item

			if sub_pages_total > sub_pages_current:
				subdoamin_url = 'https://www.dnsscan.cn/dns.html?keywords={}&page={}'.format(url,
				                                                                             (sub_pages_current + 1))
				subdoamin_data = {'ecmsfrom': '', 'show': '', 'classid': '1', 'keywords': url}
				subdomain_headers = {'Content-Type': 'application/x-www-form-urlencoded',
				                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'}
				yield scrapy.FormRequest(subdoamin_url, headers=subdomain_headers, meta={'url': url, 'temp_num': 2},
				                         formdata=subdoamin_data,
				                         callback=self.sub_subdomain)
