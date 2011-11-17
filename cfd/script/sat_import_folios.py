#!/bin/pyhon
# -*- coding: utf-8 -*-
import os, sys, progressbar, MySQLdb
from optparse import OptionParser
from ftplib import FTP, error_reply
from datetime import datetime
from difflib import unified_diff
#
## CONFIGURACION
#
sql_host = 'localhost'
sql_port = 3306
# user must have FILE privilege
sql_user = 'drupal'
sql_passwd = 'cdrupal'
# This database must have the tables already set up
sql_database = 'd7'

# servidor y ruta del los archivos del SAT: ftp://ftp2.sat.gob.mx/agti_servicio_ftp/verifica_comprobante_ftp/
sat_server = 'ftp2.sat.gob.mx'
sat_dir = 'agti_servicio_ftp/verifica_comprobante_ftp/'

filename = 'FoliosCFD.txt'
sql_table = 'cfd_folios'
# local dierectory, full path
local_dir = os.path.join(os.getcwd(), 'sat_files') # = current directory/sat_files

#
## PROGRAM
#
"""writes block to file while updating the progressbar by reading the filesize every write"""
def progress_write(block):
	global write_file, dl_bar, dlded_size
	write_file.write(block)
	dlded_size += len(block)
	dl_bar.update(dlded_size)

"""reads filename and returns repr of its newlines"""
def get_newlines(filename):
	fd = open(filename, 'rU')
	fd.read(128)  # read a 128 bytes i.e. at least a couple of lines
	fd.close()
	return repr(fd.newlines)

"""return a dict with mtime and size for file f in FTP server ftp"""
def get_stats(f, ftp):
	resp = ftp.sendcmd('MDTM %s' %f) # Ask for file's modification time
	# parse response into a datetime if response code is 213 - OK file status.
	if resp[:3] == '213':
		# substract 6 from hour becuase tzinfo is too complicated and would require pytz
		fmtime = datetime(int(resp[4:8]), int(resp[8:10]), int(resp[10:12]), int(resp[12:14])-6, int(resp[14:16]), int(resp[16:18]))
		return {'mtime': fmtime, 'size': ftp.size(f)}
	else:
		raise error_reply('Error FTP: Respuesta insperada')

def main():
	global write_file, dl_bar, dlded_size

	# OPTIONS
	global options
	parser = OptionParser("python script.py [options]")
	parser.add_option('--init', action='store_true', dest='init', default=False,
		help='Vacia las tablas e importa.')
	parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False)
	(options, args) = parser.parse_args()

	# PROGRAM
	# change directory. make it if it doesn't exist
	if not os.access(local_dir, os.F_OK):
		os.mkdir(local_dir)

	os.chdir(local_dir)

	try:
		filestats = {
			'mtime': datetime.fromtimestamp(os.path.getmtime(filename)),
			'size': os.path.getsize(filename)
		}
	except OSError as err:
		if err[0] == 2: # file not found
			filestats = {'mtime': datetime.fromtimestamp(0), 'size': 0}
			options.init = True

	# -----FTP-----
	sat_ftp = FTP(sat_server)
	sat_ftp.login()
	sat_ftp.cwd(sat_dir) # "cd sat_dir"
	remote_filestats = get_stats(filename, sat_ftp)

	must_dl = False
	# must download if remote file is newer or bigger
	if remote_filestats['mtime'] > filestats['mtime'] or remote_filestats['size'] > filestats['size']:
		must_dl = True

	if must_dl:
		if options.init:
			resume_from = None
			dl_size = remote_filestats['size']
			dl_filename = filename
		else:
			resume_from = filestats['size']
			dl_size = remote_filestats['size'] - resume_from
			dl_filename = filename[:-4] + '_diff' + filename[-4:] # foliosCFD_diff.txt

		write_file = open(dl_filename, 'wb') # global
		if options.verbose:
			widgets = [progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA(), ' ', progressbar.FileTransferSpeed()]
			print 'Descargando: ', filename , '\n\ta:', dl_filename
			# globals shared with progress_write : dl_bar, write_file, dlded_size
			dl_bar = progressbar.ProgressBar(maxval=dl_size, widgets=widgets) 
			# write_filename = files[f]['local']['dlded']
			dlded_size = 0
			dl_bar.start()
			write_func = progress_write
		else: 
			# efectively call: sat_ftp.retrbinary('RETR %s' %filanme, open(filename, 'wb').write)
			write_func = write_file.write

		# Do the downloading
		sat_ftp.retrbinary('RETR %s' %filename, write_func, rest=resume_from)
		write_file.close()

	sat_ftp.close()

	# -----pre-SQL-----
	# make SQL statement
	try:
		import_filename = dl_filename
	except NameError:
		import_filename = filename

	# if filename != dl_filename: # if must_dl and not options.init:
	if must_dl and not options.init:
		ignore_lines = 0
	else:
		ignore_lines = 1

	newlines = get_newlines(import_filename)
	import_filename = os.path.abspath(import_filename).replace('\\', r'\\')
	import_sql = "LOAD DATA INFILE '%s' INTO TABLE %s FIELDS TERMINATED BY '|'LINES TERMINATED BY %s IGNORE %i LINES;" \
		% (import_filename, sql_table, newlines, ignore_lines)

	# -----SQL-----
	db_connection = MySQLdb.connect(host=sql_host, port=sql_port, user=sql_user, passwd=sql_passwd, db=sql_database)
	cursor = db_connection.cursor()
	if options.init:
		if options.verbose:
			print 'Vaciando tabla: ', sql_table

		cursor.execute('TRUNCATE TABLE ' + sql_table + ';')
		db_connection.commit()
			
	# if nothing was downladed and --init wasn't passed then do nothing
	if must_dl or options.init: # if not (not must_dl and not options.init)
		if options.verbose:
			print datetime.now(), 'Importando: ', dl_filename, ' a tabla: ', sql_table
			print cursor.execute(import_sql), ' registros agregados'
		else:
			cursor.execute(import_sql)
			
		db_connection.commit()
		if options.verbose:
			print datetime.now(), 'Finalizado'

	cursor.close()
	db_connection.close()

	# -----END-----
	# if filename != dl_filename: # if must_dl and not options.init:
	if must_dl and not options.init:
		f = open(filename, 'a')
		diff_f = open(dl_filename, 'rU')
		f.writelines(diff_f.readlines())
		f.close()
		diff_f.close()
		os.remove(dl_filename)

	if not must_dl and not options.init and options.verbose:
		print 'no hice nada'

if __name__ == "__main__":
	main()
