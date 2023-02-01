import find_errors
import count_nodes

def clean_attrib(attrib, atr_dict):
    if attrib in atr_dict:
        del atr_dict[attrib]

def clean_attribs(attributes):
    for atr in ['begin', 'end', 'id', 'sense', 'word', 'lemma', 'root', 'mwu_sense', 'mwu_root']:
        clean_attrib(atr, attributes)
    return attributes

def create_dict(data):
	feats_dict = {}
	for word in data:
		for attrib in clean_attribs(word):
			featName = attrib + '_' + word[attrib]
			if word[attrib].find('(') > 0:
				featName = attrib + '_' + word[attrib][:word[attrib].find('(')]
			if featName in feats_dict:
				feats_dict[featName] += 1
			else:
				feats_dict[featName] = 1
	return feats_dict

def compareDicts(err_dict, cor_dict):
	results = {}
	for attrib in err_dict:
		total = err_dict[attrib]
		if attrib in cor_dict:
			total += cor_dict[attrib]
		score = err_dict[attrib]/float(total)
		results[attrib] = score
	for attrib in sorted(results, key=lambda l:results[l]):
		if attrib in cor_dict:
			print attrib, results[attrib], err_dict[attrib], cor_dict[attrib] + err_dict[attrib]
		else:
			print attrib, results[attrib], err_dict[attrib]
			
if __name__ == '__main__':
	atr_err, atr_cor = find_errors.get_errors('../results/2015-11-17_15-52-52/')
	err_dict = create_dict(atr_err)
	cor_dict = create_dict(atr_cor)
	compareDicts(err_dict, cor_dict)
	"""
	all_counts = count_nodes.get_total_counts()
	all_dict = create_dict(all_counts)

	results = []
	for featName in err_dict:
		if featName in all_dict:
			results.append([float(err_dict[featName])/all_dict[featName], featName, err_dict[featName], all_dict[featName]])

	for feature in sorted(results, key=lambda l:l[0]):
		print feature
	print(len(errors))
	print(len(all_counts))
	"""
