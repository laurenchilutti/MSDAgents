#needed for autoeval
from pathlib import Path
from typing import Dict
import yaml
import json
import argparse

from shared.chatbot import RAGChatbot
from shared.client import Client, MilvusRetriever

#needed for autoeval
parser = argparse.ArgumentParser(description="fmscoupler chatbot")
parser.add_argument("-t", "--test", action="store_true", help="Enable chatbot in test mode for auto evaluation")
args = parser.parse_args()

OLLAMA_CHAT_MODEL = "mistral-nemo:latest"
COLLECTION_NAME = "FMSCoupler"

system_message = """
You are a technical assistant for the FMSCoupler.  

## Background
FMSCoupler, Flexible Modeling Systems Coupler, is a set of program
and modules to couple the atmosphere, ocean, land, and ice components in the 
GFDL (Geophysical Fluid Dynamics Laboratory) coupled climate models.

## Instructions:
- Use only the supplied context to answer.
- If the context does not contain the answer, say you do not know.
- Answer with a concise explanation.  Do not use markdown formatting.

## Context: 
{context}
"""

client = Client(COLLECTION_NAME)
retriever = MilvusRetriever(client)

chatbot = RAGChatbot(
    retriever=retriever, 
    system_message=system_message,
    model_name=OLLAMA_CHAT_MODEL, 
)

#needed for autoeval
if args.test:
    BASELINE_FILE = Path("fmscoupler_groundtruth.yaml")
    #$ Parse the BASELINE_FILE yaml and store as a dictionary called groundtruth_yaml
    with BASELINE_FILE.open("r", encoding="utf-8") as f:
        groundtruth_yaml: Dict[str, str] = yaml.safe_load(f)

    #needed for lauren's logger
    OUTPUT_FILE = Path("fmscoupler_chatbot.yaml")
    #Dictionary to store logs for lauren
    bot_responses: Dict[str, str]= {}

    for user_question in groundtruth_yaml.keys():
        response, docs_and_scores, context = chatbot.ask(user_question)
        print(f"\nAssistant: {response}")
        print(f"source: {[doc['sourcefile'] for doc in docs_and_scores]}")
        print("\n\n")

        #needed for lauren's logger
        try:
            bot_responses[user_question] = yaml.safe_load(json.dumps(response))
        except yaml.YAMLError as e:
            print(f"YAML Parsing Errror for query '{user_question}': {e}")
            bot_responses[user_question] = response
    # Outside of the LLM loop, aggregate evaluation results
    # This should be replaced by the logger
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        yaml.dump(
            bot_responses,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
else:
    while True:
        user_question = input("\nYou: ").strip()
        if user_question.lower() in {"quit", "exit", "q"}:
            print("Bye.")
            break

        response, docs_and_scores, context = chatbot.ask(user_question)        
        print(f"\nAssistant: {response}")
        print(f"source: {[doc['sourcefile'] for doc in docs_and_scores]}")
        print("\n\n")
