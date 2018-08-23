#!/usr/bin/python
import requests
import sys
import os
import pprint
import time
import logging
#import click
#from multiprocessing import Process




logging.basicConfig(filename='hts_template_rebuild.log',format='%(asctime)s %(levelname)s %(message)s',level=logging.DEBUG)

oss_creds = ('opsapi@kvh.com','kVh!23456')
#oss_creds = ('osstasks@kvh.com','kVh!23456')

headers = {
	'authorization': "Basic b3BzYXBpQGt2aC5jb206a1ZoITIzNDU2",
	'content-type': "application/json",
	'cache-control': "no-cache",
	}


def get_oss_networks():
	database = {}
	r = requests.get("https://oss.minivsat.net/api/1.0/hts/collections/terminalnetworks",auth=oss_creds)
	data = r.json()
	for i in data:
		ips = i['eth0ip'].split('.')
		ip = "{}.{}.{}.{}".format(ips[0],ips[1],ips[2],"2")
		key = i['obj_parentid']
		value = ip
		database[key] = value
	return database

def get_oss_terminals():
	r = requests.get("https://oss.minivsat.net/api/1.0/hts/terminals/",auth=oss_creds)
	data = r.json()
	logging.debug('get_oss_terminals: {}'.format(data))
	return data

def post_oss_sweeper_templates(template_id, template_and_version, terminal_ids_exclude):
	url = "https://oss.minivsat.net/api/1.0/hts/sweepers/terminals/templates"

	payload = {'template_id': template_id, 'template_and_version': template_and_version,'terminal_ids_exclude': [terminal_ids_exclude]}

	response = requests.post(url, json=payload, auth=oss_creds)
	logging.debug('post_oss_sweeper_templates: Response Code: {}'.format(response.status_code))
	data = response.json()
	logging.debug('post_oss_sweeper_templates: {}'.format(data))
	return data

def get_oss_subscriber(subscriber_id):
	r = requests.get("https://oss.minivsat.net/api/1.0/hts/subscribers/?subscriber_id={}".format(subscriber_id),auth=oss_creds)
	data = r.json()
	logging.debug('get_oss_subscribers: {}'.format(data))
	return data

def patch_oss_subscriber(obj_id,plan):
	payload = {'subscriber_plan_id': plan, 'subsriber_detailed_report': 'true'}
	r = requests.patch("https://oss.minivsat.net/api/1.0/hts/subscribers/{}".format(obj_id),json=payload,auth=oss_creds)
	return r.status_code

def get_oss_async_status(obj_id):
	r = requests.get("https://oss.minivsat.net/api/1.0/hts/terminals/async/status?obj_id={}".format(obj_id),auth=oss_creds)
	data = r.json()
	print 'get_oss_async_status: {}'.format(data)
	#if data['complete'] == True:
	return data

def fix_qos(terminal_id):
	subscriberDetails = get_oss_subscriber(terminal_id + '-02')
	logging.debug('fix_qos: {}'.format(subscriberDetails))
	try:
		respCode =patch_oss_subscriber(subscriberDetails[0]['obj_id'],subscriberDetails[0]['subscriber_plan_id'])
		if respCode == 204:
			logging.info('{} qos fix success'.format(terminal_id))
		else:
			logging.warning('{} qos fix function returned {}'.format(terminal_id, respCode))
	except KeyError:
		logging.warning('{} qos fix failed {}'.format(terminal_id,subscriberDetails))


#def get_exclusions(allSubscribers):

#def terminal_rebuild(template_id, template_and_version, terminal_ids_exclude):


if __name__ == "__main__":
	logging.debug('START')
	
	# Check cmd line arguments
	# Ex. ./hts_termplate_rebuild.py <Region of Template to rebuild> <> 
	# Get all subscribers in OSS
	#allSubscribers = get_oss_terminals()

	# Post Template Rebuild
	templateRebuildJson = post_oss_sweeper_templates('CONUS_STANDARD', 'CONUS_STANDARD.Hayden' , 0)
	#print templateRebuildJson
	#templateRebuildJson = [{u'terminal': {u'terminal_id': u'40850458', u'terminal_ip_address': u'10.64.167.0/24', u'template_id': u'CONUS_STANDARD', u'coremodule_id': 85475, u'terminaltype_id': 2931, u'mgmtipaddress': u'10.242.128.50'}, u'obj_id': u'f013e56c-3b98-438e-b1e1-d03fd44c937a'}]

	# Monitor Template Rebuild Jobs
	isAsyncTaskPending = True
	pendingAsyncTasks = 0
	while isAsyncTaskPending:
		isAsyncTaskPending = False
		pendingAsyncTasks = 0

		time.sleep(60)

		for terminal in templateRebuildJson:
			status = get_oss_async_status(terminal['obj_id'])
			if status['complete'] == 'false':
				isAsyncTaskPending = True
			elif status['Result'] == 'true':
				pendingAsyncTasks +=1
				fix_qos(terminal['terminal']['terminal_id'])
				logging.info('{} rebuild complete'.format(terminal['terminal']['terminal_id']))
			elif status['Result'] == 'false':
				logging.warning('{} result: {} message: {}'.format(terminal['terminal']['terminal_id'], status['result'], status['message']))
				logging.warning('Payload for failed terminal: {}'.format(terminal))
		logging.info('{} pending async tasks'.format(pendingAsyncTasks))

	#for terminal in sweeperJson:
			
	# Create exclusion list

	# Make sweeper call
	# Monitor job status


	# .format(template_id, template_and_version, terminal_ids_exclude)