import openai
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.core import SimpleDirectoryReader
from app_secrets import gpt_4t_azure_endpoint, gpt_4t_azure_api_key, gpt_4t_model, gpt_4t_azure_api_version
from prompt import check_toc_in_text, extract_toc_form_text, check_signature_page, extract_signature_page


client = openai.AzureOpenAI(
    api_version= gpt_4t_azure_api_version,
    api_key=gpt_4t_azure_api_key,
    base_url= gpt_4t_azure_endpoint
)

def get_completion(messages=None,
                   temperature=0, max_tokens=4000, top_p=1, frequency_penalty=0,
                   presence_penalty=0, stop=None):

    messages = messages or []
    
    # Make API call with provided parameters
    response = client.chat.completions.create(
        # engine=gpt_4t_model,
        messages= messages,
        model=gpt_4t_model,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stop=stop
    )
    content = response.choices[0].message.content
    return content



def find_signature_page_range(documents):  
    """  
    Finds the starting and ending index of documents containing a signature page, typically at the end of the documents list.  
  
    :param documents: A list of Document objects.  
    :return: A list with the starting and ending index of the signature pages,   
             or an empty list if no signature pages are found.  
    """  
    # Initialize the starting and ending indices  
    start_index = None  
    end_index = None  
  
    # Iterate over the documents in reverse to find the range of signature pages  
    for index in reversed(range(len(documents))):  
        document = documents[index]  
          
        # Extract the document text  
        document_text = document.text  
        # Create a user object with the role and content to be analyzed  
        user = {  
            "role": "user",  
            "content": f"document text:\n```\n{document_text}\n```\n---\nNow return True if the signature page is identified else return False."  
        }  
        # Assuming 'check_signature_page' is a list that collects user objects for processing  
        message = check_signature_page
        message.append(user)  
          
        # Assuming 'get_completion' is a function that processes the 'check_signature_page' list and returns 'True' or 'False'  
        has_signature_page = get_completion(messages=message)  
          
        # Cast the result to boolean  
        has_signature_page = True if has_signature_page.lower() == "true" else False  
  
        # If a signature page is found and end_index is not set, set end_index  
        if has_signature_page and end_index is None:  
            end_index = index  
  
        # If a signature page is found and end_index is set, update start_index  
        if has_signature_page and end_index is not None:  
            start_index = index  
  
        # If we already found a signature page and the current document does not have one, break the loop  
        if end_index is not None and not has_signature_page:  
            break  
  
    # If we found a signature page, return the starting and ending indices  
    if start_index is not None:  
        return [start_index, end_index]  
  
    # If no signature pages are found, return an empty list  
    return []  
  

def extract_signature_page_data(document_path):  
    # Load the document data from the given path  
    documents = SimpleDirectoryReader(document_path).load_data()  
    signature_range = find_signature_page_range(documents)  
  
    # Check if a signature range was found  
    if not signature_range or len(signature_range) != 2:  
        raise ValueError("No signature page range found or range is invalid.")  
  
    # Extract the text of the signature pages  
    signature_text = '\n'.join(doc.text for doc in documents[signature_range[0]:signature_range[1] + 1])  
  
    # Format the extracted text for further processing  
    user_signature = {  
        "role": "user",  
        "content": f"Signature Page Data:\n```\n{signature_text}\n```\n---\n\nUsing this Signature Page data, your task is to extract and return well formatted signature section."
    }
  
    message = extract_signature_page  # Assuming this is the list that we will append our user_signature object to  
    message.append(user_signature)  
  
    # Generate the extracted signature data  
    extracted_data = get_completion(messages=message)  
  
    # Write the extracted signature data to `extracted_data.txt`  
    with open('extracted_data.txt', 'w') as file:  
        file.write(f"Signature Page:\n{extracted_data}\n")  
  
    # Return the extracted data and the signature page range  
    return extracted_data, signature_range  



def find_table_of_contents_range(documents):  
    """  
    Finds the starting and ending index of documents containing a table of contents.  
      
    :param documents: A list of Document objects.  
    :return: A list with the starting and ending index, or an empty list if no table of contents is found.  
    """  
    # Initialize the starting and ending indices  
    start_index = None  
    end_index = None  
  
    # Iterate over the documents to find the range of table of contents  
    for index, document in enumerate(documents):  
        # Check if the document has a table of contents

        document_text = document.text
        user = {"role":"user","content":f"document text:\n```\n{document_text}\n```\n---\nNow return True if the table of content is identified else return False."}
        message = check_toc_in_text
        message.append(user)
        has_toc = get_completion(message)
        print(has_toc)

        has_toc = True if has_toc.lower() == "true" else False
          
        # If a table of contents is found and start_index is not set, set start_index  
        if has_toc and start_index is None:  
            start_index = index  
          
        # If a table of contents is found and start_index is set, update end_index  
        if has_toc and start_index is not None:  
            end_index = index  
          
        # If we already found a table of contents and the current document does not have one, break the loop  
        if start_index is not None and not has_toc:  
            break  
  
    # If we found a table of contents, return the starting and ending indices  
    if start_index is not None:  
        return [start_index, end_index]  
      
    # If no table of contents is found, return an empty list  
    return []  




def extract_document_schema(document_path):  
    # Load the document data from the given path  
    documents = SimpleDirectoryReader(document_path).load_data()  
    toc_range = find_table_of_contents_range(documents)
  
    # Extract the text of the table of contents  
    document_toc_text = documents[toc_range[0]:toc_range[1]]  
  
    # Format the extracted text for further processing  
    user_toc = {  
        "role": "user",  
        "content": f"Table of Content of Note Purchase and Guarantee Agreement:\n```\n{document_toc_text}\n```\n---\n\nUsing this Table of content, your task is to return a Json object that shows schema of document."  
    }  
  
    extract_toc_form_text.append(user_toc)  
  
    # Generate the document schema  
    document_schema = get_completion(extract_toc_form_text)  
  
    # Write the document schema to `document_schema.txt`  
    with open('document_schema.txt', 'w') as file:  
        file.write(document_schema)  
    # data = {"document_schema": document_schema, "toc_range": toc_range}

    # Return the document schema as a string  
    return document_schema, toc_range
    # return data