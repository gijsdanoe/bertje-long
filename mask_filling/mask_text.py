#!/usr/bin/python3

from random import randrange
import csv
from transformers import BertForMaskedLM, BertTokenizerFast, AutoModelForMaskedLM, AutoTokenizer, LongformerForMaskedLM



f = open("text.txt", "r")
text_short = f.read()

g = open("context.txt", "r")
text_long = g.read()

goldlist = []
wordlist = text_short.split()
wordlist2 = text_short.split()
for i in range(len(wordlist)):
    r = randrange(0, 100)
    if r <= 15:
        goldlist.append(wordlist[i])
        wordlist[i] = '[MASK]'
        wordlist2[i] = '<mask>'

text_masked = ' '.join(wordlist)
text_masked2 = ' '.join(wordlist2)

with open("text_long_bert.txt", "w") as text_file:
    text_file.write(text_long)
    text_file.write(text_masked)

with open("text_short_bert.txt", "w") as text_file:
    text_file.write(text_masked)

with open("text_long_roberta.txt", "w") as text_file:
    text_file.write(text_long)
    text_file.write(text_masked2)

with open("text_short_roberta.txt", "w") as text_file:
    text_file.write(text_masked2)


with open("gold.txt", "w") as text_file:
    for word in goldlist:
        text_file.write(word + '\n')


tokenizer = AutoTokenizer.from_pretrained('GroNLP/bert-base-dutch-cased')
inputs = tokenizer(text_masked, return_tensors='pt', max_length=4096)
print(len(inputs[0]))




