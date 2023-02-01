#!/usr/bin/python3

import os
from transformers import BertForMaskedLM, BertTokenizerFast
import torch
import csv

model_path = 'wietsedv/bert-base-dutch-cased'
tokenizer = BertTokenizerFast.from_pretrained(model_path)

trainpospath = '/home/s3494888/Scriptie/DBRD/train/pos/'

trainposlist = []

for filename in os.listdir(trainpospath):
    f = os.path.join(trainpospath,filename)
    if os.path.isfile(f):
        with open(f) as text: # Use file to refer to the file object
            review = text.read()
            trainposlist.append(review)
        
print(len(trainposlist))

trainnegpath = '/home/s3494888/Scriptie/DBRD/train/neg/'

trainneglist = []

for filename in os.listdir(trainnegpath):
    f = os.path.join(trainnegpath,filename)
    if os.path.isfile(f):
        with open(f) as text: # Use file to refer to the file object
            review = text.read()
            trainneglist.append(review)
    
print(len(trainneglist))

with open('train.csv', 'w', newline='') as train:
    writer = csv.writer(train)
    for pos,neg in zip(trainposlist,trainneglist):
        writer.writerow([pos, "pos"])
        writer.writerow([neg, "neg"])
        


testpospath = '/home/s3494888/Scriptie/DBRD/test/pos/'

testposlist = []

for filename in os.listdir(testpospath):
    f = os.path.join(testpospath,filename)
    if os.path.isfile(f):
        with open(f) as text: # Use file to refer to the file object
            review = text.read()
            tokenized_input = tokenizer.tokenize(review)
            if len(tokenized_input) >= 512:
                testposlist.append(review)
        
print(len(testposlist))

testnegpath = '/home/s3494888/Scriptie/DBRD/test/neg/'

testneglist = []

for filename in os.listdir(testnegpath):
    f = os.path.join(testnegpath,filename)
    if os.path.isfile(f):
        with open(f) as text: # Use file to refer to the file object
            review = text.read()
            tokenized_input = tokenizer.tokenize(review)
            if len(tokenized_input) >= 512:
                testneglist.append(review)
    
print(len(testneglist))

with open('test.csv', 'w', newline='') as test:
    writer = csv.writer(test)
    for pos,neg in zip(testposlist,testneglist):
        writer.writerow([pos, "pos"])
        writer.writerow([neg, "neg"])
