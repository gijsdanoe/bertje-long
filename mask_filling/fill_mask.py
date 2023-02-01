#!/usr/bin/python3

import os
from transformers import BertForMaskedLM, BertTokenizerFast, AutoModelForMaskedLM, AutoTokenizer, LongformerForMaskedLM
import torch
import csv

try:
    from transformers.modeling_longformer import LongformerSelfAttention
except ImportError:
    from transformers import LongformerSelfAttention

class BertLongSelfAttention(LongformerSelfAttention):
    def forward(
        self,
        hidden_states,
        attention_mask=None,
        head_mask=None,
        encoder_hidden_states=None,
        encoder_attention_mask=None,
        past_key_value=None,
        output_attentions=False,
    ):
        return super().forward(hidden_states, attention_mask=attention_mask,
                output_attentions=output_attentions)


class BertLong(BertForMaskedLM):
    def __init__(self, config):
        super().__init__(config)
        for i, layer in enumerate(self.bert.encoder.layer):
            # replace the `modeling_bert.BertSelfAttention` object with
            # `LongformerSelfAttention`
            layer.attention.self = BertLongSelfAttention(config, layer_id=i)



models = ['/net/shared/andreas/bertje/longformer/bert-base-dutch-4096/','/net/shared/andreas/bertje/robbert-long/robbert-v2-dutch-base-4096/','GroNLP/bert-base-dutch-cased','pdelobelle/robbert-v2-dutch-base','markussagen/xlm-roberta-longformer-base-4096','flax-community/pino-bigbird-roberta-base']

dic = {}

for model_path in models:

    if model_path == '/Users/gijsdanoe/Documents/Informatiekunde/Masterscriptie/robbert-long/robbert-v2-dutch-base-4096':
    	tokenizer_path = 'pdelobelle/robbert-v2-dutch-base'
    else:
    	tokenizer_path = model_path



    tokenizer = AutoTokenizer.from_pretrained('GroNLP/bert-base-dutch-cased')
    model = AutoModelForMaskedLM.from_pretrained('/net/shared/andreas/bertje/longformer/bert-base-dutch-4096/')

    # open text with <mask> for roberta models and [MASK] for BERT
    if model_path == '/net/shared/andreas/bertje/longformer/bert-base-dutch-4096/' or model_path == 'GroNLP/bert-base-dutch-cased':  
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
    
