functions_desc = [  
    {  
        "name": "perform_similarity_search",  
        "description": "Finds and extracts information from a document that best matches the transformed query using a similarity search algorithm.",  
        "parameters": {  
            "type": "object",  
            "properties": {  
                "transformed_query": {  
                    "type": "string",  
                    "description": "The refined query augmented with keywords and concepts from a predefined schema to improve the accuracy of the similarity search."  
                }  
            },  
            "required": ["transformed_query"]  
        },  
        "returns": {  
            "type": "string",  
            "description": "The extracted information from the document that corresponds to the transformed query. If no match is found, a response indicating no results will be returned."  
        }  
    },  
    {  
        "name": "update_response",  
        "description": "Appends extracted data to a local file named 'data.txt' to persistently store the results of the data extraction process.",  
        "parameters": {  
            "type": "object",  
            "properties": {  
                "extracted_data": {  
                    "type": "string",  
                    "description": "The information extracted from the similarity search (without conversational text) that needs to be recorded in the file. Ex: 'Sponsor Name: J.H. Whitney Capital Partners, LLC'"  
                }  
            },  
            "required": ["extracted_data"]  
        },  
        "returns": {  
            "type": "string",  
            "description": "A status message indicating the outcome of the file operation. Returns 'Success' if the data was appended without issues, or 'Failed' if an error occurred."  
        }  
    }  
]  