#!/bin/pyhon
# -*- coding: utf-8 -*-
import os
from imapclient import IMAPClient, DELETED
from optparse import OptionParser
from ConfigParser import RawConfigParser

# ----PROGRAM START----
# --functions--
def parse_bodystructure(data):
	"""Parses multipart only"""
	for part, basic_body in enumerate(data[0], start=1):
		if basic_body[0] == 'text':
			if basic_body[1] == 'xml':
				# basic_body[9] if text, [8] if application
				yield {'encoding': basic_body[5], 'filename': basic_body[9][1][1], 'part': part}
			elif basic_body[1] == 'xls':
				if basic_body[9][1][1][-4:].lower() == '.xml':
					yield {'encoding': basic_body[5], 'filename': basic_body[9][1][1], 'part': part}
		elif basic_body[0] == 'application':
			# content-disposition is basic_body[9] if text, basic_body[8] if application
			# found one provider who sents xml as application/xls
			if basic_body[1] == 'xml' or basic_body[1] == 'xls' or basic_body[1] == 'octet-stream':
				if basic_body[8]:
					if basic_body[8][0] == 'attachment':
						if basic_body[8][1][1][-4:].lower() == '.xml' or basic_body[8][1][1][-4:].lower() == '.zip':
							yield {'encoding': basic_body[5], 'filename': basic_body[8][1][1], 'part': part}
				elif basic_body[2]:
					if basic_body[2][0] == 'name' \
					and (basic_body[2][1][-4:].lower() == '.xml' or basic_body[2][1][-4:].lower() == '.zip'):
						yield {'encoding': basic_body[5], 'filename': basic_body[2][1], 'part': part}
			elif basic_body[1] == 'zip' \
			or basic_body[1] == 'x-zip' \
			or basic_body[1] == 'x-zip-compressed' \
			or basic_body[1] == 'x-compress' \
			or basic_body[1] == 'x-compressed':
				if basic_body[8]:
					if basic_body[8][0] == 'attachment':
						if basic_body[8][1][1][-4:].lower() == '.zip':
							yield {'encoding': basic_body[5], 'filename': basic_body[8][1][1], 'part': part}
				elif basic_body[2]:
					if basic_body[2][0] == 'name' and basic_body[2][1][-4:].lower() == '.zip':
						yield {'encoding': basic_body[5], 'filename': basic_body[2][1], 'part': part}
		elif basic_body[0] == 'multipart' and basic_body[1] == 'x-zip':
			if basic_body[8][0] == 'attachment':
				if basic_body[8][1][1][-4:].lower() == '.zip':
					yield {'encoding': basic_body[5], 'filename': basic_body[8][1][1], 'part': part}

def generate_filename(filename):
	f = filename
	ext_pos = filename.rfind('.')
	c = 0
	while os.path.exists(f):
		f = filename[:ext_pos] + '_' + str(c) + filename[ext_pos:]
		c += 1
	return f

# --script--
def main():
	# -options-
	parser = OptionParser("python chkemail.py [options] CONFIG_FILE")
	parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False)
	(options, args) = parser.parse_args()

	# -settings-
	if len(args) < 1:
		parser.print_help()
		exit()

	if not os.path.exists(args[0]):
		raise IOError(2, 'Archivo de configuracion no encontrado')

	config = RawConfigParser()
	config.read(args[0])
	# settings = config.read(args[0])
	for name, value in config.items('chkemail'):
		globals()[name.upper()] = value

	# -workflow-
	# change directory
	os.chdir(OUTPUT_DIR)
	# create, connect, and login to server
	server = IMAPClient(HOST, use_uid=True)
	try:
		server.login(USER, PASSWORD, port=PORT)
	except NameError:
		server.login(USER, PASSWORD)

	inbox = server.select_folder('INBOX')
	if options.verbose:
		print '%d messages in INBOX' % inbox['EXISTS']

	messages = server.search(['NOT DELETED', 'HEADER Content-Type mixed'])
	if options.verbose:
		print "%d messages with possible attch" % len(messages)

	# fetch data from messages, then parse it and select only messages with text/xml parts
	scan = server.fetch(messages, ['BODYSTRUCTURE'])
	msgs_info = []
	for msgid, data in scan.iteritems():
		# print 'ID ', msgid
		# print data['BODYSTRUCTURE']
		if data['BODYSTRUCTURE'].is_multipart:
			for bodbystructure in parse_bodystructure(data['BODYSTRUCTURE']):
				msgs_info += [(msgid, bodbystructure)]

	# group all messages that have the attachment in the same section/part
	# also create a dictionary of attachments and the section/part they're from
	# e.g.
	# {uid: {part2: {'filename': '...', 'encoding': '...'}, part4: {'...': '...', ...}}, uid3: {part2: {...}}}
	grouped_msgs = {} # will be used to fetch all messages with the same part
	msgs_dict = {} # will be used to store fetched message content
	for msg in msgs_info:
		msgid, info = msg
		part = info['part']
		# create group of messages whose same part we need
		try:
			grouped_msgs[part] += [msgid]
		except KeyError:
			grouped_msgs[part] = [msgid]

		# create dictionary for attachment data
		del info['part']
		if msgid not in msgs_dict:
			msgs_dict[msgid] = {part: info}
		else:
			msgs_dict[msgid][part] = info

	if options.verbose:
		print '%d messages to examine (i.e. have a XML attachment)' % len(msgs_dict)

	# fetch all msgs's xml part
	for part, msgs in grouped_msgs.iteritems():
		request = 'BODY['+str(part)+']'
		response = server.fetch(msgs, [request])
		for mid in msgs:
			msgs_dict[mid][part]['data'] = response[mid][request]


	# move messages to trash
	if len(msgs_dict.keys()) > 0:
		server.copy(msgs_dict.keys(), 'INBOX.Trash')
		server.delete_messages(msgs_dict.keys())
	server.logout()

	# decode and write data to file
	num_attch = 0
	for m, part in msgs_dict.iteritems():
		for data in part.itervalues():
			if data['filename'][-4:].lower() == '.xml':
				attach_filename = generate_filename(data['filename'])
				xml_file = open(attach_filename, 'wb')
				if data['encoding'] == 'base64':
					from base64 import b64decode
					xml_file.write(b64decode(data['data']))
				elif data['encoding'] == 'quoted-printable':
					from quopri import decodestring
					xml_file.write(decodestring(data['data']))
				xml_file.close()
				num_attch += 1
			elif data['filename'][-4:].lower() == '.zip':
				from base64 import b64decode
				from zipfile import ZipFile, ZipInfo
				import tempfile
				tmp_zip = tempfile.TemporaryFile()
				tmp_zip.write(b64decode(data['data']))
				zipped = ZipFile(tmp_zip)
				for f_info in zipped.infolist():
					if f_info.filename[-4:].lower() == '.xml':
						xml_filename =  generate_filename(os.path.basename(f_info.filename))
						xml_file = open(xml_filename, 'wb')
						xml_file.write(zipped.read(f_info))
						xml_file.close()
						num_attch += 1						
				tmp_zip.close()

	
	if options.verbose:
		print '%d parts dlded' % num_attch

if __name__ == "__main__":
	main()