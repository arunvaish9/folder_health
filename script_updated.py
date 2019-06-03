#!/usr/bin/python3
import os
import time
import json
import glob
import shutil
import random
import tarfile
import datetime
import subprocess
from arg_parser import argument_parser
from apscheduler.schedulers.blocking import BlockingScheduler


class archive():
	"""
	Class to perform archive operation.
	"""
	def __init__(self, args, size_temp):
		self.path_secured = args.path_secured
		self.path_archive = args.path_archive
		self.path_log = args.path_log
		self.size_limit_sec = args.size_limit_secured * 1000
		self.size_temp = size_temp
		self.archive_json = args.archive_json

	def make_json(self, to_be_archived, timestamp, list_size):
		"""
		make json file to store the details of files to be archived.
		Args:	to_be_archived - list of files to be archived
				timestamp: timestamp of archive operation
				list_size: sizr of files to be archived
		Return: None
				writes the json file
		"""
		archive_details = {}

		archive_details_sub = {}
		archive_details_sub['timestamp'] = timestamp
		archive_details_sub['no_files_archived'] = len(to_be_archived)
		archive_details_sub['size_files_archived'] = list_size
		archive_details_sub['files'] = to_be_archived

		archive_details[timestamp] = archive_details_sub

		filename = self.archive_json 
		with open(filename, 'w') as fp:
			json.dump(archive_details, fp)


	def get_sorted_files(self):
		"""
		create the list of files in sorted directory, 
		according to the date of creation
		Args:
		Return: sorted list of files 
		"""
		file_list_sorted = [file for file in os.listdir(self.path_secured)
			 if os.path.isfile(os.path.join(self.path_secured, file))]
		file_list_sorted.sort(key=lambda file: os.path.getmtime(os.path.join(self.path_secured, file)))
		return file_list_sorted

	def make_tarfile(self, to_be_archived, list_size):
		"""
		make tar archive of the list of files
		args: to_be_archived - list of files to be archived
			  list_size - size of files to be archived
		return: timestamp of the archive
		"""
		timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		output_filename =  timestamp + '.tar.gz'
		save_filename = os.path.join(self.path_archive, output_filename)
		with tarfile.open(save_filename, "w:gz") as tar:
			for items in to_be_archived:
				tar.add(items)
				os.remove(items)
		self.make_json(to_be_archived, timestamp, list_size)

		return timestamp		

	def make_archive(self):
		"""
		Function to archive the files
		args:
		return: timestamp of the archive 
		"""
		to_be_archived = [] # list to append the files to be archived
		list_size = 0       # initialize the size of list 
		files_list = self.get_sorted_files()
		for items in files_list:
			file_size = int(subprocess.check_output(['du', os.path.join(self.path_secured, items)]).split()[0].decode('utf-8'))
			list_size += file_size
			to_be_archived.append((os.path.join(self.path_secured, items), file_size))
			if list_size >= int(self.size_temp):
				break

		archive_timestamp = self.make_tarfile(dict(to_be_archived), list_size)
		return archive_timestamp

class main():
	"""
	main class to perform the functionality.
	Initialize the instance with command line arguments.
	"""
	def __init__(self, args):
		self.path_temp = args.path_temp
		self.path_secured = args.path_secured
		self.path_archive = args.path_archive
		self.size_limit_sec = args.size_limit_secured * 1000
		self.size_temp = 0
		self.size_secured = 0
		self.verbose = args.verbose
		self.archive_json = args.archive_json

	def check_size(self, path):
		"""find the size of directory mentioned by path"""
		size = subprocess.check_output(['du', path]).split()[0].decode('utf-8')
		return size

	def secured_oversize(self):
		"""
		Check if at any moment secured directory is oversized,
		i.e. >100 MB
		Args:
		Return: Bool type status
		"""
		self.size_secured = self.check_size(self.path_secured)
		return True if int(self.size_secured) + int(self.size_temp) > self.size_limit_sec else False

	def move_files(self):
		"""
		move files from temp to secured directory 
		"""
		for filename in glob.glob(os.path.join(self.path_temp, '*.*')):
		    shutil.move(filename, self.path_secured)
		    print("file written: ", filename)

	def read_from_temp(self):
		"""
		read the data from temp directory and write to secured directory
		"""
		self.size_temp = self.check_size(self.path_temp) # check size of temp directory

		if self.size_temp == 0:
			test_instance = test()
			test_instance.dump_data_to_temp()

		if self.verbose == True:
			print("At timestamp: {}".format(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')))
			print("Current size of data in temp directory is {} MB".format(int(self.size_temp)/1000))
			print("Checking the size of secured...")

		# Check for the status of secured directory
		if self.secured_oversize():
			if self.verbose == True: 
				print("Size of secured directory is not enough to accomodate the data from temp direcory !")
				print("Archiving the files...")
			archive_instance = archive(args, self.size_temp)
			archive_timestamp = archive_instance.make_archive()

			if self.verbose == True:
				print("Archive file saved as {}/{}.tar.gz, details saved in ./{}".format(self.path_archive, archive_timestamp, self.archive_json) ) 
				print("Writing the files from temp to secured...")

			# after archiving is complete, move files from temo to secured 
			self.move_files()

			if self.verbose == True: 
				print("Finished writing the data")

		else:
			if self.verbose == True: 
				print("Size of secured directory is ENOUGH to accomodate the data from temp direcory !")
				print("Writing the files from temp to secured...")
			
			# move files from temo to secured
			self.move_files()
			
			if self.verbose == True: 
				print("Finished writing the data")

		if self.verbose == True: 
			print("Dumping random data to temp... ")

		# copy data to temo for testing at further steps
		test_instance = test(args)
		test_instance.dump_data_to_temp()

		if self.verbose == True: 
			print("Dumping complete. ")

		print("=====================================")
		print(2*'\n')


class test():
	"""
	dump random data to temp for testing purpose
	"""
	def __init__(self, args):
		self.path_temp = args.path_temp
		self.path_test = args.path_test

	def move_files(self, list_files):
		"""
		move files from test_dir to temp
		Args:
		"""
		for items in list_files:
		    shutil.move(items, self.path_temp)

	def dump_data_to_temp(self):
		"""
		dump data of random size from 10 to 100MB to temp
		"""
		size = random.randint(10,101)

		to_be_copied = [] # list to append the files to be copied
		list_size = 0       # initialize the size of list 
		files_list = os.listdir(self.path_test)
		for file in files_list:
			file_size = int(subprocess.check_output(['du', os.path.join(self.path_test, file)]).split()[0].decode('utf-8'))
			list_size += file_size
			if list_size <= size:
				to_be_copied.append(os.path.join(self.path_test, file))
			else:
				list_size -= file_size

		self.move_files(to_be_copied)





if __name__ == '__main__':
	args = argument_parser()

	main_instance = main(args)
	main_instance.read_from_temp()

	scheduler = BlockingScheduler()
	scheduler.add_job(main_instance.read_from_temp, 'interval', seconds=15)
	scheduler.start()







