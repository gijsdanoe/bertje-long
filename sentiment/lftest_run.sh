#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --gres=gpu:v100:1
#SBATCH --time=50:00:00
#source /data/$USER/.envs/masterthesis_env/bin/activate
source /data/$USER/.envs/bert_env/bin/activate
python lftest.py
