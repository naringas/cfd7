#!/bin/pyhon
# -*- coding: utf-8 -*-
import os
import tempfile

from base64 import b64decode
from ConfigParser import RawConfigParser
from email.header import decode_header
from errno import ENOENT
from optparse import OptionParser
from quopri import decodestring
from time import strftime
from zipfile import ZipFile, ZipInfo

from imapclient import IMAPClient, DELETED

# ----CLASS DEFINITIONS----
class Mess(object):
	"""Mess(message_id, envelope, multipart_bodystructure)
	"""

	class Parts(object):
		class Info(object):
			def __init__(self, content_type, content_subtype, parameters, encoding, disposition):
				self.content_type = content_type.lower()
				self.content_subtype = content_subtype.lower()
				self.parameters = parameters
				self.encoding = encoding.lower()
				self._disposition = disposition
				self.data = None
				self._filename = None

			@property
			def disposition(self):
				if self._disposition:
					return self._disposition[0]
				else:
					return None
			@property
			def filename(self):
				if self._filename is not None:
					return self._filename
				# Try to return content disposition parameter: filename
				disp_parm = self._disposition[1] if self.disposition else ()
				if len(disp_parm)%2 != 0: raise ValueError('Malformed Content-Disposition')
				for name, value in [disp_parm[i:i+2] for i in xrange(0, len(disp_parm), 2)]:
					if name.lower() == 'filename':
						self._filename = decode_header(value)[0][0]
						return self._filename
				# if that didn't work, try the body parameter: name
				body_parm = self.parameters if self.parameters else ()
				if len(body_parm)%2 != 0: raise ValueError('Malformed body parameters')
				for name, value in [body_parm[i:i+2] for i in xrange(0, len(body_parm), 2)]:
					if name.lower() == 'name':
						self._filename = decode_header(value)[0][0]
						return self._filename
				# if all fails return ''
				self._filename = ''
				return self._filename

			def __str__(self):
				return (
					"Content-Type: {o.content_type}/{o.content_subtype}\n"
					"Parameter:    {o.parameters}\n"
					"Encoding:     {o.encoding}\n"
					"Disposition:  {o.disposition}\n"
					"Filename:     {o.filename}\n"
					).format(o=self)

		def __init__(self, bodystructure):
			self._parts_dict = dict()
			# parse IMAPClient returned bodystructure
			for part_num, part in enumerate(bodystructure[0], start=1):
				if isinstance(part[0], basestring):
					if part[0].lower() == 'message' and part[1].lower() == 'rfc822':
						# part[8] is the bodypart part (after the envelope) of a rfc822 part of a message
						for subpart_num, subpart in enumerate(part[8], start=1):
							if subpart and not isinstance(subpart, str):
								full_part = str(part_num) + '.' + str(subpart_num)
								self._imbue_part_info(full_part, subpart)
							elif isinstance(subpart, str):
								# As soon as subpart is a string, there won't be anymore message subparts
								break
					else:
						self._imbue_part_info(str(part_num), part)
			# make an ordered list of parts, to do so:
			# convert to float then sort then convert back to string while removing the .0 (inserted by float)
			all_parts = [float(x) for x in self._parts_dict.keys()]
			all_parts.sort()
			self.sorted_parts = [str(x) if str(x)[-1]!='0' else str(x)[0] for x in all_parts]

		def _imbue_part_info(self, part_num, part_info):
			"""part_num has to be a string."""
			if isinstance(part_info[0], basestring):
				try:
					disposition = part_info[9] if part_info[0].lower() == 'text' else part_info[8]
				except IndexError:
					disposition = None
				self._parts_dict[part_num] = Mess.Parts.Info(part_info[0], part_info[1], part_info[2], part_info[5], disposition)


		def __str__(self):
			string = ''
			for part_num in self.sorted_parts:
				string += ("{0}"
					"\tContent-Type: {o.content_type}/{o.content_subtype}\n"
					"\tParameter:    {o.parameters}\n"
					"\tEncoding:     {o.encoding}\n"
					"\tDisposition:  {o.disposition}\n"
					"\tFilename:     {o.filename}\n"
					"\n").format(part_num, o=self._parts_dict[part_num])
			return string

		def __getitem__(self, key):
			if isinstance(key, int):
				return self._parts_dict[self.sorted_parts[key]]
			else:
				return self._parts_dict[str(key)]

		# def __iter__(self): return iter(self._parts_dict)
		def iteritems(self): return self._parts_dict.iteritems()

	class EnvInfo(object):
		def __init__(self, envelope):
			self.mailbox = envelope[2][0][2]
			self.domain = envelope[2][0][3]

		def __str__(self): return self.mailbox + '-en-' + self.domain

	def __init__(self, mid, envelope, bodystructure):
		self.id = mid
		self.envelope = Mess.EnvInfo(envelope)
		self.parts = Mess.Parts(bodystructure)

	def __str__(self):
		return "#{0} -- from:{1}\n{2}".format(str(self.id), str(self.envelope), str(self.parts))

# ----PROGRAM START----
# --functions--
def generate_filename(filename):
	f = filename
	ext_pos = filename.rfind('.')
	c = 0
	while os.path.exists(f):
		f = filename[:ext_pos] + '_' + str(c) + filename[ext_pos:]
		c += 1
	return f

def ensure_dir(dir_):
	if not os.path.isdir(dir_):
		os.makedirs(dir_)

# --script--
def main():
	# -options-
	parser = OptionParser("python %prog [options] CONFIG_FILE")
	parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False)
	(options, args) = parser.parse_args()

	# -settings-
	if len(args) < 1:
		parser.print_help()
		exit()

	if not os.path.exists(args[0]):
		raise IOError(ENOENT, 'Archivo de configuracion no encontrado', args[0])

	config = RawConfigParser()
	config.read(args[0])
	# put read config options (from the .ini) into global namespace and in uppercase
	for name, value in config.items('chkemail'):
		globals()[name.upper()] = value

	# -workflow-
	# create, connect, and login to server
	server = IMAPClient(HOST, use_uid=True)
	try:
		server.login(USER, PASSWORD, port=PORT)
	except NameError: # if PORT is not defined
		server.login(USER, PASSWORD)

	inbox = server.select_folder('INBOX')
	if options.verbose:
		print '%d messages in INBOX (included deleted)' % inbox['EXISTS']

	messages = server.search(['NOT DELETED', 'HEADER Content-Type mixed'])
	if options.verbose:
		print "%d messages with possible attch" % len(messages)

	# fetch data from messages, put each message (Mess object) into the msgs list
	scan = server.fetch(messages, ['BODYSTRUCTURE', 'ENVELOPE'])
	msgs = dict()
	for mid, response in scan.iteritems():
		# Mess class only works with mulipart messages
		if response['BODYSTRUCTURE'].is_multipart:
			msgs[mid] =  Mess(mid, response['ENVELOPE'], response['BODYSTRUCTURE'])

	# Select the messages with attachements I want, put them in group_msgs
	group_msgs = dict()
	for msg in msgs.itervalues():
		group_msgs[msg.id] = list()
		for part_num, part_info in msg.parts.iteritems():
			if part_info.filename:
				filename = part_info.filename.lower()
				if filename.endswith('.pdf') or filename.endswith('.xml') or \
					filename.endswith('.zip'):
					group_msgs[msg.id] += [part_num]
		if not group_msgs[msg.id]:
			del group_msgs[msg.id]

	# fetch all interesting parts
	for msg_id, parts in group_msgs.iteritems():
		request = ['BODY['+str(part)+']' for part in parts]
		response = server.fetch(msg_id, request)
		for body_part in response[msg_id].iterkeys():
			if 'BODY' in body_part:
				msgs[msg_id].parts[body_part[5:-1]].data = response[msg_id][body_part]

	# move messages to trash
	if len(group_msgs.keys()) > 0:
		server.copy(group_msgs.keys(), 'INBOX.Trash')
		server.delete_messages(group_msgs.keys())
	server.logout()

	# ensure there's an OUTPUT_DIR directory
	pdf_dir = os.path.join(OUTPUT_PDF, strftime('%Y-%m'))
	ensure_dir(pdf_dir)
	ensure_dir(OUTPUT_DIR)

	# decode and write data to file
	num_attch = 0
	for msg in msgs.itervalues():
		for part in msg.parts:
			if part.data:
				filename = part.filename.lower()
				if filename.endswith('.pdf') or filename.endswith('.xml'):
					if filename.endswith('.pdf'):
						ensure_dir(os.path.join(pdf_dir, str(msg.envelope)))
						attachment_filename = generate_filename(os.path.join(pdf_dir, str(msg.envelope), os.path.basename(part.filename)))
					else:
						attachment_filename = generate_filename(os.path.join(OUTPUT_DIR, os.path.basename(part.filename)))
					with open(attachment_filename, 'wb') as file_:
						if part.encoding == 'quoted-printable':
							file_.write(decodestring(part.data))
						elif part.encoding == 'base64':
							file_.write(b64decode(part.data))
					num_attch += 1
				elif filename.endswith('.zip') and part.encoding == 'base64':
					with tempfile.TemporaryFile() as tmp_zip:
						tmp_zip.write(b64decode(part.data))
						zip_file = ZipFile(tmp_zip)
						for f_info in zip_file.infolist():
							if f_info.filename.lower().endswith('.xml'):
								attachment_filename = generate_filename(os.path.join(OUTPUT_DIR, os.path.basename(f_info.filename)))
							elif f_info.filename.lower().endswith('.pdf'):
								ensure_dir(os.path.join(pdf_dir, str(msg.envelope)))
								attachment_filename = generate_filename(os.path.join(pdf_dir, str(msg.envelope), os.path.basename(f_info.filename)))
							else:
								continue
							with open(attachment_filename, 'wb') as file_:
								file_.write(zip_file.read(f_info))
							num_attch += 1

	if options.verbose:
		print '%d files extracted' % num_attch

if __name__ == "__main__":
	main()
