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

filename = 'CSD.txt'
sql_table = 'cfd_certs'
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

"""Generates a diff file to import, appends '_diff' to new's fileanme
writes the file and returns the filename"""
def make_diff(old, new):
	fromlines = open(old, 'U').readlines()
	tolines = open(new, 'U').readlines()
	diff_filename = new[:-4] + '_diff' + new[-4:]
	diff = unified_diff(fromlines, tolines, n=0)
	diff_file = open(diff_filename, 'w')
	diff_file.writelines(diff)
	diff_file.close()
	return diff_filename

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
	parser = OptionParser("python sat_import_certs [options]")
	parser.add_option('--init', action='store_true', dest='init', default=False,
		help='Vacia las tablas e importa (--no-ftp o --force-dl implican esto).')
	parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False,
		help='Modo callado/silencioso. Tambien evita las preguntas.')
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
	
	old_filename = filename[:-4] + '_old' + filename[-4:] # CSD_old.txt
	if must_dl:
		if os.access(filename, os.F_OK) and not options.init:
			try:
				os.rename(filename, old_filename)
			except WindowsError: # will overwirte on unix, do the same on windows
				os.remove(old_filename)
				os.rename(filename, old_filename)

		write_file = open(filename, 'wb') # global
		if options.verbose:
			widgets = [progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA(), ' ', progressbar.FileTransferSpeed()]
			print 'Descargando: ', filename #, '\n\ta:', dl_filename
			# globals shared with progress_write : dl_bar, write_file, dlded_size
			dl_bar = progressbar.ProgressBar(maxval=remote_filestats['size'], widgets=widgets) 
			# write_filename = files[f]['local']['dlded']
			dlded_size = 0
			dl_bar.start()
			write_func = progress_write
		else: 
			# efectively call: sat_ftp.retrbinary('RETR %s' %filanme, open(filename, 'wb').write)
			write_func = write_file.write

		# Do the downloading
		sat_ftp.retrbinary('RETR %s' %filename, write_func)
		write_file.close()

	sat_ftp.close()

	# -----pre-SQL-----
	# make SQL statement
	if os.access(old_filename, os.F_OK) and not options.init:
		import_filename = make_diff(old_filename, new_filename)
		ignore_lines = 3
		start_by = " STARTING BY '+' "
		replace = ' REPLACE '
	else:
		import_filename = filename
		ignore_lines = 1
		replace = ' '
		start_by = ' '
		# so that the table is truncated because the difference file is not being used
		# options.init = True

	newlines = get_newlines(import_filename)
	import_filename = os.path.abspath(import_filename).replace('\\', r'\\')
	import_sql = "LOAD DATA INFILE%s'%s' INTO TABLE %s FIELDS TERMINATED BY '|'LINES%sTERMINATED BY %s IGNORE %i LINES;" \
		% (replace, import_filename, sql_table, start_by, newlines, ignore_lines)

	# -----SQL-----
	db_connection = MySQLdb.connect(host=sql_host, port=sql_port, user=sql_user, passwd=sql_passwd, db=sql_database)
	cursor = db_connection.cursor()
	if options.init:
		if options.verbose:
			print 'Vaciando tabla: ', sql_table

		cursor.execute('TRUNCATE TABLE ' + sql_table + ';')
		db_connection.commit()
	
	if must_dl or options.init: # if nothing was downladed and not --init was passed do nothing
		if options.verbose:
			print datetime.now(), 'Importando: ', os.path.basename(import_filename), ' a tabla: ', sql_table
			print cursor.execute(import_sql), ' registros agregados'
		else:
			cursor.execute(import_sql)
			
		db_connection.commit()
		if options.verbose:
			print datetime.now(), 'Finalizado'

	cursor.close()
	db_connection.close()

	# -----END-----
	try:
		os.remove(old_filename)
	except:
		pass

	try:
		os.remove(diff_filename)
	except:
		pass

if __name__ == "__main__":
	main()
