#!/usr/bin/python
import requests
import sys
import os
import pprint
import time
import logging
import pickle
import json

from multiprocessing import Pool


logging.basicConfig(filename='hts_template_rebuild_redux.log',format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

oss_creds = ()
oss_url = ''

headers = {
	'authorization': "Basic b3BzYXBpQGt2aC5jb206a1ZoITIzNDU2",
	'content-type': "application/json",
	'cache-control': "no-cache",
}


def get_oss_terminal(terminal_id):
	r = requests.get(
		"https://{}/api/1.0/hts/terminals/?terminal_id={}".format(oss_url,terminal_id), auth=oss_creds)
	data = r.json()
	return r.status_code, data

def get_oss_terminal_config(terminal_obj_id):
	r = requests.get(
		"https://{}/api/1.0/hts/terminals/{}".format(oss_url,terminal_obj_id), auth=oss_creds)
	data = r.json()
	return r.status_code, data

def post_oss_sweeper_templates(template_id, template_and_version, terminal_ids_exclude):
	url = "https://{}/api/1.0/hts/sweepers/terminals/templates".format(oss_url)

	payload = {'template_id': template_id, 'template_and_version': template_and_version,
			'terminal_ids_exclude': terminal_ids_exclude}

	response = requests.post(url, json=payload, auth=oss_creds)
	logging.debug(
		'post_oss_sweeper_templates: Response Code: {}'.format(response.status_code))
	data = response.json()
	logging.info('post_oss_sweeper_templates: {}'.format(data))
	return data

def put_oss_terminal(obj_id, payload):
	url = "https://{}/api/1.0/hts/terminals/{}".format(oss_url,obj_id)
	
	# Example payload
	# payload = { "obj_revision": 2, "enablestaticroutes": true, "static_ip_data_channel_id": 1703 }

	response = requests.put(url, json=payload, auth=oss_creds)
	#data = response.json()
	return response.status_code #, data

def get_oss_subscriber(subscriber_id):
	r = requests.get(
		"https://{}/api/1.0/hts/subscribers/?subscriber_id={}".format(oss_url,subscriber_id), auth=oss_creds)
	data = r.json()
	logging.debug('get_oss_subscribers: {}'.format(data))
	return r.status_code, data

def get_all_oss_subscriber():
	r = requests.get(
		"https://{}/api/1.0/hts/subscribers/".format(oss_url), auth=oss_creds)
	data = r.json()
	#logging.debug('get_oss_subscribers: {}'.format(data))
	return r.status_code, data

def get_all_oss_terminals():
	r = requests.get(
		"https://{}/api/1.0/hts/terminals/".format(oss_url), auth=oss_creds)
	data = r.json()
	#logging.debug('get_oss_subscribers: {}'.format(data))
	return r.status_code, data

def get_oss_subscriber_obj_id(obj_id):
	r = requests.get(
		"https://{}/api/1.0/hts/subscribers/{}".format(oss_url,obj_id), auth=oss_creds)
	data = r.json()
	#logging.debug('get_oss_subscribers: {}'.format(data))
	return r.status_code, data

def patch_oss_subscriber(obj_id, plan):
	payload = {'subscriber_plan_id': plan, 'subsriber_detailed_report': 'true'}
	r = requests.patch(
		"https://{}/api/1.0/hts/subscribers/{}".format(oss_url,obj_id), json=payload, auth=oss_creds)
	return r.status_code

def get_oss_async_status(obj_id):
	r = requests.get(
		"https://{}/api/1.0/hts/terminals/async/status?obj_id={}".format(oss_url,obj_id), auth=oss_creds)
	data = r.json()
	return r.status_code, data

def post_oss_terminal_EDk(edk, template_id, terminal_ids):
	url = "https://{}/api/1.0/hts/sweepers/terminals/customkeys".format(oss_url)

	payload = {'keys':  {"BEAM_SELECTOR": {"asc_mode": 1}}, 'template_id': template_id,
			'terminal_ids': terminal_ids}
	# {
	#   "keys": {"BEAM_SELECTOR": {"asc_mode": 1}},
	#   "template_id": "CONUS_STANDARD",
	#   "terminal_ids": [
	#     338378
	#   ]
	# }
	response = requests.post(url, json=payload, auth=oss_creds)
	logging.info('post_oss_terminal_EDk: Response Code: {}'.format(response.status_code))
	data = response.json()
	logging.debug('post_oss_terminal_EDk: {}'.format(data))
	return response.status_code, data
	
def get_oss_terminals_status(terminal_obj_id):
	r = requests.get(
		"https://{}/api/1.0/hts/terminals/{}/status".format(oss_url,terminal_obj_id), auth=oss_creds)
		
	data = r.json()
	#logging.debug('get_oss_subscribers: {}'.format(data))
	return r.status_code, data

def write_terminals_to_be_rebuilt_to_file(active_terminals):
	with open('terminals_to_be_rebuilt.pkl', 'wb') as output:
		pickle.dump(active_terminals, output)

def read_terminals_to_be_rebuilt_from_file():
	with open('terminals_to_be_rebuilt.pkl', 'rb') as input:
		return pickle.load(input)

def write_terminals_exception_to_file(active_terminals):
	with open('terminals_exception.pkl', 'wb') as output:
		pickle.dump(active_terminals, output)

def read_terminals_exception_from_file():
	with open('terminals_exception.pkl', 'rb') as input:
		return pickle.load(input)

def write_terminals_statics_to_file(active_terminals):
	with open('terminals_statics.pkl', 'wb') as output:
		pickle.dump(active_terminals, output)

def read_terminals_statics_from_file():
	with open('terminals_statics.pkl', 'rb') as input:
		return pickle.load(input)

def fix_qos(terminal):
	def apply_plan(subscriber):
		respCode = patch_oss_subscriber(subscriber['obj_id'], subscriber['subscriber_plan_id'])
		if respCode == 204:
			logging.info('{} plan apply success'.format(subscriber['subscriber_id']))
		else:
			logging.warning('{} plan apply failure {}'.format(subscriber['subscriber_id'],respCode))
	#hs_sub_resp_code, hs_sub = get_oss_subscriber(terminal+'-01')
	ul_sub_resp_code, ul_sub = get_oss_subscriber(terminal+'-02')

	# if hs_sub_resp_code == 200:
	# 	apply_plan(hs_sub)
	# else:
	# 	logging.warning('fix qos subscriber lookup failed {} {} {}'.format(terminal,ul_sub_resp_code, ul_sub))
	if ul_sub_resp_code == 200:
		apply_plan(ul_sub[0])
	elif ul_sub_resp_code == 404:
		logging.warning('fix qos subscriber does not exist')
	else:
		logging.warning('fix qos subscriber lookup failed {} {} {}'.format(terminal,ul_sub_resp_code, ul_sub))

# TODO Fix statics function does not handle template region changes
def fix_statics(terminal_id, static_payload):
	# Look up the obj_id
	status, terminal = get_oss_terminal(terminal_id)
	if status == 200:
		# new_terminal_config_status, new_terminal_config = get_oss_terminal_config(terminal[0]['obj_id'])
		# if new_terminal_config_status == 200:
		# 	new_data_channels = new_terminal_config['data_channels']
			# Loop through static payloads
		for payload in static_payload:
			# Post payload to fix satic
			status_code = put_oss_terminal(terminal[0]['obj_id'], payload)
			if status_code == 204:
				logging.info('{} static fixed for {}'.format(payload['static_ip_data_channel_id'],terminal_id))
			else:
				logging.warning('Error trying to fix {} static for {} {}'.format(payload['static_ip_data_channel_id'],terminal_id, payload))
	else:
		logging.warning('Error trying to fix static, unable to look up obj_id for {} {}'.format(terminal_id, terminal))


# def monitor_async(terminalJson):
# 	isPending = True
# 	while isPending:
# 		status = get_oss_async_status(terminalJson['obj_id'])
# 		try:
# 			isPending = not status['complete']
# 			if status['complete'] == True:
# 				if status['result'] == True:
# 					return (True, terminalJson)
# 				if status['result'] == False:
# 					logging.warning('{} result: {} message: {}'.format(
# 						terminalJson['terminal']['terminal_id'], status['result'], status['message']))
# 					logging.warning('Payload for failed terminal: {}'.format(terminalJson))
# 					return (False, terminalJson)
# 		except KeyError:
# 			isPending = False
# 		time.sleep(10)
# 	return (False, terminalJson)

def make_terminal_config_dict(some_obj_ids, destination_template):
	conus_dc = [1703,1704]
	emea_dc = [1705,1706]
	asia_dc = [1707,1708]

	if 'CONUS_STANDARD' in destination_template:
		dest_dc = conus_dc
	elif 'EMEA_STANDARD' in destination_template:
		dest_dc = emea_dc
	elif 'ASIA_STANDARD' in destination_template:
		dest_dc = asia_dc

	terminal_static_dict = {}

	for obj_id in some_obj_ids:
		# Pull terminals config based on obj_id
		term_config_response_code, term_config = get_oss_terminal_config(obj_id)

		if term_config_response_code == 200:
			# Var to hold payloads for terminals static fixes
			static_payload = []

			if term_config['data_channels'][0]['enablestaticroutes'] == True:
				# Create json payload to post in after terminal is rebuit
				static_payload.append({ "obj_revision": term_config['obj_revision'], "enablestaticroutes": True, "static_ip_data_channel_id": dest_dc[0] })
			
			if term_config['data_channels'][1]['enablestaticroutes'] == True:
				# Create json payload to post in after terminal is rebuit
				static_payload.append({ "obj_revision": term_config['obj_revision'], "enablestaticroutes": True, "static_ip_data_channel_id": dest_dc[1] })
			
			# Check if the list has some length
			if len(static_payload) > 0:
				terminal_static_dict[term_config['terminal_id']] = static_payload
		else:
			logging.warning('Failed to lookup terminal config for {} {} {}'.format(obj_id,term_config_response_code, term_config))
	#return dict
	#logging.info(terminal_static_dict)
	return terminal_static_dict

# This functions returns all terminals obj_ids, split into two lists
def hard_to_name_function(some_list,template_and_version_to_be_rebuilt):
	term_scode, terminals = get_all_oss_terminals()
	
	diff_list = []
	converted_input_list = []

	if term_scode == 200:
		for terminal in terminals:
			if terminal['contactnote'] == template_and_version_to_be_rebuilt:
				if terminal['terminal_id'] not in some_list:
					diff_list.append(terminal['obj_id'])
				else:
					converted_input_list.append(terminal['obj_id'])
			
	else:
		logging.warning('create diff list get_all_oss_terminals() returned {}'.format(terminals))

	return diff_list, converted_input_list

def chunks(l, n):
	n = max(1, n)
	return (l[i:i+n] for i in xrange(0, len(l), n))

def shall_we_proceed():
	uinput = raw_input("Press 'c' to continue or 'a' to abort...")
	if uinput == 'c':
		logging.info('Continue...')
		return True
	else:
		logging.info('ABORT')
		return False
	
if __name__ == "__main__":
	logging.info('START')

	# Load in config
	config = json.load(open('config.json'))
	# Init rebuild dict
	rebuild_parameters = config['rebuild_parameters']

	# Determine enviroment
	if rebuild_parameters['environment'] == 'prod':
		oss_creds = (config['prod_environment']['prod_usr'], config['prod_environment']['prod_pw'])
		oss_url = config['prod_environment']['prod_url']
	elif rebuild_parameters['environment'] == 'dev':
		oss_creds = (config['dev_environment']['dev_usr'], config['dev_environment']['dev_pw'])
		oss_url = config['dev_environment']['dev_url']
	else:
		logging.warning('Invaild environment.. Try "prod" or "dev" ')
		sys.exit(0)

	# log rebuild parameters
	logging.info('Rebuild Parameters')
	logging.info('Environment: {}'.format(rebuild_parameters['environment']))
	logging.info('Destination newest version of: {}'.format(rebuild_parameters['template_id']))
	logging.info('Source template and version: {}'.format(rebuild_parameters['template_and_version']))
	logging.info('{} list: {}'.format(rebuild_parameters['list_type'],rebuild_parameters['terminal_list']))

	rebuild_list = []
	exception_list = []
	terminal_config_dict = {}

	if rebuild_parameters["continue_previous_deploy"]:
		try:
			rebuild_list = read_terminals_to_be_rebuilt_from_file()
			exception_list = read_terminals_exception_from_file()
			terminal_config_dict = read_terminals_statics_from_file()
			logging.info('{} active terminals loaded from file!'.format(rebuild_list))
		except:
			logging.critical("failed to load active terminal file {}".format(e))
			sys.exit(0)
	else:
		# We are either have a rebuild list or an exception list
		if rebuild_parameters['list_type'] == 'rebuild':
			exception_list, rebuild_list = hard_to_name_function(rebuild_parameters['terminal_list'], rebuild_parameters['template_and_version'])
		elif rebuild_parameters['list_type'] == 'exception':
			rebuild_list, exception_list = hard_to_name_function(rebuild_parameters['terminal_list'], rebuild_parameters['template_and_version'])
		else:
			logging.warning('Invalid list type.. Try "rebuild" or "exception"')
			sys.exit(0)

		# Make a dict of terminals static ips configs
		terminal_config_dict = make_terminal_config_dict(rebuild_list, rebuild_parameters['template_id'])

		write_terminals_statics_to_file(terminal_config_dict)
		write_terminals_to_be_rebuilt_to_file(rebuild_list)
		write_terminals_exception_to_file(exception_list)
		
		logging.info('Saved rebuild and exception_list to files')

	logging.info('exception list: {}'.format(exception_list))
	logging.info('Terminals with statics: {}'.format(terminal_config_dict.keys()))
	logging.info('There are {} in the exception list'.format(len(exception_list)))
	logging.info('There are {} in the rebuild list'.format(len(rebuild_list)))
	logging.info('There are {} in the terminal config dictionary'.format(len(terminal_config_dict)))
	# Ask the user to verify the above config is going to do what they want
	if shall_we_proceed():
		chunk_size = rebuild_parameters["chunk_size"]
		chunk_number = 0
		while len(rebuild_list) > 0:
			rebuild_list = rebuild_list[chunk_size:]
			# Start rebuild process
			template_rebuild_json = post_oss_sweeper_templates(rebuild_parameters['template_id'], rebuild_parameters['template_and_version'] , (exception_list + rebuild_list))
			# Monitor Template Rebuild Jobs
			is_async_task_pending = True
			pending_async_tasks = len(template_rebuild_json)
			complete_obj_ids = []
			while is_async_task_pending:
				is_async_task_pending = False
				
				time.sleep(config['general']['async_task_status_check_interval'])

				for terminal in template_rebuild_json:
					if terminal['obj_id'] not in complete_obj_ids:
						status_code, status = get_oss_async_status(terminal['obj_id'])
						if status_code == 200:
							if status['complete'] == False:
								is_async_task_pending = True
							else:
								if status['result'] == True:
									logging.info(status)
									pending_async_tasks -=1
									# After terminal is rebuild NMS is out of sync with plan
									fix_qos(terminal['terminal']['terminal_id'])
									# After terminal is rebuilt static settings are lost in terminal config
									if terminal['terminal']['terminal_id'] in terminal_config_dict:
										fix_statics(terminal['terminal']['terminal_id'], terminal_config_dict[terminal['terminal']['terminal_id']])
									logging.info('{} rebuild complete'.format(terminal['terminal']['terminal_id']))

								else:
									pending_async_tasks -=1
									logging.warning('{} result: {} message: {}'.format(terminal['terminal']['terminal_id'], status['result'], status['message']))
									logging.warning('Payload for failed terminal: {}'.format(terminal))
								complete_obj_ids.append(terminal['obj_id'])

				logging.info('{} pending rebuilds'.format(pending_async_tasks))
			write_terminals_to_be_rebuilt_to_file(rebuild_list)
			logging.info('{} terminals remaining'.format(len(rebuild_list)))
			logging.info('Remaining terminals written to disk')
			if rebuild_parameters['continuous'] == False:
				if not shall_we_proceed():
					sys.exit(0)
			else:
				time.sleep(rebuild_parameters['chunk_interval'])
	else:
		logging.info('No changes made...')
		sys.exit(0)





	#active_terminals = []

	# # check if list of active subscribers exists
	# # try to load list
	
	# try:
	# 	active_terminals = read_active_terminals_from_file()
	# 	logging.info('{} active terminals loaded from file!'.format(len(active_terminals)))
	# except:
	# 	sub_scode, subscribers = get_all_oss_subscriber()
	# 	if sub_scode == 200:
	# 		for sub in subscribers:
	# 			if '-01' in sub['subscriber_id'] and sub['subscriber_plan_id'] != 'Enabled':
	# 				# Look up terminal obj_id

	# 				term_scode, terminal_obj = get_oss_terminal(sub['subscriber_id'].strip('-01'))

	# 				if term_scode == 200 and len(terminal_obj) == 1:
	# 					active_terminals.append(terminal_obj[0]['obj_id'])
	# 				else:
	# 					logging.warning('Failed terminal lookup for: {}'.format(sub['subscriber_id']))

	# 		logging.info("Active subscribers: {}".format(len(active_terminals)))
	# 	else:
	# 		logging.warning('Failed to get all subscribers')
	# 	# write active terminals to file
	# 	write_active_terminals_to_file(active_terminals)


	# # Iterate overall active terminals
	# chunk_size = 20
	# terminal_chunks = chunks(active_terminals, chunk_size)
	# chunk_number = 0
	# for chunk in terminal_chunks:
	# 	logging.info(chunk)
	#  	status, job_ids = post_oss_terminal_EDk('edk', 'CONUS_STANDARD', chunk)
	# 	if status == 202:
	# 		logging.info(job_ids)
	# 		# Monitor Template Rebuild Jobs
	# 		rebuild_success = []
	# 		rebuild_failure = []
	# 		if len(job_ids) > 0:
	# 			pool = Pool(processes=len(job_ids))
	# 			logging.info('{} pending async tasks'.format(len(job_ids)))
	# 			for n in pool.map(monitor_async, job_ids):
	# 				if n[0] == True:
	# 					rebuild_success.append(n[1])
	# 					logging.info('Success {}'.format(n))
	# 				else:
	# 					rebuild_failure.append(n[1])
	# 					logging.info('Failure {}'.format(n))

	# 		for term in chunk:
	# 			t_scode, t_status = get_oss_terminals_status(term)

	# 			if t_scode == 200:
	# 				logging.info(t_status['obj_name'])
	# 			else:
	# 				logging.warning(term)

	# 		logging.info('REBUILD COMPLETE: {} Successful and {} failures'.format(len(rebuild_success), len(rebuild_failure)))

	# 		# Attempt Recovery of Failed Rebuilds
	# 		if len(rebuild_failure) > 0:
	# 			logging.info('Failed Rebuilds: {}'.format(rebuild_failure))
			
	# 		#chunk complete
	# 		chunk_number += 1
	# 		write_active_terminals_to_file(active_terminals[chunk_size*chunk_number:])
	# 		logging.info('{} terminals remaining in EDK deploy'.format(len(active_terminals[chunk_size*chunk_number:])))
	# 		logging.info('Remaining active terminals written to disk')
	# 	else:
	# 		logging.warning('Sweeper returned {} {}'.format(status, job_ids))
	# 	# wait for user input
	# 	uinput = raw_input("Press 'c' to continue or 'a' to abort...")
	# 	if uinput == 'c':
	# 		logging.info('Starting next chunk')
	# 	elif uinput == 'a':
	# 		logging.info('ABORT')
	# 		sys.exit(0)
	# 	else:
	# 		logging.info('User input: {}'.format(uinput))
	# 		logging.warning('ABORT')
	# 		sys.exit(0)

	logging.info('END')
