import os
import time
import json
import datetime
import subprocess
from arg_parser import argument_parser
from apscheduler.schedulers.blocking import BlockingScheduler

class monitor():
	"""
	monitor the health of secured directory at regular interval
	At every interval, it reads the details archived files from the archive_details.json
	"""

	def __init__(self, args):
		self.path_secured = args.path_secured
		self.archive_json = args.archive_json
		self.path_log = args.path_log
		self.verbose = args.verbose

	def check_size(self, path):
		"""find the size of directory mentioned by path"""
		size = subprocess.check_output(['du', path]).split()[0].decode('utf-8')
		return size

	def diff_time(self, t1, t2):
		"""
		find the difference between two timestamps in the format: %Y-%m-%d %H:%M:%S
		args: t1, t2: timestamps to find the difference
		return: difference of timestamps
		"""
		return (time.mktime(time.strptime(t1,"%Y-%m-%d %H:%M:%S")) -
				   time.mktime(time.strptime(t2, "%Y-%m-%d %H:%M:%S")))

	def check_executable(self):
		files_exe = []
		files_list = os.listdir(self.path_secured)
		for items in files_list:
			file_path = os.path.join(self.path_secured, items)
			status_exe = os.path.isfile(file_path) and os.access(file_path, os.X_OK)
			if status_exe:
				os.remove(file_path)
				files_list.append(file_path)

		return files_exe

	def monitor_log(self, now, data=None):
		"""
		generate log for monitor operation
		args: data - list of archived details in dictionary
			  now - timestamp for current log interval
		return: None
				writes the json named log_<timestamp>.json for log file
		"""
		monitor_log_json = {}
		monitor_log_json['no_files_secured'] = len(os.listdir(self.path_secured))
		monitor_log_json['secured_size_current'] = self.check_size(self.path_secured)

		# check for executable files
		files_exe = self.check_executable()
		monitor_log_json['num_exe_files'] = len(files_exe)
		monitor_log_json['deleted_exe_files'] = files_exe

		if data is not None:
			total_size = 0
			files = []
			for items in data:
				total_size += items['size_files_archived']
				files.extend([(k, (v, items['timestamp'])) for k, v in items['files'].items()])

			monitor_log_json['size_files_archived'] = total_size
			monitor_log_json['no_files_archived'] = len(files)
			monitor_log_json['archived_files_and_size'] = dict(files)

		else:
			monitor_log_json['no_files_archived'] = 0

		save_name = os.path.join(self.path_log, 'log_' + now + '.json')
		with open(save_name, 'w') as fp:
			json.dump(monitor_log_json, fp)

		if self.verbose == True:
			print("At timestamp {}, details of secured directory:".format(now))
			print("* Total number of files in secured: {}".format(monitor_log_json['no_files_secured']))
			print("* Total size of secured directory: {} MB".format(int(monitor_log_json['secured_size_current'])/1000))
			print("* Number of executable files in secured: {}".format(monitor_log_json['num_exe_files']))
			if monitor_log_json['num_exe_files'] != 0:
				print("* Deleted executable files from secured: ")
				for items in monitor_log_json['deleted_exe_files']:
					print(items)
			if monitor_log_json['no_files_archived'] != 0:
				print("* Number of files archived: {}".format(monitor_log_json['no_files_archived']))
				print("* Size of files archived: {} MB".format(int(monitor_log_json['size_files_archived'])/1000))				
				print("* Archived files and thier size: ")
				for items in monitor_log_json['archived_files_and_size']:
					print(items)

			else:
				print("* Number of files archived: {}".format(monitor_log_json['no_files_archived']))

	def monitor_details(self):
		"""
		perform the functionality of monitor for secured directory
		If there exists any archive file, then process it according to that,
		otherwise add the required details in a json
		"""
		# check if archive file exists
		archive_file = './' + self.archive_json

		# if archive file exista then extract data from it
		if os.path.isfile(archive_file):
			with open(self.archive_json, 'r') as file:
				data=file.read()

			# parse file
			archive_details = json.loads(data)

			archived_files = []

			data = []
			now = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

			# check if the difference between the entry and present is less than 5 mins.(300 sec.)
			for items in archive_details:
				difference = self.diff_time(now, items)
				if int(difference) < 300:
					data.append(archive_details[items])

			self.monitor_log(now, data) # generate monitor log
		else:
			now = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
			self.monitor_log(now) # generate monitor log

		print("=====================================")
		print(2*'\n')

if __name__ == '__main__':
	args = argument_parser()

	monitor_instance = monitor(args)
	monitor_instance.monitor_details()

	scheduler = BlockingScheduler()
	scheduler.add_job(monitor_instance.monitor_details, 'interval', seconds=30)
	scheduler.start()
