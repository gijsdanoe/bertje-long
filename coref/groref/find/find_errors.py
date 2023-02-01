import os, re, pickle, sys
import xml.etree.ElementTree as ET

class Mention:
	def __init__(self):
		self.begin = 0
		self.end = 0
		self.ID = 0
		self.filename = ''
		self.parsefile = ''
		self.tokenList = []
		self.tokenAttribs = []

atr_err = []
atr_cor = []
word_errors = 0
subtree_errors = 0
nontree_errors = 0
def find_attributes(mention, atr):
	global word_errors, subtree_errors, nontree_errors
	tree = ET.parse(mention.parsefile)
	subtrees = tree.findall('.//node[@begin="' + str(mention.begin) + '"][@end="' + str(mention.end) + '"]')
	if int(mention.end) - int(mention.begin) == 1:
		word_errors += 1
	elif len(subtrees) > 0:
		subtree_errors += 1
		firstChild = subtrees[0].find('.//node[@word]')
		lastChild = subtrees[len(subtrees)-1].find('.//node[@word]')
		if (lastChild == None):
			lastChild = subtrees[len(subtrees)-2].find('.//node[@word]')
		if (lastChild != None):
			atr.append(lastChild.attrib)
		else:
			print ("None")
	else:
		nontree_errors += 1
	print mention.tokenList
	print mention.parsefile

	
def found(mention, mentionList):
	
	for mentionItr in mentionList:
		if mention.parsefile == mentionItr.parsefile and mention.begin == mentionItr.begin and mention.end == mentionItr.end:
			return True
	return False

def find_errors(mentions_gold, mentions_own):
	for mention in mentions_own: # other way around for recall/precision
		if not found(mention, mentions_gold):
			find_attributes(mention, atr_err)
		else:
			find_attributes(mention, atr_cor)

def find_end(data, wordIdx, data_point, data_point_idx):
        data_point = data_point[1:]
        if data_point[len(data_point)-1] == ')':
                return wordIdx + 1
        else:
                innerFound = 0
                for i in range(wordIdx, len(data)):
			data_point_beg = 0
			if i == wordIdx:
				data_point_beg = data_point_idx + 1
                        for data_point_itr in range(data_point_beg, len(data[i])):
				dataItr = data[i][data_point_itr]
                                if dataItr == '(' + data_point:
                                        innerFound += 1
                                if data_point in dataItr and dataItr.endswith(')') and not dataItr.startswith('('):
					if innerFound > 0:
                                                innerFound -= 1
                                        else:
                                                return i + 1
        print ("ERROR")

def find_mentions(filename, co_file):
	sents_data = []
	sent_data = []
	for line in open(filename):
		if line.startswith('#'):
			pass
		elif len(line.split('\t')) > 2:
			ref_id = line.split('\t')[len(line.split('\t'))-1][:-1]
			sent_data.append(ref_id.split('|'))
		else:
			sents_data.append(sent_data)
			sent_data = []
	mentions = []
	for i in range(len(sents_data)):
		data = sents_data[i]
	        for wordIdx in range(len(data)):
			for data_point_idx in range(len(data[wordIdx])):
				data_point = data[wordIdx][data_point_idx]
        		        if data_point[0] == '(':
                			new_ment = Mention()
                        		new_ment.begin = wordIdx

                	                new_ment.end = find_end(data, wordIdx, data_point, data_point_idx)
		                        new_ment.ID = int(re.sub("\D", "", data_point))
	        	                new_ment.filename = co_file
					new_ment.parsefile = '../clinDevData/'+co_file[:co_file.find('_')] + '/' + str(i+1) + '.xml'
					tree = ET.parse(new_ment.parsefile)
					for node in tree.findall(".//node[@word]"):
						if int(node.attrib['begin']) >= new_ment.begin and int(node.attrib['end']) <= new_ment.end:
							new_ment.tokenList.append(node.attrib["word"])
							new_ment.tokenAttribs.append(node.attrib)
                	                mentions.append(new_ment)
	return mentions

def get_errors(own_dir):
	gold_dir = '../clinDevData/'
	for co_file in os.listdir(gold_dir):
        	if co_file.endswith('_ne') :
			mentions_gold = find_mentions(gold_dir + co_file, co_file)
			mentions_own = find_mentions(own_dir + co_file, co_file)
			find_errors(mentions_gold, mentions_own)
	print word_errors
	print subtree_errors
	print nontree_errors
	print word_errors + subtree_errors + nontree_errors


	return atr_err, atr_cor
