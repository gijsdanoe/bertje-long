## Mask filling
How to run:

1. In 'text.txt' paste your text. Then in 'context.txt', paste the extra context for the long models.
2. Run:
  ```
  python3 mask_text.py
  ```
  This will create 5 files:
  - text_short_bert, the short text with `[MASK]`
  - text_short_roberta, the short text with `<mask>`
  - text_long_bert, the full text with `[MASK]`
  - text_long_roberta, the full text with `<mask>`
  - gold, all the words that are masked
  
3. Run: 
  ```
  python3 fill_mask.py
  ```
  This will evaluate all models.
