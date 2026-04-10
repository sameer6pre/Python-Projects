#!/usr/bin/env python

import os
import json

'''
This script requires following environment variables:

- REPO_NAME:
  > example: 'iamwatchdogs/test'
  > GitHub action variable: ${{ github.repository }}
'''


def find_table_points(lines):
	"""
	Find table points within a given list of lines.

	The table points are determined by the presence of the markers:
		<!-- TABLE BEGINS -->
		<!-- TABLE ENDS -->

	Args:
		lines (list): List of lines to search in.

	Returns:
		tuple: A tuple of two integers containing the start and end indices of
			the table points.

	Raises:
		SystemExit: If the table markers are not found or if the table end
			marker appears before the table start marker.
	"""

	# Setting default return values
	table_start = None
	table_end = None

	# Setting the markers
	table_start_marker = '<!-- TABLE BEGINS -->'
	table_end_marker = '<!-- TABLE ENDS -->'

	# Iterating over lines to find the markers
	for index, line in enumerate(lines):
		if table_start is None and table_start_marker in line:
			table_start = index
		elif table_end is None and table_end_marker in line:
			table_end = index
		if table_start is not None and table_end is not None:
			break

	# Checking for possible errors
	if table_start is None or table_end is None:
		print('Table not found in the file.')
		exit(1)
	elif table_start >= table_end:
		print('Invaild use of table markers.')
		exit(2)

	return (table_start, table_end)


def main():
	import re
	import html
	import urllib.parse
	import sys

	"""
	Update the index.md file with the latest contributors data.

	This function retrieves the REPO_NAME environment variable and the
	CONTRIBUTORS_LOG file path. It then reads the log file and extracts the
	data from it. The function then reads the index.md file and calculates
	the table points. If the table does not exist, it creates the table
	header. The function then iterates over the log data and updates the
	table with the latest data. Finally, it updates the index.md file with
	the updated data and prints a success message.

	"""

	# Retrieving Environmental variables
	REPO_NAME = os.environ.get('REPO_NAME')

	# Setting path for the log JSON file
	TARGET_FILE = 'index.md'
	CONTRIBUTORS_LOG = '.github/data/contributors-log.json'

	# Load JSON safely with error handling
	try:
		with open(CONTRIBUTORS_LOG, 'r') as json_file:
			data = json.load(json_file)
	except FileNotFoundError:
		print(f"Contributors log not found: {CONTRIBUTORS_LOG}")
		sys.exit(1)
	except ValueError:
		print(f"Invalid JSON in {CONTRIBUTORS_LOG}")
		sys.exit(1)

	# Reading lines from the file
	try:
		with open(TARGET_FILE, 'r') as file:
			lines = file.readlines()
	except FileNotFoundError:
		print(f"Target file not found: {TARGET_FILE}")
		sys.exit(1)

	# Calculating Stating and ending points of the targeted table
	table_start, table_end = find_table_points(lines)

	# Creating HTML table header to replace md table
	table_header = list()
	table_header.append('&lt;table>\n')
	table_header.append('\t&lt;tr align="center">\n')
	table_header.append('\t\t&lt;th>Project Title&lt;/th>\n')
	table_header.append('\t\t&lt;th>Contributor Names&lt;/th>\n')
	table_header.append('\t\t&lt;th>Pull Requests&lt;/th>\n')
	table_header.append('\t\t&lt;th>Demo&lt;/th>\n')
	table_header.append('\t&lt;/tr>\n')

	# Initializing empty list for lines
	updated_lines = list()

	# Regular expressions / helpers
	username_re = re.compile(r'^[A-Za-z0-9-]+$')

	# Iterating over log to update target file
	for title, details in data.items():

		# Processing contributors-names
		contributors_names = details.get('contributor-name', [])
		contributors_names_list = []
		for name in contributors_names:
			name_str = str(name)
			display = html.escape(name_str)
			# PRECOGS_FIX: Build a safe href and HTML-escape attribute and content to prevent attribute/context breakout
			if username_re.match(name_str):
				href = f"https://github.com/{urllib.parse.quote(name_str)}"
			else:
				# encode anything unsafe; do not allow raw user content to inject attributes
				href = f"https://github.com/{urllib.parse.quote(name_str)}"
			contributors_names_list.append(f'&lt;a href="{html.escape(href, quote=True)}" title="goto {display} profile">{display}&lt;/a>')
		contributors_names_output = ', '.join(contributors_names_list)

		# Processing pull-requests
		pull_requests = details.get('pull-request-number', [])
		pull_requests_list = []
		for pr in pull_requests:
			pr_str = str(pr)
			# PRECOGS_FIX: Only allow numeric PR identifiers to form links; sanitize otherwise
			if pr_str.isdigit():
				if REPO_NAME:
					href = f"https://github.com/{urllib.parse.quote(REPO_NAME)}/pull/{pr_str}"
				else:
					href = f"/pull/{pr_str}"
			else:
				href = '#'
			pull_requests_list.append(f'&lt;a href="{html.escape(href, quote=True)}" title="visit pr #{html.escape(pr_str)}">{html.escape(pr_str)}&lt;/a>')
		pull_requests_output = ', '.join(pull_requests_list)

		# Processing demo-path
		demo_path = str(details.get('demo-path', ''))
		# Normalize spaces
		demo_path = demo_path.replace(' ', '%20')
		parsed = urllib.parse.urlparse(demo_path)
		# Allow only http(s) or relative paths (no javascript:, data:, vbscript:, etc.)
		if parsed.scheme in ('', 'http', 'https'):
			href = demo_path
		else:
			href = '#'

		# Build display label (escaped)
		display_title = html.escape(str(title))
		display_repo = html.escape(str(REPO_NAME)) if REPO_NAME else ''
		if title == 'root' or title == '{init}':
			label = f'/{display_repo}/'
		elif title == '{workflows}':
			label = f'/{display_repo}/.github/workflows'
		elif title == '{scripts}':
			label = f'/{display_repo}/.github/scripts'
		elif title == '{others}':
			label = f'/{display_repo}/.github'
		else:
			label = f'/{display_repo}/{display_title}/'

		demo_path_output = f'&lt;a href="{html.escape(href, quote=True)}" title="view the result of {display_title}">{label}&lt;/a>'

		# Appending all data together (escape title displayed in cell)
		updated_lines.append('\t&lt;tr align="center">\n')
		updated_lines.append(f'\t\t&lt;td>{html.escape(str(title))}&lt;/td>\n')
		updated_lines.append(f'\t\t&lt;td>{contributors_names_output}&lt;/td>\n')
		updated_lines.append(f'\t\t&lt;td>{pull_requests_output}&lt;/td>\n')
		updated_lines.append(f'\t\t&lt;td>{demo_path_output}&lt;/td>\n')
		updated_lines.append(f'\t&lt;/tr>\n')

	# Table footer
	table_footer = ['&lt;/table>\n']

	# Updating the lines with updated data
	lines[table_start+1:table_end] = table_header + updated_lines + table_footer

	# Updating the target file
	with open(TARGET_FILE, 'w') as file:
		file.writelines(lines)

	# Printing Success Message
	print(f"Updated '{TARGET_FILE}' Successfully")