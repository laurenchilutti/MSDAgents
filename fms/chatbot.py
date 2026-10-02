import logging

# Suppress gRPC debug logs (too_many_pings warnings)
logging.getLogger("grpc").setLevel(logging.WARNING)

#needed for autoeval
from pathlib import Path
from typing import Dict
import yaml
import json
import argparse

from shared.chatbot import RAGChatbot
from shared.client import Client, MilvusRetriever

#needed for autoeval
parser = argparse.ArgumentParser(description="fms chatbot")
parser.add_argument("-t", "--test", action="store_true", help="Enable chatbot in test mode for auto evaluation")
args = parser.parse_args()

LLM_MODEL = "llama3.2"
COLLECTION_NAME = "FMS"

SYSTEM_MESSAGE = (
  "FMS is the Flexible Modeling System, a Fortran library used for scientific computing in climate simulations. "
  "You are an FMS coding assistant to answer questions about FMS routines and modules. "
  "Only answer questions using the retrieved context. "
  "If context is insufficient, say you do not have enough information from the indexed FMS docs. "
  "Ensure that any code examples you provide are valid Fortran code. "
  "FMS contains many interfaces to provide generic interfaces to different data types, "
  "which should be used instead of calling their routines directly. "
  "If a routine belongs to a generic interface, provide the name of the generic interface in your answer first. "
  "\n\nContext:\n{context}"
)


client = Client(COLLECTION_NAME)
retriever = MilvusRetriever(client)

chatbot = RAGChatbot(
    retriever=retriever,
    system_message=SYSTEM_MESSAGE,
    model_name=LLM_MODEL,
)

#needed for autoeval
if args.test:
    BASELINE_FILE = Path("fms_groundtruth.yaml")
    #$ Parse the BASELINE_FILE yaml and store as a dictionary called groundtruth_yaml
    with BASELINE_FILE.open("r", encoding="utf-8") as f:
        groundtruth_yaml: Dict[str, str] = yaml.safe_load(f)

    #needed for lauren's logger
    OUTPUT_FILE = Path("fms_chatbot.yaml")
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
            print(f"YAML Parsing Error for query '{user_question}': {e}")
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
