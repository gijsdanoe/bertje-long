#!/usr/bin/env python

from utils import *

'''General head-matching sieve, value for strictness determines how many constraints are applied
strictness 3 = sieve 5, strictness 2 = sieve 6 and strictness 1 = sieve 7'''
def sieveHeadMatch(mention_id_list, mention_dict, cluster_dict, cluster_id_list, strictness, verbosity):
	mention_ids_per_sentence = get_mention_id_list_per_sentence(mention_id_list, mention_dict)
	if verbosity == 'high':
		print 'Doing head-matching with strictness %d...' % strictness
	for cluster_id in cluster_id_list[:]:
		# Initialize linking constraints here
		entityHeadMatch = False
		wordInclusion = False
		compModsOnly = False
		relaxedHeadMatch = False
		bothNE = False
		IwithinI = False
		madeLink = False # If a link has been made, look at the next cluster
		if madeLink:
			continue
		cluster = cluster_dict[cluster_id]
		anaphor = mention_dict[cluster.mentionList[0]] # Only consider first mention in cluster for resolution
		if not anaphor.headWords: # If no headwords, head-matching is not going to work
			continue
		# Find all words and modifiers in the anaphoric mention
		anaphorMods = []
		anaphorWords = []		
		for tokenAttrib in anaphor.tokenAttribs:
			if tokenAttrib["lemma"] not in stopWords:
				anaphorWords.append(tokenAttrib["lemma"])
			if tokenAttrib["rel"] == "mod":
				anaphorMods.append(tokenAttrib["lemma"])
		# Cycle through sentences backwards
		for sent_id in range(anaphor.sentNum, 0, -1): 
			if madeLink:
				break
			if sent_id in mention_ids_per_sentence:
				# Cycle through mentions within a sentence forwards
				for candidate_mention_id in mention_ids_per_sentence[sent_id]:
					if madeLink:
						break
					if candidate_mention_id == anaphor.ID: # Don't look ahead of anaphor
						break
					candidate_mention = mention_dict[candidate_mention_id]
					if not candidate_mention.headWords: # Without head words, head-matching is not going to work
						continue
					if candidate_mention.type.lower() == 'name' and anaphor.type.lower() == 'name':
						bothNE = True
					IwithinI = False
					entityHeadMatch = False
					relaxedHeadMatch = False
					if anaphor.sentNum == candidate_mention.sentNum and anaphor.begin >= candidate_mention.begin and \
						anaphor.end <= candidate_mention.end:
						IwithinI = True
					# Find all modifiers in the candidate mention
					candidateMentionMods = []
					for tokenAttrib in candidate_mention.tokenAttribs:
						if tokenAttrib['rel'] == "mod":
							candidateMentionMods.append(tokenAttrib["lemma"])
					candidate_cluster = cluster_dict[candidate_mention.clusterID]
					# Find all words in the candidate cluster
					candidateWords = []
					for ment_id in candidate_cluster.mentionList:
						for tokenAttrib in mention_dict[ment_id].tokenAttribs:
							if tokenAttrib["lemma"] not in stopWords:
								candidateWords.append(tokenAttrib["lemma"])
						if set(anaphor.headWords).issubset(set(mention_dict[ment_id].headWords)): # Check for entity head match
							entityHeadMatch = True
					if set(anaphor.headWords).issubset(set(candidateWords)): # Check for relaxed head match
						relaxedHeadMatch = True
					if set(anaphorWords).issubset(set(candidateWords)):	# Check for word inclusion		
						wordInclusion = True	
					if set(anaphorMods).issubset(set(candidateMentionMods)): # Check whether modifiers are compatible
						compModsOnly = True
					# Given a strictness, decide to make a link or not
					if strictness == 3: 
						if entityHeadMatch and wordInclusion and compModsOnly:
							if verbosity == 'high':
								print 'Linking clusters %d and %d' % (candidate_cluster.ID, anaphor.clusterID)
							cluster_dict, cluster_id_list = mergeClustersByMentionIDs(candidate_mention_id, anaphor.ID, \
								mention_dict, cluster_dict, cluster_id_list)
							madeLink = True
					elif strictness == 2:
						if entityHeadMatch and wordInclusion:
							if verbosity == 'high':						
								print 'Linking clusters %d and %d' % (candidate_cluster.ID, anaphor.clusterID)
							cluster_dict, cluster_id_list = mergeClustersByMentionIDs(candidate_mention_id, anaphor.ID, \
								mention_dict, cluster_dict, cluster_id_list)
							madeLink = True					
					elif strictness == 1:
						if entityHeadMatch and compModsOnly:
							if verbosity == 'high':						
								print 'Linking clusters %d and %d' % (candidate_cluster.ID, anaphor.clusterID)
							cluster_dict, cluster_id_list = mergeClustersByMentionIDs(candidate_mention_id, anaphor.ID, \
								mention_dict, cluster_dict, cluster_id_list)
							madeLink = True
					elif strictness == 0:
#						if relaxedHeadMatch and wordInclusion and not IwithinI:
						if relaxedHeadMatch and wordInclusion and bothNE: # Make it slightly more restrictive or not?
							if verbosity == 'high':						
								print 'Linking clusters %d and %d' % (ment_id, anaphor.ID)
							cluster_dict, cluster_id_list = mergeClustersByMentionIDs(candidate_mention_id, anaphor.ID, \
								mention_dict, cluster_dict, cluster_id_list)
							madeLink = True			
					if madeLink:
						break
	return mention_id_list, mention_dict, cluster_dict, cluster_id_list
