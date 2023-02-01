#!/usr/bin/env python

from utils import *

'''Pronoun resolution sieve'''
def sievePronounResolution(mention_id_list, mention_dict, cluster_dict, cluster_id_list, verbosity):
	if verbosity == 'high':
		print 'Doing pronoun resolution...'
	mention_ids_per_sentence = get_mention_id_list_per_sentence(mention_id_list, mention_dict)
	for cluster_id in cluster_id_list[:]:
		'''Initialize linking constraints here'''
		matchNumber = False
		matchGender = False
		matchPerson = False
#		matchAnimacy = False
		matchNER = False
		madeLink = False
		if madeLink:
			continue
		cluster = cluster_dict[cluster_id]
		anaphor = mention_dict[cluster.mentionList[0]] # Only consider first mention in cluster for resolution
		'''Check for constraints on the anaphor here'''
		if anaphor.type.lower() != 'pronoun': # Skip non-pronouns
			continue
#		else:
#			print 'Checking this anaphor:'
#			print anaphor.tokenList, anaphor.type, anaphor.number, anaphor.gender, anaphor.animacy, anaphor.person
		for sent_id in range(anaphor.sentNum, max(0, anaphor.sentNum-3), -1): # Cycle through sentences backwards, but through mentions within a sentence forwards
			if madeLink:
				break
			if sent_id in mention_ids_per_sentence: # Not empty
				for candidate_mention_id in mention_ids_per_sentence[sent_id]:
					if madeLink:
						break
					if candidate_mention_id == anaphor.ID: # Don't look ahead of anaphor
						break
					candidate_cluster = cluster_dict[mention_dict[candidate_mention_id].clusterID]
#					print 'looking at cluster %d' % candidate_cluster.ID
					'''Check things against the candidate mention here'''
					for ment_id in candidate_cluster.mentionList:
						'''Check things against other mentions in the candidate cluster here, if necessary'''
						matchNumber = False
						matchGender = False
						matchPerson = False
						matchNER = False
						cluster_mention = mention_dict[ment_id]
#						print cluster_mention.tokenList, cluster_mention.type, cluster_mention.number, cluster_mention.gender, cluster_mention.animacy, cluster_mention.NEtype
						if cluster_mention.number == anaphor.number or anaphor.number == 'unknown':
							matchNumber = True
						if cluster_mention.gender == anaphor.gender or anaphor.gender == 'unknown':
							matchGender = True
						if anaphor.animacy == 'animate':
							if cluster_mention.NEtype == 'person' or cluster_mention.NEtype == 'misc':
								matchNER = True
							if cluster_mention.NEtype == '' or cluster_mention.NEtype == 'unknown':
								matchNER = True
						else:
							if cluster_mention.NEtype != 'person':
								matchNER = True
							if cluster_mention.NEtype == '' or cluster_mention.NEtype == 'unknown':
								matchNER = True								
						if cluster_mention.type.lower() == 'pronoun':
							if cluster_mention.person == anaphor.person or anaphor.person == 'unknown':
								matchPerson = True
							if matchNumber and matchGender and matchPerson and matchNER:
								madeLink = True
						else:
							if matchNumber and matchGender and matchNER:
								madeLink = True
						if madeLink:
							if verbosity == 'high':
								print 'Linking clusters %d and %d' % (ment_id, anaphor.ID)
								cluster_dict, cluster_id_list = mergeClustersByMentionIDs(candidate_mention_id, anaphor.ID, \
									mention_dict, cluster_dict, cluster_id_list)
							break
	return mention_id_list, mention_dict, cluster_dict, cluster_id_list
