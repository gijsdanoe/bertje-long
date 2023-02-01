import os, re
#TODO bug when (190|(190

class Mention:
	def __init(self):
		self.begin = 0
		self.end = 0
		self.ID = 0
		self.fileName = ''

num_ments = 0
ment_length = [0] * 100
#ref_dist_words = [0] * 100
ref_dist_ments = [0] * 100
num_ref = [0] * 20

def find_end(data, wordIdx, data_point):
	data_point = data_point[1:]
	if data_point[len(data_point)-1] == ')':
		return wordIdx
	else:
		innerFound = False
		for i in range(wordIdx+1, len(data)):
			for dataItr in data[i]:
				if dataItr == '(' + data_point:
					innerFound = True
				if data_point in dataItr and dataItr.endswith(')') and not dataItr.startswith('('):
					if innerFound:
						innerFound = False
					else:
						return i
	print ("ERROR")
def addCounts(data, filename):
	#print (filename)
	global num_ments, ment_length, ref_dist_words, num_ref
	ments = []
	for wordIdx in range(len(sent_data)):
		for data_point in data[wordIdx]:
			if data_point[0] == '(':
				new_ment = Mention()
				new_ment.begin = wordIdx
				
				new_ment.end = find_end(data, wordIdx, data_point)
				new_ment.ID = int(re.sub("\D", "", data_point))
				new_ment.filename = filename
				#print(new_ment.ID, new_ment.begin, new_ment.end)
				ments.append(new_ment)
	num_ments += len(ments)
	ids_done = []
	for i in range(len(ments)):
		ment_length[ments[i].end - ments[i].begin] += 1
		if ments[i].ID not in ids_done:
			num_refs = 0
			for j in range(i+1, len(ments)):
				if ments[i].ID == ments[j].ID:
					num_refs += 1
					#ref_dist_words[ments[j].begin - ments[i].end] += 1
					ref_dist_ments[j-i-1] += 1
			num_ref[num_refs] = num_ref[num_refs] + 1
			#if ments[j].begin - ments[i].end == 100:
				#print(ments[j].begin, ments[i].end,  ments[i].filename, ments[i].ID)
		ids_done.append(ments[i].ID)

data_dir = 'clinDevData/'
for co_file in os.listdir(data_dir):
	if co_file.endswith('_ne'):
		sent_data = []
		for line in open(data_dir + co_file):
			if len(line.split('\t')) > 2:
				ref_id = line.split('\t')[len(line.split('\t'))-1][:-1]
				if not ref_id == '_':
					sent_data.append(ref_id.split('|'))
		addCounts(sent_data, co_file)

print (' Number of mentions:  ') 
print (num_ments)

print (' Length of a mention measured in words:\n')
for i in range(20):
	print (str(i+1) + ':\t' + str(ment_length[i]))

#print ('\n Reference distance counted in number of words inbetween')
#for i in range(len(ref_dist_words)):
#	print (str(i) + ':\t' + str(ref_dist_words[i]))

print ('\n Reference distance counted in number of mentions inbetween')
for i in range(30):
	print (str(i) + ':\t' + str(ref_dist_ments[i]))

print ('\n Number of mentions per cluster')
for i in range(20):
	print (str(i+1) + ':\t' + str(num_ref[i]))

print ('\n')

