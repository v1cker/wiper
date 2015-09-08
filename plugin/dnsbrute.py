#!/usr/bin/env python
#-*- coding: UTF-8 -*-

'''
Information probing tool for penetration test
Copyright (c) 2014-2015 alpha1e0
See the file COPYING for copying detail
'''

import os
import socket
import multiprocessing
import re

from plugin.lib.tools import readList
from plugin.hostscan import HostScan
from init import log
from dbman.dbmanage import DBManage


class DnsBrute(multiprocessing.Process):
	'''
	Use wordlist to bruteforce subdomain.
	'''
	def __init__(self, url, projectID, dictlist):
		multiprocessing.Process.__init__(self)
		log.debug("init here")
		urlPattern = re.compile(r"^(?:http(?:s)?\://)?((?:[-0-9a-zA-Z_~!=:]+\.)+(?:[-0-9a-zA-Z_~!=:]+))")
		self.domain = urlPattern.match(url.strip()).group()
		self.projectID = projectID
		self.dictlist = [os.path.join("plugin","wordlist","dnsbrute",f) for f in dictlist]
		self.result = []
		#partDoman示例：aaa.com partDomain为aaa，aaa.com.cn partDomain为aaa
		pos = self.domain.rfind(".com.cn")
		if pos==-1: pos = self.domain.rfind(".")
		self.partDomain = self.domain if pos==-1 else self.domain[0:pos]
		#去掉domain前面的www
		pos = self.domain.find("www.")
		self.domain = self.domain if pos==-1 else self.domain[pos+4:]

		log.debug(self.dictlist+self.projectID+self.domain+self.partDomain)


	def checkDomain(self, domain):
		#这里使用python内置的gethostbyname来查询DNS记录
		try:
			ip = socket.gethostbyname(domain)
		except:
			return False
		return ip


	def bruteSubDomain(self):
		for dlist in self.dictlist:
			for line in readList(dlist):
				domain = line + "." + self.domain
				log.debug(domain)
				ip = self.checkDomain(domain)
				if ip:
					self.result.append(["",domain,ip,"","","","",""])


	def bruteTopDomain(self):
		dlist = os.path.join("plugin","wordlist","toplevel.txt")
		for line in readList(dlist):
			domain = self.partDomain + "." + line
			log.debug(domain)
			ip = self.checkDomain(domain)
			if ip:
				self.result.append(["",domain,ip,"","","","",""])


	def saveResult(self):
		dbcon = DBManage()

		sqlCmdP = "insert into tmp_host(title,url,ip,protocol,level,os,server_info,middleware,source,project_id) values('{0}', '{1}', '{2}', '{3}', '{4}')"

		for i in self.result:
			sqlCmd = sqlCmdP.format(i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7],"dnsbrute",self.projectID)
			log.debug(sqlCmd)
			dbcon.sql(sqlCmd)


	def run(self):
		self.bruteTopDomain()
		self.bruteSubDomain()
		self.result = HostScanner.getHttpHosts(self.result)
		self.saveResult()



