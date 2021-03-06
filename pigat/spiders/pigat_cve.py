import time
import pymongo
import scrapy
from bs4 import BeautifulSoup
from pigat.items import PigatItem_cve


class pigat_beian(scrapy.Spider):
	name = 'pigat_cve'

	def start_requests(self):
		url = self.url  # 待爬取 URL
		cve_pools = []
		client = pymongo.MongoClient('localhost', 27017)  # 连接数据库
		collection = list(client['pigat']['pigat_shodan'].find({'url': url}))  # 读取数据
		for i in collection:  # 判断数据是否为空
			if i['shodan_vulns'] != '':
				cve_list = {}
				cve_list['sub_ip'] = i['sub_ip']
				cve_list['subdomain_url'] = i['subdomain_url']
				cve_list['cve_number'] = i['shodan_vulns']
				cve_pools.append(cve_list)
		if cve_pools == []:
			print(
				'\n\033[1;31;40m[{}] 数据库中未查询到 {} 的漏洞信息，无法进行 {} 的漏洞信息查询，请先获取 {} 的 shodan 信息\n\033[0m'.format(
					time.strftime('%Y-%m-%d %H:%M:%S'),
					url, url ,url))

		else:
			# cve查询
			print('\033[1;33;40m[{}] 正在被动收集 {} 的漏洞详情信息……\033[0m'.format(time.strftime('%Y-%m-%d %H:%M:%S'), url))
			headers = {
				'Content-Type': 'application/x-www-form-urlencoded',
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
			}
			for i in cve_pools:
				sub_ip = i['sub_ip']
				subdomain_url = i['subdomain_url']
				cve_number = i['cve_number']

				for j in cve_number:
					cve_url = 'http://www.cnnvd.org.cn/web/vulnerability/queryLds.tag'
					yield scrapy.FormRequest(cve_url, headers=headers, formdata={"qcvCnnvdid": j},
					                         meta={'url': url, 'cve_number': j, 'sub_ip': sub_ip,
					                               'subdomain_url': subdomain_url},
					                         callback=self.sub_cve)

	def sub_cve(self, response):
		url = response.meta['url']
		sub_ip = response.meta['sub_ip']
		cve_number = response.meta['cve_number']
		subdomain_url = response.meta['subdomain_url']
		cve_soup = BeautifulSoup(response.text, 'html.parser')
		cve_level = cve_soup.select('img')[3]['title']
		cve_title = cve_soup.select('.a_title2')[0].text.replace('\r', '').replace('\n', '').replace('\t', '').replace(
			' ', '')
		cve_url = 'http://www.cnnvd.org.cn' + cve_soup.select('.a_title2')[0]['href']
		print(
			'\033[1;32;40m[{}] {}\t{}\t{}\t{}\t{}\t{}\t{}\n\033[0m'.format(time.strftime('%Y-%m-%d %H:%M:%S'),
			                                                               url, cve_number,
			                                                               cve_level,
			                                                               cve_title,
			                                                               sub_ip, subdomain_url, cve_url))
		item = PigatItem_cve(
			url=url,
			cve_number=cve_number,
			cve_level=cve_level,
			cve_title=cve_title,
			sub_ip=sub_ip,
			subdomain_url=subdomain_url,
			cve_url=cve_url
		)
		yield item
