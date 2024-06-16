import nest_asyncio
from app_secrets import api_key, azure_endpoint, api_version
nest_asyncio.apply()
import os
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core import Settings
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from typing import List
from llama_index.core import SimpleDirectoryReader

from llama_index.core import GPTVectorStoreIndex

from gensim.utils import simple_preprocess  
from gensim import corpora  
from gensim.models.ldamodel import LdaModel  
from nltk.corpus import stopwords  
import nltk  
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.extractors import SummaryExtractor

llm = AzureOpenAI(
    model="gpt-35-turbo-16k",
    deployment_name="DanielChatGPT16k",
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
)

embed_model = AzureOpenAIEmbedding(
    model="text-embedding-3-large",
    deployment_name="text-embedding-3-large",
    api_key="c09f91126e51468d88f57cb83a63ee36",
    azure_endpoint="https://chat-gpt-a1.openai.azure.com/",
    api_version="2023-12-01-preview",
)

Settings.llm = llm
Settings.embed_model = embed_model
Settings.chunk_size = 4096
Settings.chunk_overlap = 256


extractors = [
    SummaryExtractor(summaries=["prev", "self", "next"], llm=llm)
]


import re  
import nltk  
from nltk.corpus import stopwords  
from nltk.tokenize import word_tokenize  
  
# Make sure to download the necessary NLTK data  
nltk.download('stopwords')  
nltk.download('punkt')  
  
def normalize_text(text):  
    # Normalize Text  
    text = re.sub(r'\s+', ' ', text).strip()  
    text = re.sub(r". ,", "", text)  
    text = text.replace(",", "")  
    text = text.replace("..", ".")  
    text = text.replace(". .", ".")  
    text = text.replace('"', "")  
    text = text.replace("'", "")  
    text = text.replace(':', "")  
    text = text.replace(';', "")
    text = text.replace('[', "")
    text = text.replace(']', "")
    text = text.replace('“', "")
    text = text.replace('”', "")
    # text = text.replace("\n", "")
    text = text.strip()
    return text



def preprocess(text, stop_words):
    """
    Tokenizes and preprocesses the input text, removing stopwords and short 
    tokens.

    Parameters:
        text (str): The input text to preprocess.
        stop_words (set): A set of stopwords to be removed from the text.
    Returns:
        list: A list of preprocessed tokens.
    """
    result = []
    for token in simple_preprocess(text, deacc=True):
        if token not in stop_words and len(token) > 3:
            result.append(token)
    return result


def extract_keywords_from_nodes(nodes, num_topics=1, words_per_topic=15):  
    """  
    Extracts keywords from the text of each node using LDA and updates the  
    metadata of the node with the extracted keywords.  
  
    Parameters:  
        nodes (list): A list of nodes, where node.text gives the text chunk.  
        num_topics (int): The number of topics to discover (default 1).  
        words_per_topic (int): The number of words to include per topic (default 15).  
    """  
    nltk.download('stopwords')  
    stop_words = set(stopwords.words('english'))  # Customize this line for different languages as needed  
  
    keys_to_keep = ['window', 'original_text', 'section_summary']
    # Process each node  
    for node in nodes:  
        try:  
            # Preprocess the text in the node  
            processed_text = preprocess(node.text, stop_words)
            if not processed_text:  # If the processed text is empty, continue to the next node  
                print("Processed text is empty. Skipping to the next node.")  
                continue  
  
            metadata = node.metadata  
            keys_to_remove = [  
                key for key in metadata  
                if key not in keys_to_keep or (key in keys_to_keep and not metadata[key])  
            ]  
  
            for key in keys_to_remove:  
                del metadata[key]  

            # Create a dictionary and a corpus for the node's text  
            dictionary = corpora.Dictionary([processed_text])  
            corpus = [dictionary.doc2bow(processed_text)]  
  
            # Build the LDA model  
            lda_model = LdaModel(  
                corpus,  
                num_topics=num_topics,  
                id2word=dictionary,  
                passes=15  
            )  

            # Retrieve the topics and their corresponding words  
            topics = lda_model.print_topics(num_words=words_per_topic)  
  
            # Extract keywords from the topics  
            keywords = []  
            for topic in topics:  
                words = topic[1].split("+")  
                topic_keywords = [word.split("*")[1].replace('"', '').strip() for word in words]  
                keywords.extend(topic_keywords)  
  
            # Update the node metadata with keywords  
            metadata['keywords'] = keywords  
            node.metadata = metadata  
            # print(node.metadata)
            # exit()
  
        except ValueError as e:  
            print(f"An error occurred with node: {node}. Error: {e}")  
            continue  # Skip to the next node  



# create the sentence window node parser w/ default settings
node_parser = SentenceWindowNodeParser.from_defaults(
    window_size=3,
    window_metadata_key="window",
    original_text_metadata_key="original_text",
)

transformations = [
    SummaryExtractor(summaries=["prev", "self"]),
    node_parser
]

from llama_index.core.ingestion import IngestionPipeline

def process_documents(doc_folder: str, storage_base_folder: str, toc_range: list, max_retries: int = 5) -> GPTVectorStoreIndex:  
    # Make sure the storage base directory exists  
    os.makedirs(storage_base_folder, exist_ok=True)  
    Settings.chunk_size = 4096
    Settings.chunk_overlap = 256
  
    retries = 0  
    while retries < max_retries:  
        try:  
            # Process the single document
            docs = SimpleDirectoryReader(doc_folder).load_data()
            # Iterate over each document and update the text attribute  
            
            docs = docs[:toc_range[0]] + docs[toc_range[1]+1:]

            print("Preprocessing Chunks...")

            for doc in docs:  
                # Preprocess the text using the normalize_text function  
                processed_text = normalize_text(doc.text)  
                
                # Update the text attribute of the document with the processed text  
                doc.text = processed_text

            print("Completed Preprocessing")
            # print(docs[5].text)
            

            pipeline = IngestionPipeline(transformations=transformations)
            orig_nodes = pipeline.run(documents=docs)

            extract_keywords_from_nodes(orig_nodes)
            # exit()
  
            # Create the index with a storage context pointing to the storage base folder  
            index = GPTVectorStoreIndex(orig_nodes, show_progress=True)  
            index.storage_context.persist(persist_dir=storage_base_folder)  
  
            return index  # Return the index object directly  
  
        except Exception as e:  
            retries += 1  
            Settings.chunk_size = 5120  
            Settings.chunk_overlap = 420  
  
            print(f"An error occurred: {e}. Retrying ({retries}/{max_retries})")
            if retries >= max_retries:  
                print(f"Maximum retries reached. Unable to process the document.")  
                raise  # Re-raise the exception to indicate failure  
