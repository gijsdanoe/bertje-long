"""Extract BERT token embeddings for sentences.

Based on https://github.com/Filter-Bubble/e2e-Dutch/blob/master/e2edutch/bert.py
"""
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import sys

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel, logging
from coref import gettokens
from glob import glob
import re
from lxml import etree
import getopt

logging.set_verbosity_error()

def parsesentid(path):
	"""Given a filename, return tuple with numeric components for sorting.

	Accepts three formats: 1.xml, 1-2.xml, abc.p.1.s.2.xml """
	filename = os.path.basename(path)
	x = tuple(map(int, re.findall(r'\d+', filename.rsplit('.', 1)[0])))
	if len(x) == 1:
		return 0, x[0]
	elif re.match(r'\d+-\d+.xml', filename):
		return x
	elif re.match(r'.*p\.[0-9]+\.s\.[0-9]+\.xml', filename):
		return x[-2:]
	else:
		raise ValueError('expected sentence ID of the form sentno.xml, '
				'parno-sentno.xml, p.parno.s.sentno.xml. Got: %s' % filename)

def loadmodel(name):
	"""Load BERT model."""
	if name == 'bertje-long':
		tokenizer = AutoTokenizer.from_pretrained('/net/shared/andreas/bertje/longformer/bert-base-dutch-4096')
		bertmodel = AutoModel.from_pretrained('/net/shared/andreas/bertje/longformer/bert-base-dutch-4096')
	if name == 'robbert-long':
		tokenizer = AutoTokenizer.from_pretrained('pdelobelle/robbert-v2-dutch-base')
		bertmodel = AutoModel.from_pretrained('/net/shared/andreas/bertje/robbert-long/robbert-v2-dutch-base-4096')
	if name == 'bertje':
		tokenizer = AutoTokenizer.from_pretrained('wietsedv/bert-base-dutch-cased')
		bertmodel = AutoModel.from_pretrained('wietsedv/bert-base-dutch-cased')
	if name == 'robbert':
		tokenizer = AutoTokenizer.from_pretrained('pdelobelle/robbert-v2-dutch-base')
		bertmodel = AutoModel.from_pretrained('pdelobelle/robbert-v2-dutch-base')
	if name == 'pino':
		tokenizer = AutoTokenizer.from_pretrained('flax-community/pino-bigbird-roberta-base')
		bertmodel = AutoModel.from_pretrained('flax-community/pino-bigbird-roberta-base')
	if name == 'xlm-l':
		tokenizer = AutoTokenizer.from_pretrained('markussagen/xlm-roberta-longformer-base-4096')
		bertmodel = AutoModel.from_pretrained('markussagen/xlm-roberta-longformer-base-4096')
        
	return tokenizer, bertmodel


def getvectors(parses, trees, tokenizer, model, context, name, cache=True):
	"""Encode sentences in `trees` and cache in file next to directory
	with parses."""
	cachefile = parses + '.%s-%s-vectors.npy' % (name,context)
	if (cache and os.path.exists(cachefile) and os.stat(cachefile).st_mtime
			> os.stat(parses).st_mtime):
		embeddings = np.load(cachefile)
	else:
		# use BERT to obtain vectors for the text of the given trees
		sentences = [gettokens(tree, 0, 9999) for _, tree in trees]
		# NB: this encodes each sentence independently
		# embeddings = encode_sentences(sentences, tokenizer, model)
		result = []
		for n in range(len(sentences)):
			# each sentence independently
			if context == 'sent':
				for sent in _encode_sentences(sentences[n:n + 1], tokenizer, model):
					result.extend(sent)
			# with context
			else:
				maxsegmentlen = int(context)
				result.extend(encode_sentences_overlap(sentences, n, tokenizer, model, maxsegmentlen))
			
		embeddings = np.array(result)
		if cache:
			np.save(cachefile, embeddings)
	return embeddings



def encode_sentences_overlap(sentences, n, tokenizer, model, maxsegmentlen,
		layer=9):
	"""Encode tokens of sentences[n] with BERT.
	Encodes a segment of up to 128 subwords consisting of sentences that
	precede sentences[n] and sentences[n] itself.
	:returns: an array of shape (sent_length, hidden_size=768)
	Layer 9 gives the best results with coreference, according to
	https://www.aclweb.org/anthology/2020.findings-emnlp.389.pdf"""
	# Apply BERT tokenizer (even if sentences are already tokenized, since BERT
	# uses subword tokenization).
	if n < 0 or n >= len(sentences):
		raise ValueError('n (%d) is out of bounds; len(sentences) == %d'
				% (n, len(sentences)))
	tokenized = [tokenizer.tokenize(word) for word in sentences[n]]
	nnumtokens = sum(1 for word in tokenized for tok in word)

	segmentlen = 0
	nn = n
	while nn >= 0:
		tokenized = [tokenizer.tokenize(word) for word in sentences[nn]]
		numtokens = sum(1 for word in tokenized for tok in word)
		if segmentlen + numtokens >= maxsegmentlen:
			break
		segmentlen += numtokens
		nn -= 1
	if segmentlen == 0 and nnumtokens < 512:
		nn = n - 1  # long sentence, use all subwords, but disable context.
	elif segmentlen == 0:
		raise ValueError('Sentence %d longer (%d subwords) than 512 subwords?'
				% (n, numtokens))
	sentence = sum(sentences[nn + 1:n + 1], [])
	#print(len(sentence), file=sys.stderr)
	#print('encoding', sentence, file=sys.stderr)
	sentence_tokenized = [tokenizer.tokenize(word) for word in sentence]
	sentence_tokenized_flat = [tok for word in sentence_tokenized
			for tok in word]
	indices_flat = [i for i, word in enumerate(sentence_tokenized)
				for tok in word]

	max_nrtokens = len(sentence_tokenized_flat)
	indexed_tokens = np.zeros((1, max_nrtokens), dtype=int)
	idx = tokenizer.convert_tokens_to_ids(sentence_tokenized_flat)
	indexed_tokens[0, :len(idx)] = np.array(idx)

	# Convert inputs to PyTorch tensors
	tokens_tensor = torch.tensor(indexed_tokens)
	with torch.no_grad():
		# torch tensor of shape (n_sentences, sent_length, hidden_size=768)
		outputs = model(tokens_tensor, output_hidden_states=True, return_dict=True)
		bert_output = outputs.hidden_states[layer].numpy()

	# Add up tensors for subtokens coming from same word
	max_sentence_length = len(sentence)
	bert_final = np.zeros((max_sentence_length, bert_output.shape[2]))
	counts = np.zeros(len(sentence))
	for tok_id, word_id in enumerate(indices_flat):
		bert_final[word_id, :] += bert_output[0, tok_id, :]
		counts[word_id] += 1
	for word_id, count in enumerate(counts):
		if count > 1:
			bert_final[word_id, :] /= count
	bert_final = np.array(bert_final)
	return bert_final[-nnumtokens:, :]


def _encode_sentences(sentences, tokenizer, model, layer=9):
	"""Encode tokens with BERT.

	:returns: an array of shape (n_sentences, sent_length, hidden_size=768)

	Layer 9 gives the best results with coreference, according to
	https://www.aclweb.org/anthology/2020.findings-emnlp.389.pdf"""
	# Apply BERT tokenizer (even if sentences are already tokenized, since BERT
	# uses subword tokenization).
	sentences_tokenized = [
			[tokenizer.tokenize(word) for word in sentence]
			for sentence in sentences]
	sentences_tokenized_flat = [
			[tok for word in sentence for tok in word]
			for sentence in sentences_tokenized]
	indices_flat = [
			[i for i, word in enumerate(sentence)
				for tok in word]
			for sentence in sentences_tokenized]

	max_nrtokens = max(len(s) for s in sentences_tokenized_flat)
	indexed_tokens = np.zeros((len(sentences), max_nrtokens), dtype=int)
	for i, sent in enumerate(sentences_tokenized_flat):
		idx = tokenizer.convert_tokens_to_ids(sent)
		indexed_tokens[i, :len(idx)] = np.array(idx)

	# Convert inputs to PyTorch tensors
	tokens_tensor = torch.tensor(indexed_tokens)
	with torch.no_grad():
		# torch tensor of shape (n_sentences, sent_length, hidden_size=768)
		outputs = model(tokens_tensor, output_hidden_states=True, return_dict=True)
		bert_output = outputs.hidden_states[layer].numpy()

	# Add up tensors for subtokens coming from same word
	max_sentence_length = max(len(s) for s in sentences)
	bert_final = np.zeros((bert_output.shape[0],
			max_sentence_length,
			bert_output.shape[2]))   
	for sent_id in range(len(sentences)):
		counts = np.zeros(len(sentences[sent_id]))
		for tok_id, word_id in enumerate(indices_flat[sent_id]):
			bert_final[sent_id, word_id, :] += bert_output[sent_id, tok_id, :]
			counts[word_id] += 1
		for word_id, count in enumerate(counts):
			if count > 1:
				bert_final[sent_id, word_id, :] /= count
	bert_final = np.array(bert_final)
	return bert_final


