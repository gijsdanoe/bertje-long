## Sentiment analysis
How to run:

1. Unzip 'data.zip' in '/data'.
2. Run:

  ```
  python3 model.py <model> <sequence length>
  ```
  
  Available models:
  - bertje-long
  - robbert-long
  - bertje
  - robbert
  - pino
  
  The sequence length of the long-document models can be up to 4096 and for the normal models up to 512. For this experiment 2048 and 512 have been chosen respectively.
  
3. Run the English Longformer test: 
  ```
  python3 lf_test.py
  ```
  
The bash scripts are for running on the Peregrine cluster.
