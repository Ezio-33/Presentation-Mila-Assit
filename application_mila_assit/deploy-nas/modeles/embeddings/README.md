---
pipeline_tag: sentence-similarity
language: fr
license: mit
datasets:
- unicamp-dl/mmarco
metrics:
- recall
tags:
- passage-retrieval
library_name: sentence-transformers
base_model: camembert-base
model-index:
- name: biencoder-camembert-base-mmarcoFR
  results:
    - task:
        type: sentence-similarity
        name: Passage Retrieval
      dataset:
        type: unicamp-dl/mmarco
        name: mMARCO-fr
        config: french
        split: validation
      metrics:
        - type: recall_at_500
          name: Recall@500
          value: 89.1
        - type: recall_at_100
          name: Recall@100
          value: 77.8
        - type: recall_at_10
          name: Recall@10
          value: 51.5
        - type: map_at_10
          name: MAP@10
          value: 27.9
        - type: ndcg_at_10
          name: nDCG@10
          value: 33.7
        - type: mrr_at_10
          name: MRR@10
          value: 28.5
---

# biencoder-camembert-base-mmarcoFR

This is a dense single-vector bi-encoder model for **French** that can be used for semantic search. The model maps queries and passages to 768-dimensional dense vectors which are used to compute relevance through cosine similarity.

## Usage

Here are some examples for using the model with [Sentence-Transformers](#using-sentence-transformers), [FlagEmbedding](#using-flagembedding), or [Huggingface Transformers](#using-huggingface-transformers).

#### Using Sentence-Transformers

Start by installing the [library](https://www.SBERT.net): `pip install -U sentence-transformers`. Then, you can use the model like this:

```python
from sentence_transformers import SentenceTransformer

queries = ["Ceci est un exemple de requête.", "Voici un second exemple."]
passages = ["Ceci est un exemple de passage.", "Et voilà un deuxième exemple."]

model = SentenceTransformer('antoinelouis/biencoder-camembert-base-mmarcoFR')
q_embeddings = model.encode(queries, normalize_embeddings=True)
p_embeddings = model.encode(passages, normalize_embeddings=True)

similarity = q_embeddings @ p_embeddings.T
print(similarity)
```

#### Using FlagEmbedding

Start by installing the [library](https://github.com/FlagOpen/FlagEmbedding/): `pip install -U FlagEmbedding`. Then, you can use the model like this:

```python
from FlagEmbedding import FlagModel

queries = ["Ceci est un exemple de requête.", "Voici un second exemple."]
passages = ["Ceci est un exemple de passage.", "Et voilà un deuxième exemple."]

model = FlagModel('antoinelouis/biencoder-camembert-base-mmarcoFR')
q_embeddings = model.encode(queries, normalize_embeddings=True)
p_embeddings = model.encode(passages, normalize_embeddings=True)

similarity = q_embeddings @ p_embeddings.T
print(similarity)
```

#### Using Transformers

Start by installing the [library](https://huggingface.co/docs/transformers): `pip install -U transformers`. Then, you can use the model like this:

```python
from transformers import AutoTokenizer, AutoModel
from torch.nn.functional import normalize

def mean_pooling(model_output, attention_mask):
    """ Perform mean pooling on-top of the contextualized word embeddings, while ignoring mask tokens in the mean computation."""
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


queries = ["Ceci est un exemple de requête.", "Voici un second exemple."]
passages = ["Ceci est un exemple de passage.", "Et voilà un deuxième exemple."]

tokenizer = AutoTokenizer.from_pretrained('antoinelouis/biencoder-camembert-base-mmarcoFR')
model = AutoModel.from_pretrained('antoinelouis/biencoder-camembert-base-mmarcoFR')

q_input = tokenizer(queries, padding=True, truncation=True, return_tensors='pt')
p_input = tokenizer(passages, padding=True, truncation=True, return_tensors='pt')
with torch.no_grad():
    q_output = model(**encoded_queries)
    p_output = model(**encoded_passages)
q_embeddings = mean_pooling(q_output, q_input['attention_mask'])
q_embedddings = normalize(q_embeddings, p=2, dim=1)
p_embeddings = mean_pooling(p_output, p_input['attention_mask'])
p_embedddings = normalize(p_embeddings, p=2, dim=1)

similarity = q_embeddings @ p_embeddings.T
print(similarity)
```

## Evaluation

The model is evaluated on the smaller development set of [mMARCO-fr](https://ir-datasets.com/mmarco.html#mmarco/v2/fr/), which consists of 6,980 queries for a corpus of 
8.8M candidate passages. We report the mean reciprocal rank (MRR), normalized discounted cumulative gainand (NDCG), mean average precision (MAP), and recall at various cut-offs (R@k).
To see how it compares to other neural retrievers in French, check out the [*DécouvrIR*](https://huggingface.co/spaces/antoinelouis/decouvrir) leaderboard.

## Training

#### Data

We use the French training samples from the [mMARCO](https://huggingface.co/datasets/unicamp-dl/mmarco) dataset, a multilingual machine-translated version of MS MARCO that contains 8.8M passages and 539K training queries. We do not employ the BM25 netaives provided by the official dataset but instead sample harder negatives mined from 12 distinct dense retrievers, using the [msmarco-hard-negatives](https://huggingface.co/datasets/sentence-transformers/msmarco-hard-negatives) distillation dataset.

#### Implementation

The model is initialized from the [camembert-base](https://huggingface.co/camembert-base) checkpoint and optimized via the cross-entropy loss (as in [DPR](https://doi.org/10.48550/arXiv.2004.04906)) with a temperature of 0.05. It is fine-tuned on one 32GB NVIDIA V100 GPU for 20 epochs (i.e., 65.7k steps) using the AdamW optimizer with a batch size of 152, a peak learning rate of 2e-5 with warm up along the first 500 steps and linear scheduling. We set the maximum sequence lengths for both the questions and passages to 128 tokens. We use the cosine similarity to compute relevance scores.

## Citation

```bibtex
@online{louis2024decouvrir,
	author    = 'Antoine Louis',
	title     = 'DécouvrIR: A Benchmark for Evaluating the Robustness of Information Retrieval Models in French',
	publisher = 'Hugging Face',
	month     = 'mar',
	year      = '2024',
	url       = 'https://huggingface.co/spaces/antoinelouis/decouvrir',
}
```