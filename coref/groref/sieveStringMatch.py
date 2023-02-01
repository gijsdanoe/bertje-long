#!/usr/bin/env python

from utils import *

'''links two mentions only if they contain exactly the same extent text, including modifiers and determiners'''
def sieveStringMatch(mention_id_list, mention_dict, cluster_dict, cluster_id_list, verbosity):
	mention_ids_per_sentence = get_mention_id_list_per_sentence(mention_id_list, mention_dict)
	if verbosity == 'high':
		print 'Doing exact + relaxed string matching...'
	for cluster_id in cluster_id_list[:]:
		ExactEntityMatch = False
		RelaxedEntityMatch = False
		madeLink = False
		if madeLink:
			continue
		cluster = cluster_dict[cluster_id]
		anaphor = mention_dict[cluster.mentionList[0]] # Only consider first mention in cluster for resolution			
		anaphor_relaxedtokenlist = []		
		for token in anaphor.tokenList:
			if len(anaphor.headWords) > 0:
				if token == anaphor.headWords[0]:
					anaphor_relaxedtokenlist.append(token.lower())
					break
				else:
					anaphor_relaxedtokenlist.append(token.lower())
		for sent_id in range(anaphor.sentNum, 0, -1): # Cycle through sentences backwards, but through mentions within a sentence forwards
			if madeLink:
				break						
			if sent_id in mention_ids_per_sentence: # Not empty
				for candidate_mention_id in mention_ids_per_sentence[sent_id]:						
					if madeLink:
						break
					if candidate_mention_id == anaphor.ID: # Don't look ahead of anaphor
						break
					candidate_cluster = cluster_dict[mention_dict[candidate_mention_id].clusterID]		
					for ment_id in candidate_cluster.mentionList:
						'''Exact Match'''		
						if mention_dict[ment_id].tokenList == anaphor.tokenList:
							ExactEntityMatch = True				
						'''Relaxed Match'''
						ment_relaxedtokenlist = []
						for token in mention_dict[ment_id].tokenList:
							if len(mention_dict[ment_id].headWords) > 0:
								if token == mention_dict[ment_id].headWords[0]:
									ment_relaxedtokenlist.append(token.lower())
									break
								else:
									ment_relaxedtokenlist.append(token.lower())
						if len(ment_relaxedtokenlist) > 0:
							if ment_relaxedtokenlist == anaphor_relaxedtokenlist:
								RelaxedEntityMatch = True			
						if ExactEntityMatch or RelaxedEntityMatch:							
							if verbosity == 'high':						
								print 'Linking clusters %d and %d' % (ment_id, anaphor.ID)							
							cluster_dict, cluster_id_list = mergeClustersByMentionIDs(ment_id, anaphor.ID, \
								mention_dict, cluster_dict, cluster_id_list)	
							madeLink = True					
						if madeLink:
							break
	return mention_id_list, mention_dict, cluster_dict, cluster_id_list
	
	

