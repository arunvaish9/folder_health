import argparse

def argument_parser():
	# Instantiate the parser
	parser = argparse.ArgumentParser(description='Input path for temp and secured directory')

	parser.add_argument('--path_temp', type=str, default='./temp',
	                    help='Path for temp directory')

	parser.add_argument('--path_secured', type=str, default='./secured',
	                    help='Path for secured directory')

	parser.add_argument('--path_archive', type=str, default='./archive',
	                    help='Path for archive directory')

	parser.add_argument('--path_log', type=str, default='./log',
	                    help='Path for log directory')

	parser.add_argument('--path_test', type=str, default='./test_data',
	                    help='Path for test data directory')

	parser.add_argument('--size_limit_secured', type=str, default=100,
	                    help='Maximum allowed size for the secured directory in MB')

	parser.add_argument('--verbose', type=bool, default=True,
	                    help='whether print the INFO')

	parser.add_argument('--archive_json', type=str, default='archive_details.json',
	                    help='name for the json file to save archive details')

	args = parser.parse_args()

	return args