#!/usr/bin/env python

from utils import *

'''Skeleton sieve that cycles through anaphora and candidate mentions in the right order'''
def sieveSkeleton(mention_id_list, mention_dict, cluster_dict, cluster_id_list):
	mention_ids_per_sentence = get_mention_id_list_per_sentence(mention_id_list, mention_dict)
	for cluster_id in cluster_id_list[:]:
		print 'looking at cluster: %d' % cluster_id
		'''Initialize linking constraints here'''
		
		if madeLink:
			continue
		cluster = cluster_dict[cluster_id]
		anaphor = mention_dict[cluster.mentionList[0]] # Only consider first mention in cluster for resolution
		'''Check for constraints on the anaphor here'''
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
					'''Check things against the candidate mention here'''
					for ment_id in candidate_cluster.mentionList:
						'''Check things against other mentions in the candidate cluster here, if necessary'''
						if madeLink:
							print 'Linking clusters %d and %d' % (ment_id, anaphor.ID)
							break
	return mention_id_list, mention_dict, cluster_dict, cluster_id_list
