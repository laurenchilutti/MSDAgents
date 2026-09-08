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

Then you need to make sure that you use MiKyung's branch and you need to load compilers and run a preprocessor

(I put this all in a script that gets run after cloning FMS and before running doxygen in the create_fms_database.py script)
source /home/Lauren.Chilutti/Lauren_ifx.sh
autoreconf -if
./configure
make preprocess

Then, you can create the database:

cd fms
python create_fms_database.py

3. Run the Chatbot

python chatbot.py
