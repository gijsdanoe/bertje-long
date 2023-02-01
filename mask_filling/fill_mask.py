#!/usr/bin/python3

import os
from transformers import BertForMaskedLM, BertTokenizerFast, AutoModelForMaskedLM, AutoTokenizer, LongformerForMaskedLM
import torch
import csv

try:
    from transformers.modeling_longformer import LongformerSelfAttention
except ImportError:
    from transformers import LongformerSelfAttention




models = ['gijsdanoe/bertje-long','gijsdanoe/robbert-long','GroNLP/bert-base-dutch-cased','pdelobelle/robbert-v2-dutch-base','markussagen/xlm-roberta-longformer-base-4096','flax-community/pino-bigbird-roberta-base']

dic = {}

for model_path in models:

    if model_path == 'gijsdanoe/robbert-long':
    	tokenizer_path = 'pdelobelle/robbert-v2-dutch-base'
    else:
    	tokenizer_path = model_path



    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
    model = AutoModelForMaskedLM.from_pretrained(model_path)

    # open text with <mask> for roberta models and [MASK] for BERT
    if model_path == '.gijsdanoe/bertje-long' or model_path == 'GroNLP/bert-base-dutch-cased':  
        f = open("text_long_bert.txt", "r")
        text_long = f.read()

        p = open("text_short_bert.txt", "r")
        text_short = p.read()
    else:
        f = open("text_long_roberta.txt", "r")
        text_long = f.read()

        p = open("text_short_roberta.txt", "r")
        text_short = p.read()

    # open gold standard words
    g = open("gold.txt", "r")
    gold = g.read().splitlines()

    # make predictions on short text for 512 token models and long text for efficient transformers
    if model_path == 'GroNLP/bert-base-dutch-cased' or model_path == 'pdelobelle/robbert-v2-dutch-base':
        predict = text_short
    else:
        predict = text_long


    inputs = tokenizer(predict, return_tensors='pt', max_length=4096)
    with torch.no_grad():
        logits = model(**inputs)[0]
    mask_token_index = (inputs.input_ids == tokenizer.mask_token_id)[0].nonzero(as_tuple=True)[0]
    predicted_token_id = logits[0, mask_token_index].argmax(axis=-1)
    predicted = tokenizer.decode(predicted_token_id).split()

    score = 0
    for x,y in zip(predicted, gold):
    	if x == y:
    		score += 1

    dic[model_path] = score, len(gold)
print(dic)
    
