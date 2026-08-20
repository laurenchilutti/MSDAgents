from abc import ABC, abstractmethod
from pprint import pformat

from pymilvus import DataType, Function, FunctionType, MilvusClient
from shared.embeddings import (
    EmbeddingClass, 
    TokenizerClass,
    SentenceTransformerEmbedding,
    SentenceTransformerTokenizer
)
from shared.metadata import (
    schema_metadata_fields, 
    schema_vector_fields,
    indexes,
    sparse_vector_search_function,
    CollectionData
)

class ClientClass(ABC):

    @abstractmethod
    def connect(self):
        pass

class RetrieverClass(ABC):

    @abstractmethod
    def retrieve(self, query: str):
        pass


class Client(ClientClass):

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

        self.client = None

        if connect:
            self.connect()
        

    def connect(self):

        """
        Connect to Milvus
        """

        self.client = MilvusClient(uri=self.uri)  
        print(f"Connected to Milvus at {self.uri}")
        print(f"Collections found: {self.client.list_collections()}")

class newCollection(Client):

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
        super().__init__(collection_name=collection_name, milvus_host=milvus_host, milvus_port=milvus_port,
                         connect=connect, schema=schema, index_params=index_params, embedding=embedding, tokenizer=tokenizer)
        
    def create_schema(self):
        
        """
        Create default schema in accordance to shared/metadata
        """

        self.schema = self.client.create_schema(enable_dynamic_field=True)

        for field_name, field_info in schema_metadata_fields.items():
            self.schema.add_field(**field_info)

        for field_name, field_info in schema_vector_fields.items():
            self.schema.add_field(**field_info)        
        
        self.schema.add_function(sparse_vector_search_function)


    def add_index(self):

        """
        Add index to the collection
        """
        
        self.index_params = self.client.prepare_index_params()
        for index, index_info in indexes.items():
            self.index_params.add_index(**index_info)


    def create_collection(self):
        
        """
        Create collection
        If collection exists, overwrite
        """
        
        if self.client.has_collection(self.collection_name):
            self.client.drop_collection(self.collection_name)

        if self.schema is None: self.create_schema()
        if self.index_params is None: self.add_index()
        
        self.client.create_collection(
            collection_name=self.collection_name, 
            schema=self.schema,
            index_params=self.index_params
        )


    def add_data(self, data: list = None):

        """
        Add data to collection
        """

        for i, datum in enumerate(data, start=1):
            data_dict = datum.dict()
            print(i, data_dict["name"], data_dict["sourcefile"], data_dict["ichunk"], data_dict["chunks"])
            data_dict["dense_vector"] = self.embedding.encode(data_dict["text"])
            
        self.client.insert(self.collection_name, data=data_dict)
        
    
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
                f.write(f"ntokens:    {len(self.tokenizer.tokenize(row['text']))}\n")
                for schema_key in schema_metadata_fields:
                    f.write(f"{schema_key}: {row[schema_key]}\n")

        return data

    
class MilvusRetriever():

    def __init__(self, client: Client):
        self.client = client
        self.retrieve_limit = 10
        self.retrieve = self.simple_retrieve
        
    def simple_retrieve(self, query: str):

        embedded_query = self.client.embedding.encode(query)
        returned_fields = self.client.client.search(
            self.client.collection_name,
            data = [embedded_query],
            anns_field = "dense_vector",
            limit = self.retrieve_limit,
            output_fields=["*"],
        )
        data = []
        for returned_field in returned_fields[0]:
            collection = CollectionData(
                **{schema_key: returned_field[schema_key] for schema_key in schema_metadata_fields}
            )
            data.append(collection)

        return data
