#!/usr/bin/env python
# -*- coding: utf8 -*-

""" Pipeline script that does coreference resolution and evaluation, given
a conll-formatted file or directory containing conll-formatted files. Expects
Alpino parses to be present already. """

import argparse, os, re, subprocess, datetime
import preprocess_clin_data
import coreference_resolution
from utils import *

def processDocument(filename, verbosity, sieveList, ngdata):
	''' Do preprocessing, coreference resolution and evaluation for a single 
	document.
	'''
	global timestamp
	if verbosity != 'none':
		print 'processing ' + filename + '...'
	output_filename = 'results/' + timestamp + '/' + filename.split('/')[-1] #+ '.coref'
	scores_filename = output_filename + '.scores'
	if re.search('coref_ne', filename):
		isClinData = True
	else:
		isClinData = False
	if isClinData:
		preprocess_clin_data.preprocess_file(filename)
	with open(scores_filename, 'w') as scores_file:
		if isClinData:
			coreference_resolution.main(filename + '.forscorer', output_filename, True, verbosity, sieveList, ngdata, 'conll')
			subprocess.call(["conll_scorer/scorer.pl", "all", filename + '.forscorer', output_filename, "none"], stdout = scores_file)
		else:
			coreference_resolution.main(filename, output_filename, True, verbosity, sieveList, ngdata, 'conll')
			subprocess.call(["conll_scorer/scorer.pl", "all", filename, output_filename, "none"], stdout = scores_file)
		
def processDirectory(dirname, verbosity, sieveList, ngdata):
	'''Do preprocessing, coreference resolution and evaluation for all 
	documents in a directory.
	'''
	for filename in os.listdir(dirname):
		if os.path.isfile(dirname + filename):
			if re.search('.xml.coref_ne$', filename) or re.search('.xml.conll$', filename):
				processDocument(dirname + filename, verbosity, sieveList, ngdata)
				
def postProcessScores(scores_dir, verbosity, onlyTotal = False):
	''' Aggregates and formats evaluation scores of one or more documents,
	outputs to 'scores_overall'-file
	'''
	scores = {} # Format: {doc_name: {metric: [Pkey, Ppred, P, Rkey, Rpred, R, F1]} }
	metric = ''
	for filename in os.listdir(scores_dir):
		if os.path.isfile(scores_dir + '/' + filename) and re.search('.scores$', filename):
			docName = filename.split('_')[0]
			scores[docName] = process_conll_scorer_file(scores_dir + '/' + filename)
#			scores[docName] = {'muc' : [], 'bcub' : [], 'ceafm' : [], 'ceafe' : [], 'blanc' : [], 'conll' : [], 'md' : []}
#			for metric in scores[docName]:
#				scores[docName][metric] = [0, 1, 0, 0, 1, 0, 0]
#			with open(scores_dir + '/' + filename, 'r') as scores_file:
#				for line in scores_file:
#					if re.search('^METRIC', line):
#						metric = re.split(' ', line)[-1][:-2] # Extract metric name
#					if scores[docName]['md'] == [0, 1, 0, 0, 1, 0, 0]: # Avoid filling entry 5 times
#						if re.search('^Identification', line):
#							values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
#							scores[docName]['md'] = values[0:6] + values[7:] # At index 6 is the '1' from 'F1', so ignore
#					if metric == 'blanc':
#						if re.search('^BLANC', line):
#							values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
#							scores[docName][metric] = values[0:6] + values[7:]
#					else:
#						if re.search('^Coreference:', line):
#							values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
#							scores[docName][metric] = values[0:6] + values[7:]
#			scores[docName]['conll'] = [(scores[docName]['muc'][6] + scores[docName]['bcub'][6] + scores[docName]['ceafe'][6]) / 3] # Calculate CoNLL-F1
#	# Calculate across-document scores
	totals = {'muc' : [], 'bcub' : [], 'ceafm' : [], 'ceafe' : [], 'blanc' : [], 'md' : [], 'blanc-special' : []}
	for metric in totals:
		totals[metric] = [0, 0, 0, 0, 0, 0, 0]
	for document in scores: # Sum all documents' values
		for metric in scores[document]:
			if metric != 'conll' and metric != 'blanc-special':
				totals[metric] = [val1 + val2 for val1, val2 in zip(totals[metric], scores[document][metric])]
			if metric == 'blanc-special':
				totals[metric] = [val1 + val2 for val1, val2 in zip(totals[metric], scores[document][metric])]
	for metric in totals:
		if metric != 'blanc-special':
			try:
				totals[metric][2] = totals[metric][0] / totals[metric][1] * 100
			except ZeroDivisionError:
				totals[metric][2] = 0
			try:
				totals[metric][5] = totals[metric][3] / totals[metric][4] * 100
			except ZeroDivisionError:
				totals[metric][5] = 0
			try:
				totals[metric][6] = 2 * totals[metric][2] * totals[metric][5] / (totals[metric][2] + totals[metric][5])
			except ZeroDivisionError:
				totals[metric][6] = 0
	totals['conll'] = [(totals['muc'][6] + totals['bcub'][6] + totals['ceafe'][6] ) / 3]

	coref_recall = totals['blanc-special'][0] / totals['blanc-special'][1]
	try:
		coref_precision = totals['blanc-special'][0] / totals['blanc-special'][2]
	except ZeroDivisionError:
		coref_precision = 0
	non_recall = totals['blanc-special'][3] / totals['blanc-special'][4]
	try:
		non_precision = totals['blanc-special'][3] / totals['blanc-special'][5]
	except ZeroDivisionError:
		non_precision = 0
	try:
		coref_f = 2*coref_recall*coref_precision/(coref_recall+coref_precision)
	except ZeroDivisionError:
		coref_f = 0
	try:
		non_f = 2*non_recall*non_precision/(non_recall+non_precision)
	except ZeroDivisionError:
		non_f = 0		
#	print coref_recall, coref_precision, coref_f
#	print non_recall, non_precision, non_f
	blanc_recall = (coref_recall+non_recall)/2
	blanc_precision = (coref_precision+non_precision)/2
	blanc_f = (coref_f + non_f)/2
	totals['blanc'][2] = blanc_recall*100
	totals['blanc'][5] = blanc_precision*100
	totals['blanc'][6] = blanc_f*100
	
#	print scores
#	print totals['blanc-special']
	# Print scores to screen and file
	with open(scores_dir + '/' + 'scores_overall', 'w') as out_file:
		if verbosity == 'high':
			print '#########################################\nSCORES:'
		else:
			if not onlyTotal:
				print 'SCORES:'
#		header = 'document name\t\tMD-r/p/f1\t\tMUC-r/p/f1\t\tBCUB-r/p/f1\t\tCEAFM-r/p/f1\t\tCEAFE-r/p/f1\t\tBLANC-r/p/f1\t\tCONLL-f1'
		header = 'document name\tMD-r/p/f1\t\tMUC-r/p/f1\t\tBLANC-r/p/f1\t\tBLANC-coref\t\tBLANC-non-ref\t\tCONLL-f1'
		if not onlyTotal:
			print header
		out_file.write(header + '\n')
		for document in scores:
			docName = document + (16 - len(document)) * ' '
			a = scores[document]
			doc_coref_recall = a['blanc-special'][0] / a['blanc-special'][1]
			try:
				doc_coref_precision = a['blanc-special'][0] / a['blanc-special'][2]
			except ZeroDivisionError:
				doc_coref_precision = 0
			doc_non_recall = a['blanc-special'][3] / a['blanc-special'][4]
			try:
				doc_non_precision = a['blanc-special'][3] / a['blanc-special'][5]
			except ZeroDivisionError:
				doc_non_precision = 0
			try:
				doc_coref_f = 2*doc_coref_recall*doc_coref_precision/(doc_coref_recall+doc_coref_precision)
			except ZeroDivisionError:
				doc_coref_f = 0
			try:
				doc_non_f = 2*doc_non_recall*non_precision/(doc_non_recall+doc_non_precision)
			except ZeroDivisionError:
				doc_non_f = 0				
#			scorestring = '%s\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f' % (docName,  a['md'][2],  a['md'][5],  a['md'][6], a['muc'][2], a['muc'][5], a['muc'][6], a['bcub'][2], a['bcub'][5], a['bcub'][6], a['ceafm'][2], a['ceafm'][5], a['ceafm'][6], a['ceafe'][2], a['ceafe'][5], a['ceafe'][6], a['blanc'][2], a['blanc'][5], a['blanc'][6], a['conll'][0])
			scorestring = '%s%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f' % (docName,  a['md'][2],  a['md'][5],  a['md'][6], a['muc'][2], a['muc'][5], a['muc'][6], a['blanc'][2], a['blanc'][5], a['blanc'][6], doc_coref_recall*100, doc_coref_precision*100, doc_coref_f*100, doc_non_recall*100, doc_non_precision*100, doc_non_f*100, a['conll'][0])
			if not onlyTotal:
				print scorestring
			out_file.write(scorestring + '\n')
		if verbosity == 'high':
			print 'OVERALL:'
		a = totals
#		scorestring = '%s\t\t\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f' % ('TOTAL',  a['md'][2],  a['md'][5],  a['md'][6], a['muc'][2], a['muc'][5], a['muc'][6], a['bcub'][2], a['bcub'][5], a['bcub'][6], a['ceafm'][2], a['ceafm'][5], a['ceafm'][6], a['ceafe'][2], a['ceafe'][5], a['ceafe'][6], a['blanc'][2], a['blanc'][5], a['blanc'][6], a['conll'][0])	
		scorestring = '%s\t\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f' % ('TOTAL',  a['md'][2],  a['md'][5],  a['md'][6], a['muc'][2], a['muc'][5], a['muc'][6], a['blanc'][2], a['blanc'][5], a['blanc'][6], coref_recall*100, coref_precision*100, coref_f*100, non_recall*100, non_precision*100, non_f*100, a['conll'][0])
		print scorestring
		out_file.write(scorestring)
	
if __name__ == '__main__':
	# Parse input arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('target', type=str, help='Path to a file or directory, in .conll format, for which to do coreference resolution.')
	parser.add_argument('-v', '--verbosity', type = str, help = 'Verbosity of output, can be either "high" or "low", default is "high"', default = 'high')
	parser.add_argument('-s', '--sieve', help = 'Given this flag, scores after each sieve are reported', dest = 'per_sieve', action = 'store_true')
	args = parser.parse_args()
	# Put output in timestamped sub-folder of results/
	timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
	print 'Timestamp for this run is: %s' % timestamp
	if args.verbosity == 'high':
		print 'Reading in number-gender data...'	
	ngdata = read_number_gender_data('ngdata') # Read in number-gender data
	if args.verbosity == 'high':
		print 'Done!'
	os.system('mkdir -p results/' + timestamp)
	if os.path.isdir(args.target):
		args.target += '/'
		if args.per_sieve:
			print '\t\tMD-r/p/f1\t\tMUC-r/p/f1\t\tBLANC-r/p/f1\t\tBLANC-coref\t\tBLANC-non-ref\t\tCONLL-f1'
			for i in range(0, len(allSieves) + 1):
				processDirectory(args.target, 'none', allSieves[:i], ngdata)
				print 'using these sieves: ' + str(allSieves[:i])
				postProcessScores('results/' + timestamp, 'low', True)				
		else:
			processDirectory(args.target, args.verbosity, range(0, 20), ngdata) # Give range(0,20) as sieveList, so that all sieves are applied
	elif os.path.isfile(args.target):
		if args.per_sieve:
			print '\t\tMD-r/p/f1\t\tMUC-r/p/f1\t\tBLANC-r/p/f1\t\tBLANC-coref\t\tBLANC-non-ref\t\tCONLL-f1'
			for i in range(0, len(allSieves)):
				processDocument(args.target, 'none', allSieves[:i+1], ngdata)
				print 'using these sieves: ' + str(allSieves[:i+1])
				postProcessScores('results/' + timestamp, 'low', True)
		else:
			processDocument(args.target, args.verbosity, range(0, 20), ngdata)
	else:
		print 'Incorrect input file or directory'
		raise SystemExit
	if not args.per_sieve:
		postProcessScores('results/' + timestamp, args.verbosity)
	print 'Timestamp for this run was: %s' % timestamp
	
