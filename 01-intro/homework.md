## Homework: Introduction

In this homework, we'll learn more about search and use Elastic Search for practice. 

> It's possible that your answers won't match exactly. If it's the case, select the closest one.


## Q1. Running Elastic 

Run Elastic Search 8.17.6, and get the cluster information. If you run it on localhost, this is how you do it:
```css
[Запрос пользователя]
        ↓
[Поиск в Elasticsearch (по вектору или ключевым словам)]
        ↓
[Находятся релевантные документы]
        ↓
[LLM использует их как контекст]
        ↓
[Генерируется осмысленный и точный ответ]
```

```bash
curl localhost:9200
```

What's the `version.build_hash` value? : dbcbbbd0bc4924cfeb28929dc05d82d662c527b7

```json
{
  "name" : "MacBook-Pro-2",
  "cluster_name" : "elasticsearch",
  "cluster_uuid" : "YEQ4bsjDT8qOlij-7c_bCQ",
  "version" : {
    "number" : "8.17.6",
    "build_flavor" : "default",
    "build_type" : "tar",
    "build_hash" : "dbcbbbd0bc4924cfeb28929dc05d82d662c527b7",
    "build_date" : "2025-04-30T14:07:12.231372970Z",
    "build_snapshot" : false,
    "lucene_version" : "9.12.0",
    "minimum_wire_compatibility_version" : "7.17.0",
    "minimum_index_compatibility_version" : "7.0.0"
  },
  "tagline" : "You Know, for Search"
}
```


## Getting the data

Now let's get the FAQ data. You can run this snippet:

```python
import requests 

docs_url = 'https://github.com/DataTalksClub/llm-zoomcamp/blob/main/01-intro/documents.json?raw=1'
docs_response = requests.get(docs_url)
documents_raw = docs_response.json()

documents = []

for course in documents_raw:
    course_name = course['course']

    for doc in course['documents']:
        doc['course'] = course_name
        documents.append(doc)
```

Note that you need to have the `requests` library:

```bash
pip install requests
```

## Q2. Indexing the data

Index the data in the same way as was shown in the course videos. Make the `course` field a keyword and the rest should be text. 

Don't forget to install the ElasticSearch client for Python:

```bash
pip install elasticsearch
```

Which function do you use for adding your data to elastic?

* `insert` 
* `index` ✅
* `put`
* `add`

## Q3. Searching

Now let's search in our index. 

We will execute a query "How do execute a command on a Kubernetes pod?". 

Use only `question` and `text` fields and give `question` a boost of 4, and use `"type": "best_fields"`.

What's the score for the top ranking result?

* 84.50
* 64.50
* 44.50 ✅
* 24.50

Look at the `_score` field.

## Q4. Filtering

Now ask a different question: "How do copy a file to a Docker container?".

This time we are only interested in questions from `machine-learning-zoomcamp`.

Return 3 results. What's the 3rd question returned by the search engine?

* How do I debug a docker container?
* How do I copy files from a different folder into docker container’s working directory? ✅
* How do Lambda container images work?
* How can I annotate a graph?

## Q5. Building a prompt

Now we're ready to build a prompt to send to an LLM. 

Take the records returned from Elasticsearch in Q4 and use this template to build the context. Separate context entries by two linebreaks (`\n\n`)
```python
context_template = """
Q: {question}
A: {text}
""".strip()
```

Now use the context you just created along with the "How do I execute a command in a running docker container?" question 
to construct a prompt using the template below:

```
prompt_template = """
You're a course teaching assistant. Answer the QUESTION based on the CONTEXT from the FAQ database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT:
{context}
""".strip()
```

What's the length of the resulting prompt? (use the `len` function)

* 946
* 1446 ✅ but 1462
* 1946
* 2446

## Q6. Tokens

When we use the OpenAI Platform, we're charged by the number of 
tokens we send in our prompt and receive in the response.

The OpenAI python package uses `tiktoken` for tokenization:

```bash
pip install tiktoken
```

Let's calculate the number of tokens in our query: 

```python
encoding = tiktoken.encoding_for_model("gpt-4o")
```

Use the `encode` function. How many tokens does our prompt have?

* 120
* 220
* 320 ✅ but 322
* 420

Note: to decode back a token into a word, you can use the `decode_single_token_bytes` function:

```python
encoding.decode_single_token_bytes(63842)
```

## Bonus: generating the answer (ungraded)

Let's send the prompt to OpenAI. What's the response?  

Note: you can replace OpenAI with Ollama. See module 2.

## Bonus: calculating the costs (ungraded)

Suppose that on average per request we send 150 tokens and receive back 250 tokens.

How much will it cost to run 1000 requests?

You can see the prices [here](https://openai.com/api/pricing/)

On June 17, the prices for gpt4o are:

* Input: $0.005 / 1K tokens
* Output: $0.015 / 1K tokens

You can redo the calculations with the values you got in Q6 and Q7.


## Submit the results

* Submit your results here: https://courses.datatalks.club/llm-zoomcamp-2025/homework/hw1
* It's possible that your answers won't match exactly. If it's the case, select the closest one.
