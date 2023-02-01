#!/usr/bin/env python

from utils import *

'''Dummy sieve that links each second mention to the preceding mention, for testing purposes (output/evaluation)'''
def sieveDummy(mention_id_list, mention_dict, cluster_dict, cluster_id_list):
	for idx, mention_id in enumerate(mention_id_list):
		if idx % 2 == 1: # Link every second mention with the mention 1 position back in the list
			cluster_dict, cluster_id_list = mergeClustersByMentionIDs(mention_id_list[idx], mention_id_list[idx-1], mention_dict, cluster_dict, cluster_id_list)
	return mention_id_list, mention_dict, cluster_dict, cluster_id_list
