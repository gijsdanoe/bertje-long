import pickle

pos_words = pickle.load(open('err_word.pickle'))
all_words = pickle.load(open('all.pickle'))

featIdx = 0
def create_dict(data):
	feats_dict = {}
	for word in data:
		for attrib in word:
			if word[attrib].find('(') > 0:
				featName2 = attrib + '_' + word[attrib][:word[attrib].find('(')]
				if featName2 in feats_dict:
					feats_dict[featName2] += 1
				else:
					feats_dict[featName2] = 1
			else:
				featName = attrib + '_' + word[attrib]
				if featName in feats_dict:
					feats_dict[featName] += 1
				else:
					feats_dict[featName] = 1
				
	return feats_dict
pos_dict = create_dict(pos_words)
all_dict = create_dict(all_words)

results = []
for featName in pos_dict:
	results.append([float(pos_dict[featName])/all_dict[featName], featName, pos_dict[featName], all_dict[featName]])

for feature in sorted(results, key=lambda l:l[0]):
	print feature

