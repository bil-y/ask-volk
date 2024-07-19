"""
author: carlo schmid
"""

import re
import spacy
from spacy.lang.de import German
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import pandas as pd

# paths
leaflets_path = "../../data/leaflets/leaflets_merged.csv"
topics_path = "../../data/topics/summary_topics.csv"

def extract_sentences(text: str):
    # remove newlines etc.
    text = str(text)
    text = text.replace("\n", " ")
    text = re.sub(r"\s[a-z]\.\s", " ", text)
    text = re.sub(r"\s[0-9]\s", " ", text)

    # split into sentences using spacy
    nlp = German()
    sbd = nlp.create_pipe('sentencizer')
    nlp.add_pipe('sentencizer')
    doc = nlp(text)
    sents = doc.sents
    sents_list = []
    for sent in doc.sents:
        sents_list.append(sent.text)
    return(sents_list)

# define contexts for each sentence
def generate_contexts(sentences):
    contexts = []

    for i, sentence in enumerate(sentences):
        context = sentence
        remaining_length = 300 - len(sentence)
        remaining_before = remaining_length/2

        # Include preceding sentences
        for j in range(i - 1, -1, -1):
            if remaining_before <= 0:
                break
            context = sentences[j] + " " + context
            remaining_before -= len(sentences[j]) + 1

        remaining_length = remaining_length/2 + remaining_before

        # Include following sentences
        for j in range(i + 1, len(sentences)):
            if remaining_length <= 0:
                break
            context += " " + sentences[j]
            remaining_length -= len(sentences[j]) + 1

        contexts.append(context)

    return contexts

def produce_topics(text: str) -> dict:
    """
    this function takes a text as a string and applies topic analysis, using manifestoberta model
    it returns shares of topics (weighted per sentence) as a dictionary, with topics as key
    """
    sentences = extract_sentences(text)
    contexts = generate_contexts(sentences)
    topics = []
    results = pd.DataFrame()
    for i, sent in enumerate(sentences):
        context = contexts[i]
        probabilities, predicted_class = predict_manifestoberta(sent, context, model, tokenizer)
        probabilities_df = pd.DataFrame({k: [v] for k, v in probabilities.items()})
        results = pd.concat([results, probabilities_df])
        # print(f'sentence: {sent}')
        # print(f'probabilities: {probabilities}')
        # print(f'predicted class: {predicted_class}')
        topics.append(predicted_class)
    # print(Counter(topics))
    topic_shares = results.mean().to_dict()
    return topic_shares

def predict_manifestoberta(sentence, context, model, tokenizer):
    # predicts topics from manifestoberta for a single sentence and its context
    inputs = tokenizer(sentence,
                       context,
                       return_tensors="pt",
                       max_length=300,  #we limited the input to 300 tokens during finetuning
                       padding="max_length",
                       truncation=True)

    logits = model(**inputs).logits

    probabilities = torch.softmax(logits, dim=1).tolist()[0]
    probabilities = {model.config.id2label[index]: round(probability * 100, 2) for index, probability in enumerate(probabilities)}
    probabilities = dict(sorted(probabilities.items(), key=lambda item: item[1], reverse=True))
    # print(probabilities)

    predicted_class = model.config.id2label[logits.argmax().item()]
    # print(predicted_class)
    return probabilities, predicted_class

if __name__ == "__main__":
    # whether to rerun topic analysis for subjects with already existing topics
    rerun = False

    # initialize model
    # use manifestoberta model
    model = AutoModelForSequenceClassification.from_pretrained(
        "manifesto-project/manifestoberta-xlm-roberta-56policy-topics-context-2023-1-1", trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-large")

    df = pd.read_csv(leaflets_path)
    results = pd.DataFrame()

    # list the subjects that are already there
    already_there = pd.read_csv(topics_path)['id'].to_list()
    for index, row in df.iterrows():
        if row['id'] in already_there and not rerun:
            print(f'subject {row["id"]} is already there, skipping')
            continue
        topic_shares = produce_topics(row['summary'])
        print(f'results for {row["name"]}: {topic_shares}')
        topic_shares['id'] = row['id']
        topic_shares_df = pd.DataFrame([topic_shares])
        results = pd.concat([results, topic_shares_df], ignore_index=True)
    already_there = pd.read_csv(topics_path)
    results = pd.concat([already_there, results], ignore_index=True)
    results.to_csv(topics_path)

