#!/usr/bin/env python
import os
import sys
import json
import struct
import subprocess

try:
	sys.stdin.buffer

	# Python 3.x version
	# Read a message from stdin and decode it.
	def getMessage():
		rawLength = sys.stdin.buffer.read(4)
		if len(rawLength) == 0:
			sys.exit(0)
		messageLength = struct.unpack('@I', rawLength)[0]
		message = sys.stdin.buffer.read(messageLength).decode('utf-8')
		return json.loads(message)

	# Send an encoded message to stdout
	def sendMessage(messageContent):
		encodedContent = json.dumps(messageContent).encode('utf-8')
		encodedLength = struct.pack('@I', len(encodedContent))

		sys.stdout.buffer.write(encodedLength)
		sys.stdout.buffer.write(encodedContent)
		sys.stdout.buffer.flush()

except AttributeError:
	# Python 2.x version (if sys.stdin.buffer is not defined)
	# Read a message from stdin and decode it.
	def getMessage():
		rawLength = sys.stdin.read(4)
		if len(rawLength) == 0:
			sys.exit(0)
		messageLength = struct.unpack('@I', rawLength)[0]
		message = sys.stdin.read(messageLength)
		return json.loads(message)

	# Send an encoded message to stdout
	def sendMessage(messageContent):
		encodedContent = json.dumps(messageContent)
		encodedLength = struct.pack('@I', len(encodedContent))

		sys.stdout.write(encodedLength)
		sys.stdout.write(encodedContent)
		sys.stdout.flush()


def install():
	home_path = os.getenv('HOME')

	manifest = {
		'name': 'open_with',
		'description': 'Example host for native messaging',
		'path': os.path.realpath(__file__),
		'type': 'stdio',
	}
	locations = {
		'chrome': os.path.join(home_path, '.config', 'google-chrome', 'NativeMessagingHosts'),
		'chromium': os.path.join(home_path, '.config', 'chromium', 'NativeMessagingHosts'),
		'firefox': os.path.join(home_path, '.mozilla', 'native-messaging-hosts'),
	}
	filename = 'open_with.json'

	for browser, location in locations.iteritems():
		if os.path.exists(os.path.dirname(location)):
			if not os.path.exists(location):
				os.mkdir(location)

			browser_manifest = manifest.copy()
			if browser == 'firefox':
				browser_manifest['allowed_extensions'] = ['newopenwith@darktrojan.net']
			else:
				browser_manifest['allowed_origins'] = ['chrome-extension://eboojgmpoadapdemnbhjnnlnnnoijefc/']

			with open(os.path.join(location, filename), 'w') as file:
				file.write(
					json.dumps(browser_manifest, indent=2, separators=(',', ': '), sort_keys=True).replace('  ', '\t') + '\n'
				)


def _read_desktop_file(path):
	with open(path, 'r') as desktop_file:
		current_section = None
		name = None
		command = None
		for line in desktop_file:
			if line[0] == '[':
				current_section = line[1:-2]
			if current_section != 'Desktop Entry':
				continue

			if line.startswith('Name='):
				name = line[5:].strip()
			elif line.startswith('Exec='):
				command = line[5:].strip()

		return {
			'name': name,
			'command': command
		}


def find_browsers():
	apps = [
		'Chrome',
		'Chromium',
		'chromium-browser',
		'firefox',
		'Firefox',
		'Google Chrome',
		'google-chrome',
		'opera',
		'Opera',
		'SeaMonkey',
		'seamonkey',
	]
	paths = [
		os.path.join(os.getenv('HOME'), '.local/share/applications'),
		'/usr/local/share/applications',
		'/usr/share/applications'
	]
	suffix = '.desktop'

	results = []
	for p in paths:
		for a in apps:
			fp = os.path.join(p, a) + suffix
			if os.path.exists(fp):
				results.append(_read_desktop_file(fp))
	return results


def listen():
	while True:
		receivedMessage = getMessage()
		if receivedMessage == 'ping':
			sendMessage({
				'version': 7,
				'file': os.path.realpath(__file__)
			})
		elif receivedMessage == 'find':
			sendMessage(find_browsers())
		else:
			devnull = open(os.devnull, 'w')
			subprocess.Popen(receivedMessage, stdout=devnull, stderr=devnull)


if __name__ == '__main__':
	if len(sys.argv) == 2:
		if sys.argv[1] == 'install':
			install()
			sys.exit(0)
		elif sys.argv[1] == 'find_browsers':
			print find_browsers()
			sys.exit(0)

	listen()
