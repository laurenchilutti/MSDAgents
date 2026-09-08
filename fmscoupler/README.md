Steps for running fmscoupler chatbot on AMD dev box

Ollama is already running on AMD; as long as you do not change tyhe OLLAMA_CHAT_MODEL in fmscoupler/chatbot.py, the model is already pulled and you do not need to do any Ollama setup.

1. Configure your environemnt

module load miniforge
conda create -n msdagents python=3.12 pip
conda activate msdagents
pip install -e .

2. Create the Database

First, you need to have Milvus started:

cd MSDAgents
mkdir -p $(pwd)/volumes/milvus
./start_milvus_service.sh

Then, you can create the database:

cd fmscoupler
python create_database.py

3. Run the Chatbot

python chatbot.py
