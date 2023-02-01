#!/usr/bin/env python

import colorama as c
import re, sys, os
import xml.etree.ElementTree as ET
from time import sleep
### GLOBAL VARIABLES ###

# List of Dutch Stop words (http://www.ranks.nl/stopwords/dutch)
stopWords = ['aan', 'af', 'al', 'als', 'bij', 'dan', 'dat', 'die', 'dit', 'een', 'en', 'er', 'had', 'heb', 'hem', 'het', 'hij', 'hoe', 'hun', 'ik ', 'in', 'is', 'je', 'kan', 'me', 'men', 'met', 'mij', 'nog', 'nu', 'of', 'ons', 'ook', 'te', 'tot', 'uit', 'van', 'was ', 'wat', 'we', 'wel', 'wij', 'zal', 'ze', 'zei', 'zij', 'zo', 'zou']

# First available mentionID
mentionID = 0 

# List of implemented sieves
allSieves = [1,2, 4, 5, 6, 7, 9, 10]
#allSieves = [1,2,10]

### CLASSES ### 

# Class for 'mention'-objects
class Mention:
	'Class of mentions, containing features, IDs, links, etc.'
	def __init__(self, mentionID):
		self.ID = mentionID # ID can be used for mention ordering, but then ID assignment needs to be more intelligent/different
		self.sentNum = 0
		self.tokenList = []
		self.numTokens = 0
		self.begin = 0 # Token ID of first token
		self.end = 0 # Token ID of last token + 1
		self.type = '' # Pronoun, NP or Name
		self.clusterID = -1
		self.head_begin = 0 # Token ID of first head word, within tokenList
		self.head_end = 0
		self.headWords = []
		self.tokenAttribs = [] # List of dictionaries containing alpino output for each token/node
		self.tree = ''
		# All features can have value 'unknown' when no value can be extracted
		self.number = '' # Mention number, from {'singular', 'plural', 'both'}
		self.gender = '' # Mention gender, from {'male', 'female', 'neuter', 'nonneuter'} 
		self.person = '' # Pronoun-mention person, from {'1', '2', '3'}
		self.animacy = '' # Mention animacy, from {'animate', 'inanimate', 'organization'}
		self.NEtype = '' # Named-entity mention type, from {'location', 'person', 'organization', 'misc', 'year'}	
		self.pron_type = ''#relative pronouns
		
# Class for 'cluster'-objects
class Cluster:
	'Class of clusters, which contain features, an ID and a list of member-mentions-IDs'
	def __init__(self, clusterID):
		self.ID = clusterID
		self.mentionList = []

### READING AND WRITING ###

# Read in conll file, return list of lists containing a single word + annotation
def read_conll_file(fname):
	conll_list = []
	num_sentences = 0
	for line in open(fname, 'r'):
		split_line = line.strip().split('\t')
		if len(split_line) > 1:
			if split_line[0] != 'doc_id' and line[0] != '#': # Skip header and/or document tags
				conll_list.append(split_line)
		if not line.strip() or line == '#end document': # Empty line equals new sentence
			num_sentences += 1
	return conll_list, num_sentences
	
# Read in xml-files containing parses for sentences in document, return list of per-sentence XML trees
def read_xml_parse_files(fname):
	xml_tree_list = []
	dir_name = '/'.join(fname.split('/')[0:-1]) + '/' + fname.split('/')[-1].split('_')[0] + '/'
	xml_file_list = os.listdir(dir_name)
	delete_list = []
	for i in range (len(xml_file_list)):
		if not xml_file_list[i].endswith('.xml'):
			delete_list.append(i)
	for i in range (len(delete_list)):
		backwards = delete_list[(len(delete_list)-1)-i]
		del xml_file_list[backwards]
	# Sort list of filenames naturally (by number, not by alphabet)
	xml_file_list = [xml_file[:-4] for xml_file in xml_file_list]
	xml_file_list.sort(key=int)
	xml_file_list = [xml_file + '.xml' for xml_file in xml_file_list]
	for xml_file in xml_file_list:
		if re.search('[0-9].xml', xml_file):
			try:
				tree = ET.parse(dir_name + xml_file)
			except IOError:
				print 'Parse file not found: %s' % (xml_file)
		xml_tree_list.append(tree)
	return xml_tree_list
	
# Creates conll-formatted output with the clustering information
def generate_conll(docName, output_filename, doc_tags, sentenceDict, mention_dict, scorer):
	output_file = open(output_filename, 'w')
	if scorer == 'clin':
		docName = docName.split('/')[-1][:-10]
	else:
		docName = docName.split('/')[-1].split('_')[0]
	if doc_tags:
		if scorer == 'clin':
			output_file.write('#begin document (' + docName + ');\n') #  part 000
		else:	
			output_file.write('#begin document (' + docName + '); part 000\n')
	doc_token_id = 0	
	for key in sorted(sentenceDict.keys()): # Cycle through sentences
		for token_idx, token in enumerate(sentenceDict[key].split(' ')): # Cycle through words in sentences
			corefLabel = ''
			doc_token_id += 1
			for mention_id, mention in mention_dict.iteritems(): # Check all mentions, to see whether token is part of mention
				if mention.sentNum == key:
					if token_idx == mention.begin: # Start of mention, print a bracket
						if corefLabel:
							corefLabel += '|'
						corefLabel += '('
					if token_idx >= mention.begin and token_idx < mention.end:
						if corefLabel:
							if corefLabel[-1] != '(':
								corefLabel += '|'
						corefLabel += str(mention.clusterID)
					if token_idx + 1 == mention.end: # End of mention, print a bracket
						corefLabel += ')'
			if not corefLabel: # Tokens outside of mentions get a dash
				corefLabel = '-'
			output_file.write(docName + '\t' + str(doc_token_id) + '\t' + token.encode('utf-8') + '\t' + corefLabel + '\n')
		output_file.write('\n')
	if doc_tags:
		output_file.write('#end document')	

### COREFERENCE SIEVE HELPERS ###

# Function that takes two mention ids, and merges the clusters they are part of, returns cluster dict and cluster_id_list
def mergeClustersByMentionIDs(idx1, idx2, mention_dict, cluster_dict, cluster_id_list):
	mention1 = mention_dict[idx1]
	mention2 = mention_dict[idx2]
	if mention1.clusterID == mention2.clusterID: # Cannot merge if mentions are part of same cluster
		return
	cluster1 = cluster_dict[mention1.clusterID]
	cluster2 = cluster_dict[mention2.clusterID]
	# Put all mentions of cluster2 in cluster1
	for mentionID in cluster2.mentionList:
		cluster_dict[mention1.clusterID].mentionList.append(mentionID)
		for mention_id, mention in mention_dict.iteritems():
			if mention.ID == mentionID:
				mention.clusterID = cluster1.ID
	del cluster_dict[cluster2.ID]
	cluster_id_list.remove(cluster2.ID)
	return cluster_dict, cluster_id_list
	
# Takes mention_id_list, returns a dict, with mention_ids per sentence
def get_mention_id_list_per_sentence(mention_id_list, mention_dict):
	mention_ids_per_sentence = {}
	for mention_id in mention_id_list:
		mention = mention_dict[mention_id]
		if mention.sentNum in mention_ids_per_sentence:
			mention_ids_per_sentence[mention.sentNum].append(mention.ID)
		else:
			mention_ids_per_sentence[mention.sentNum] = [mention.ID]
	return mention_ids_per_sentence
	
### MENTION DETECTION HELPERS ###
# Helper for mentionDetection()
def make_mention(begin, end, tree, mention_type, sentNum, ngdata):
	global mentionID
	new_ment = Mention(mentionID)
	mentionID += 1
	new_ment.type = mention_type
	new_ment.begin = int(begin)
	new_ment.end = int(end)
	new_ment.numTokens = new_ment.end - new_ment.begin
	new_ment.sentNum = sentNum
	new_ment.tree = tree
	for i in range(new_ment.begin, new_ment.end ):
		node = tree.find(".//node[@word][@begin='" + str(i) + "']")
		new_ment.tokenList.append(node.attrib["word"])
		new_ment.tokenAttribs.append(node.attrib)
	# Extract additional pronouns
	if len(new_ment.tokenAttribs) == 1:
		if 'pronoun' in new_ment.tokenAttribs[0]['frame'].lower():
			new_ment.type = 'pronoun'
	if mention_type.lower()[:2] == 'np':
		if mention_type.lower() == 'np_comma':
			headRange = []
			for i in range(len(new_ment.tokenAttribs)):
				if 'rel' in new_ment.tokenAttribs[i] and new_ment.tokenAttribs[i]['rel'] == 'hd':
					headRange.append(i)
			if len (headRange) == 0:
				new_ment.head_begin = new_ment.end - 1 - new_ment.begin
				new_ment.head_end = new_ment.end - new_ment.begin
				new_ment.headWords = [new_ment.tokenList[-1]]
			else:
				new_ment.head_begin = headRange[0]
				new_ment.head_end = headRange[-1] + 1
				new_ment.headWords = new_ment.tokenList[new_ment.head_begin:new_ment.head_end]
		else:
			mention_node = tree.find(".//node[@cat='np'][@begin='" + str(begin) + "'][@end='" + str(end) + "']")
			head_node = mention_node.find("./node[@rel='hd']")
			new_ment.head_begin = int(head_node.attrib['begin']) - new_ment.begin
			new_ment.head_end = int(head_node.attrib['end']) - new_ment.begin
			new_ment.headWords = new_ment.tokenList[new_ment.head_begin:new_ment.head_end]
	elif mention_type.lower() == 'su': # Deal with su's in a hacky way
		mention_node = tree.find(".//node[@begin='" + begin + "'][@end='" + end + "']")
		if mention_node is not None:
			head_node = mention_node.find("./node[@rel='hd']")
			if head_node is not None:
				new_ment.head_begin = int(head_node.attrib['begin']) - new_ment.begin
				new_ment.head_end = int(head_node.attrib['end']) - new_ment.begin
				new_ment.headWords = new_ment.tokenList[new_ment.head_begin:new_ment.head_end]
			else:
				new_ment.head_begin = len(new_ment.tokenList) - 1
				new_ment.head_end = len(new_ment.tokenList)
				new_ment.headWords = new_ment.tokenList[-1:]
		else:
			new_ment.head_begin = len(new_ment.tokenList) - 1
			new_ment.head_end = len(new_ment.tokenList)
			new_ment.headWords = new_ment.tokenList[-1:]
	elif mention_type.lower() == 'name' or mention_type.lower()[:3] == 'mwu': # Add last part of names as headword
		new_ment.head_begin = len(new_ment.tokenList) - 1
		new_ment.head_end = len(new_ment.tokenList)
		new_ment.headWords = new_ment.tokenList[-1:]
		if not re.search('[a-zA-Z]', new_ment.tokenList[-1]): # Head cannot just be numbers, need to contain letters
			new_ment.head_begin = len(new_ment.tokenList) - 2
			new_ment.head_end = len(new_ment.tokenList) - 1
			new_ment.headWords = new_ment.tokenList[-2:-1]
	elif mention_type.lower() == 'noun':
		new_ment.head_begin = 0
		new_ment.head_end = 1
		new_ment.headWords = [new_ment.tokenList[0]]
	else: # Backup option
		if mention_type.lower() != 'pronoun':
			new_ment.head_begin = len(new_ment.tokenList) - 1
			new_ment.head_end = len(new_ment.tokenList)
			new_ment.headWords = new_ment.tokenList[-1:]
	# Make all head words lower case or not? Yes, because it works, but I don't know why, since precision goes up and recall down
	new_ment.headWords = [headWord.lower() for headWord in new_ment.headWords]
	new_ment = add_mention_features(new_ment, ngdata) # Add features for pronoun resolution
	return new_ment
				
# Add features (number, gender, animacy, NEtype, person) to a mention
def add_mention_features(mention, ngdata):
	# Base mention features on attributes of first headword
	attribs = mention.tokenAttribs[mention.head_begin]
	''' Extract number attribute '''
	try:
		if 'num' not in attribs and 'rnum' in attribs:
			attribs['num'] = attribs['rnum']
		if 'num' not in attribs and 'rnum' not in attribs and 'getal' in attribs:
			attribs['num'] = attribs['getal']
		if attribs['num'] in ['sg', 'ev']:
			mention.number = 'singular'
		elif attribs['num'] in ['pl', 'mv']:
			mention.number = 'plural'
		elif attribs['num'] == 'both':
			mention.number = 'both'
		else:
			mention.number = 'unknown'
		if 'neclass' in attribs:
			if attribs['neclass'] == 'ORG':
				mention.number = 'both'
	except KeyError:
		mention.number = 'unknown'
	''' Extract gender attribute '''
	if 'genus' in attribs:
		if attribs['genus'] == 'masc':
			mention.gender = 'male'
		elif attribs['genus'] == 'onz':
			mention.gender = 'neuter'
		elif attribs['genus'] == 'zijd':
			mention.gender = 'nonneuter'
	if 'neclass' in attribs or mention.type.lower() == 'name':
		'''separate gender classification for NEs (mentions with NE heads)'''
		lowered_token_list = [token.lower() for token in mention.tokenList]
		gender_data = [0, 0, 0, 0]
		try:
			gender_data = [a + b for a, b in zip(gender_data, ngdata[' '.join(lowered_token_list)])]
		except KeyError:
			try: # If not found exactly, try with only headwords
				lowered_head_list = [head.lower() for head in mention.headWords]
				gender_data = [a + b for a, b in zip(gender_data, ngdata[' '.join(lowered_head_list)])]
			except KeyError: # If still not found, sum all things starting and ending with the individual head words
				try:
					for lowered_head in lowered_head_list:
						gender_data = [a + b for a, b in zip(gender_data, ngdata[lowered_head + ' !'])]
						gender_data = [a + b for a, b in zip(gender_data, ngdata['! ' + lowered_head])]
				except KeyError: # If still nothing, give up
					gender_data = [0, 0, 0, 0]
		# If more than a third of total counts in either column, classify as such
		if gender_data[0] > sum(gender_data)/3:
			mention.gender = 'male'
		elif gender_data[1] > sum(gender_data)/3:
			mention.gender = 'female'
		elif gender_data[0] > sum(gender_data)/3 and gender_data[1] > sum(gender_data)/3:
			mention.gender = 'nonneuter'
		elif gender_data[2] > sum(gender_data)/3:
			mention.gender = 'neuter'
		elif gender_data[3] > sum(gender_data)/3:							
			mention.number = 'plural'
			mention.gender = 'neuter'
	if not mention.gender:
		mention.gender = 'unknown'
	''' Extract person attribute for pronouns '''
	if mention.type.lower() == 'pronoun':
		try:
			mention.person = attribs['persoon'][0]
			mention.pron_type = attribs['vwtype']
			if attribs['persoon'] == 'persoon':
				mention.person = 'unknown'
			
		except KeyError:
			mention.persoon = 'unknown'
	''' Extract named-entity-type attribute '''
	if 'neclass' in attribs:
		if attribs['neclass'] == 'LOC':
			mention.NEtype = 'location'
		elif attribs['neclass'] == 'ORG':
			mention.NEtype = 'organization'
		elif attribs['neclass'] == 'PER':
			mention.NEtype = 'person'
		elif attribs['neclass'] == 'MISC':
			mention.NEtype = 'misc'
		elif attribs['neclass'] == 'year':
			mention.NEtype = 'year'
		else:
			mention.NEtype = 'unknown'
	if mention.type.lower() == 'name' and not mention.NEtype:
		mention.NEtype = 'unknown'	
	''' Extract animacy attribute '''
	if mention.NEtype == 'person':
		mention.animacy = 'animate'	
	elif mention.NEtype == 'organization':
		mention.animacy = 'organization'
	elif mention.NEtype:
		mention.animacy = 'inanimate'
	if mention.type.lower() == 'pronoun':
		if 'vwtype' in attribs and attribs['vwtype'] == 'vb':
			mention.animacy = 'inanimate'
		else:
			mention.animacy = 'animate'	
	if not mention.animacy:
		'''fancy animacy classification here, or not?'''
		pass
	return mention

# Stitch multi-word name mentions together
def stitch_names(node_list, tree, sentNum, ngdata):
	node_list.sort(key=lambda node: int(node.attrib['begin']))
	added = [False] * len(node_list)
	mentions = []
	for beg_idx in range(len(node_list)):
		if not added[beg_idx]:
			added[beg_idx] = True
			beg_val = int(node_list[beg_idx].attrib['begin'])
			end_val = int(node_list[beg_idx].attrib['end'])
			for next_idx in range(beg_idx + 1, len(node_list)):
				if int(node_list[next_idx].attrib['begin']) == end_val:
					end_val += 1
					added[next_idx] = True
				else:
					break
			mentions.append(make_mention(beg_val, end_val, tree, 'name', sentNum, ngdata))
	return mentions

# Sort mentions in list by sentNum, begin, end
def sort_mentions(mention_id_list, mention_dict):
	return sorted(mention_id_list, key = lambda x: (mention_dict[x].sentNum, mention_dict[x].begin, mention_dict[x].end))	

def add_mention(mention_list, new_mention):
	for old_mention in mention_list:
		if old_mention.begin == new_mention.begin and old_mention.end == new_mention.end and old_mention.sentNum == new_mention.sentNum:
			return mention_list
	mention_list.append(new_mention)
	return mention_list 
	
# Creates a cluster for each mention, fills in features
def initialize_clusters(mention_dict, mention_id_list):
	cluster_id_list = []
	cluster_dict = {}
	for mention_id in mention_id_list:
		mention = mention_dict[mention_id]
		new_cluster = Cluster(mention.ID) # Initialize with same ID as initial mention
		new_cluster.mentionList.append(mention.ID)
		mention_dict[mention_id].clusterID = new_cluster.ID
		cluster_dict[new_cluster.ID] = new_cluster
		cluster_id_list.append(new_cluster.ID)
	return cluster_dict, cluster_id_list, mention_dict
	
# Reads in noun phrase number-gender data
def read_number_gender_data(filename):
	ngdata = {} # Format: {NP: [masc, fem, neuter, plural]}
	for line in open(filename, 'r'):
		split_line = line.strip().split('\t')
		ngdata[split_line[0]] = [int(x) for x in split_line[1].split(' ')]
	return ngdata
	
### MENTION PRINTING ###
	
# Human-readable printing of the output of the mention detection sieve	
def print_mentions_inline(sentenceDict, mention_id_list, mention_dict):
	for sentNum in sentenceDict:
		sentLength = len(sentenceDict[sentNum].split(' '))
		closingBrackets = '' # Print closing brackets for mention that close at end of sentence
		for idx, token in enumerate(sentenceDict[sentNum].split(' ')):
			for mention_id in mention_id_list:
				mention = mention_dict[mention_id]
				if mention.sentNum == sentNum:
					if mention.begin == idx:
						print colour_text('[', 'red'),
					if mention.end == idx:
						print colour_text(']', 'red'),
					if idx + 1 == sentLength and mention.end == sentLength:
						closingBrackets += '] '
			print colour_text(token.encode('utf-8'), 'white'),
			print colour_text(closingBrackets, 'red'),
		print ''
		
# Human-readable printing of a comparison between the output of the mention detection sieve	and the 'gold' standard
# Green brackets are correct, gold/orange brackets are mention boundaries only found in the gold standard, and
# red brackets are only found in our output
def print_mention_analysis_inline(conll_list, sentenceDict, mention_id_list, mention_dict):
	doc_token_id = -1
	for sentNum in sentenceDict:
		sentLength = len(sentenceDict[sentNum].split(' '))
		closingBrackets = '' # Print closing brackets for mention that close at end of sentence
		for idx, token in enumerate(sentenceDict[sentNum].split(' ')):
			gold_open = 0
			gold_close = 0
			resp_open = 0
			resp_close = 0
			doc_token_id += 1
			for mention_id in mention_id_list:
				mention = mention_dict[mention_id]
				if mention.sentNum == sentNum:
					if mention.begin == idx:
						resp_open += 1				
					if mention.end - 1 == idx:
						resp_close += 1
					elif idx + 1 == sentLength and mention.end == sentLength:
						resp_close += 1
			gold_open = len(re.findall('\(', conll_list[doc_token_id][-1]))
			gold_close = len(re.findall('\)', conll_list[doc_token_id][-1]))
			if gold_open >= resp_open:
				sys.stdout.write((gold_open - resp_open) * colour_text('[', 'yellow'))
				sys.stdout.write(resp_open * colour_text('[', 'green'))
			else:
				sys.stdout.write((resp_open - gold_open) * colour_text('[', 'red'))
				sys.stdout.write(gold_open * colour_text('[', 'green'))
				
			print colour_text(token.encode('utf-8'), 'white'),		
						
			if gold_close >= resp_close:
				sys.stdout.write((gold_close - resp_close) * colour_text(']', 'yellow'))
				sys.stdout.write(resp_close * colour_text(']', 'green') + ' ')
			else:
				sys.stdout.write((resp_close - gold_close) * colour_text(']', 'red'))
				sys.stdout.write(gold_close * colour_text(']', 'green') + ' ')								
		print ''
		
# Human-readable printing of gold standard mentions
def print_gold_mentions(conll_list, sentenceDict):
	doc_token_id = -1
	for sentNum in sentenceDict:
		sentLength = len(sentenceDict[sentNum].split(' '))
		closingBrackets = '' # Print closing brackets for mention that close at end of sentence
		for idx, token in enumerate(sentenceDict[sentNum].split(' ')):
			gold_open = 0
			gold_close = 0
			doc_token_id += 1
			
			gold_open = len(re.findall('\(', conll_list[doc_token_id][-1]))
			gold_close = len(re.findall('\)', conll_list[doc_token_id][-1]))
			
			sys.stdout.write(gold_open * colour_text('[', 'yellow'))
			print colour_text(token.encode('utf-8'), 'white'),		
			sys.stdout.write(gold_close * colour_text(']', 'yellow') + ' ')								
		print ''	
		
# Human-readable printing of which mentions are clusterd by a given sieve
# Pre-sieve cluster IDs are in light blue, post-sieve cluster IDs (if changed) are in green
def print_linked_mentions(old_mention_dict, mention_id_list, mention_dict, sentenceDict):
	linkings = {}
	for mention_id in mention_id_list:
		if mention_dict[mention_id].clusterID != old_mention_dict[mention_id].clusterID:
			linkings[old_mention_dict[mention_id].clusterID] = mention_dict[mention_id].clusterID
	for sentNum in sentenceDict:
		sentLength = len(sentenceDict[sentNum].split(' '))
		closingBrackets = '' # Print closing brackets for mention that close at end of sentence
		for idx, token in enumerate(sentenceDict[sentNum].split(' ')):
			for mention_id in mention_id_list:
				mention = old_mention_dict[mention_id]
				if mention.sentNum == sentNum:
					if mention.begin == idx:
						print colour_text('[', 'red'),
						if mention.clusterID in linkings:
							print colour_text(str(mention.clusterID), 'cyan'),
							print colour_text(str(linkings[mention.clusterID]), 'green'),
						else:
							print colour_text(str(mention.clusterID), 'cyan'),						
					if mention.end == idx:
						print colour_text(']', 'red'),
					if idx + 1 == sentLength and mention.end == sentLength:
						closingBrackets += '] '			
			print colour_text(token.encode('utf-8'), 'white'),
			print colour_text(closingBrackets, 'red'),
		print ''
	
# Returns coloured text
def colour_text(text, colour):
	if colour.lower() == 'red':
		return c.Fore.RED + text + c.Fore.RESET
	elif colour.lower() == 'blue':
		return c.Fore.BLUE + text + c.Fore.RESET	
	elif colour.lower() == 'green':
		return c.Fore.GREEN + text + c.Fore.RESET	
	elif colour.lower() == 'white':
		return c.Fore.WHITE + text + c.Fore.RESET
	elif colour.lower() == 'yellow':
		return c.Fore.YELLOW + text + c.Fore.RESET		
	elif colour.lower() == 'cyan':
		return c.Fore.CYAN + text + c.Fore.RESET
		
# Prints all mentions and attributes in order		
def print_all_mentions_ordered(mention_id_list, mention_dict):
	for mention_id in mention_id_list:
		print mention_dict[mention_id].__dict__
		
### SCORING HELPERS ###

# Takes a scorer-output file, returns a dict with the scores
def process_conll_scorer_file(scorer_filename):
	scores = {'muc' : [], 'bcub' : [], 'ceafm' : [], 'ceafe' : [], 'blanc' : [], 'conll' : [], 'md' : [], 'blanc-special' : []}
	metric = ''
	for metric in scores:
		scores[metric] = [0, 1, 0, 0, 1, 0, 0]
	with open(scorer_filename, 'r') as scores_file:
		for line in scores_file:
			if re.search('^METRIC', line):
				metric = re.split(' ', line)[-1][:-2] # Extract metric name
			if scores['md'] == [0, 1, 0, 0, 1, 0, 0]: # Avoid filling entry 5 times
				if re.search('^Identification', line):
					values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
					scores['md'] = values[0:6] + values[7:] # At index 6 is the '1' from 'F1', so ignore
			if metric == 'blanc': # Treat specially
				if re.search('^Coreference links', line):
					values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
					scores['blanc-special'][0] = values[0]
					scores['blanc-special'][1] = values[1]
					scores['blanc-special'][2] = values[4]
				if re.search('Non-', line):
					values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
					scores['blanc-special'][3] = values[0]
					scores['blanc-special'][4] = values[1]
					scores['blanc-special'][5] = values[4]
				if re.search('^BLANC', line):
					values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
#					scores[metric][2] = values[2]
#					scores[metric][5] = values[5]
#					scores[metric][6] = values[7]
					scores[metric] = values[0:6] + values[7:]
			else:
				if re.search('^Coreference:', line):
					values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
					scores[metric] = values[0:6] + values[7:]
	scores['conll'] = [(scores['muc'][6] + scores['bcub'][6] + scores['ceafe'][6]) / 3] # Calculate CoNLL-F1
#	print scores
	return scores
	
# 
def process_and_print_clin_scorer_file(scorer_filename):
	idx = 0
	for line in open(scorer_filename, 'r'):
		idx += 1
		line = line.strip()
		if 'MENTIONS (key mentions' in line:
			print '\nNumber of mentions in gold standard: %s' % (line.split('=')[-1][:-1])
		if '# response mentions' in line:
			response_mentions = line.split('\t')[-1]
		if '# missed mentions'  in line:
			missed_mentions = line.split('\t')[-1]
		if 'invented mentions' in line:
			invented_mentions = line.split('\t')[-1]
		if 'strictly correct' in line:
			print 'Number of mentions in our output: %s,' % response_mentions,
			print 'of which %s correct, %s missed and %s extra.' % (line.split('\t')[-1], missed_mentions, invented_mentions)
		if 'BLANC' in line:
			print 'BLANC scoring showed the following results:'
		if 'key coreference' in line:
			key_coref = line.split('\t')[-1][:-2]
		if 'response coreference' in line:
			response_coref = line.split('\t')[-1][:-2]
		if 'correct coreference' in line:
			correct_coref = line.split('\t')[-1][:-2]
			print 'Number of coreference links in the gold standard: %s' % (key_coref)
			print 'We made %s coreference links, of which %s were correct, and %d were wrong\n' % (response_coref, correct_coref, int(response_coref) - int(correct_coref))
		if 'Macro average id' in line:
			print 'Macro average scores of mention detection are as follows:'
		if 'Macro average blanc' in line:
			print 'Macro average BLANC scores are as follows:'
		if 'recall' in line:
			recall = line.split('\t')[-1][:4]
		if 'precision' in line:
			precision = line.split('\t')[-1][:4]
		if 'f1' in line:
			f1 = line.split('\t')[-1][:4]
			if idx < 30 or idx > 47:
				print 'A recall of %05.2f, a precision of %05.2f and a F1 of %05.2f\n' % (float(recall), float(precision), float(f1))




	
