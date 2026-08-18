from pprint import pformat

from pymilvus import DataType, Function, FunctionType, MilvusClient
from embeddings import (
    EmbeddingClass, 
    TokenizerClass,
    SentenceTransformerEmbedding,
    SentenceTransformerTokenizer
)

class Client():

    def __init__(self, 
                 collection_name: str, 
                 milvus_host: str="localhost", 
                 milvus_port: int = 19530,
                 connect: bool = True,
                 schema = None,
                 index_params = None,
                 embedding: EmbeddingClass = SentenceTransformerEmbedding(),
                 tokenizer: TokenizerClass = SentenceTransformerTokenizer()
                 
    ):

        self.collection_name = collection_name
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.uri = f"http://{self.milvus_host}:{self.milvus_port}"

        self.schema = schema
        self.index_params = index_params
        self.collection = None

        self.embedding = embedding
        self.tokenizer = tokenizer

        if connect:
            self.connect()
        

    def connect(self):

        """
        Connect to Milvus
        """

        self.client = MilvusClient(uri=self.uri)  
        print(f"Connected to Milvus at {self.uri}")
        print(f"Collections found: {self.client.list_collections()}")

        
    def create_default_schema(self):
        
        """
        Create default schema in accordance to shared/metadata
        """

        self.schema = self.client.create_schema(enable_dynamic_field=True)
        self.schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
        self.schema.add_field(field_name="name", datatype=DataType.VARCHAR, max_length=65535)
        self.schema.add_field(field_name="text", datatype=DataType.VARCHAR, enable_analyzer=True, max_length=65535)
        self.schema.add_field(field_name="sourcefile", datatype=DataType.VARCHAR, max_length=65535)
        self.schema.add_field(field_name="is_chunked", datatype=DataType.BOOL)
        self.schema.add_field(field_name="ichunk", datatype=DataType.INT32)
        self.schema.add_field(field_name="chunks", datatype=DataType.ARRAY, element_type=DataType.INT32, max_capacity=20)
        self.schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=384) #default
        self.schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)
        
        bm25 = Function(
            name="text_bm25_emb", 
            function_type=FunctionType.BM25,
            input_field_names=["text"],
            output_field_names=["sparse_vector"]
        )
        
        self.schema.add_function(bm25)


    def add_default_index(self):

        """
        Add default index
        """
        
        self.index_params = self.client.prepare_index_params()
        self.index_params.add_index(field_name="dense_vector", index_type="AUTOINDEX", metric_type="COSINE")
        self.index_params.add_index(field_name="sparse_vector", index_type="SPARSE_INVERTED_INDEX", metric_type="BM25")


    def create_collection(self):
        
        """
        Create collection
        If collection exists, overwrite
        """
        
        if self.client.has_collection(self.collection_name):
            self.client.drop_collection(self.collection_name)

        if self.schema is None: self.create_default_schema()
        if self.index_params is None: self.add_default_index()
        
        self.client.create_collection(
            collection_name=self.collection_name, 
            schema=self.schema,
            index_params=self.index_params
        )


    def add_data(self, data: list = None):

        """
        Add data to collection
        """

        for datum in data:
            print(datum.name)
            datum.dense_vector = self.embedding.encode(datum.text)
            
        self.client.insert(self.collection_name, data=[datum.model_dump() for datum in data])
        
    
    def test_collection(self, logfile: str = None):

        if self.client.has_collection(self.collection_name):
            self.client.load_collection(self.collection_name)
        else:
            raise RuntimeError(f"Collection '{self.collection_name}' does not exist.")

        if logfile is None:
            logfile = f"{self.collection_name}.log"

        data = []
        batch_size = 1000

        # Use query_iterator to stream all rows without manual offset paging.
        iterator = self.client.query_iterator(
            collection_name=self.collection_name,
            batch_size=batch_size,
            limit=-1,
            filter="id >= 0",
            output_fields=["*"],
        )

        while True:
            rows = iterator.next()
            if not rows:
                iterator.close()
                break
            data.extend(rows)

        with open(logfile, "w", encoding="utf-8") as f:
            f.write(f"Collection: {self.collection_name}\n")
            f.write(pformat(self.client.describe_collection(self.collection_name)))
            f.write("\n *** \n\n")
            for row in data:
                f.write(f"name:       {row['name']}\n")
                f.write(f"id:         {row['id']}\n")
                f.write(f"sourcefile: {row['sourcefile']}\n")
                f.write(f"is_chunked: {row['is_chunked']}\n")
                f.write(f"ichunk:     {row['ichunk']}\n")
                f.write(f"chunks:     {row['chunks']}\n")
                f.write(f"ntokens:    {len(self.tokenizer.tokenize(row['text']))}\n")
                f.write(f"text:\n{row['text']}\n\n")

        return data     
            

if __name__ == "__main__":
    client = Client(collection_name="FMSCoupler")
    client.connect()
    client.drop_collection()
    client.create_collection()
    print(client.list_collections())

    
