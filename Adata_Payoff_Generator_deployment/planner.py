from app_secrets import gpt_4t_azure_endpoint, gpt_4t_azure_api_key, gpt_4t_model, gpt_4t_azure_api_version  
import openai  
from prompt import planner_system_prompt, query_transformation_system_prompt
import copy
import re

# Initialize the OpenAI client with Azure configurations  
client = openai.AzureOpenAI(  
    api_version=gpt_4t_azure_api_version,  
    api_key=gpt_4t_azure_api_key,  
    base_url=gpt_4t_azure_endpoint  
)  
  
# def get_completion(messages=None,  
#                    temperature=0, max_tokens=4000, top_p=1, frequency_penalty=0,  
#                    presence_penalty=0, stop=None):  
#     """Get completion from OpenAI API."""  
#     messages = messages or []  
#     response = client.chat.completions.create(  
#         model=gpt_4t_model,  
#         messages=messages,  
#         temperature=temperature,  
#         max_tokens=max_tokens,  
#         top_p=top_p,  
#         frequency_penalty=frequency_penalty,  
#         presence_penalty=presence_penalty,  
#         stop=stop  
#     )  
#     content = response.choices[0].message.content  
#     return content  


import time  
import random  
  
# Assuming 'client' is already defined and properly initialized  
# You will also need to properly handle or import the 'gpt_4t_model'  
  
def get_completion(messages=None,    
                   temperature=0, max_tokens=4000, top_p=1, frequency_penalty=0,    
                   presence_penalty=0, stop=None):    
    """Get completion from OpenAI API with a backoff loop for retries."""  
    messages = messages or []  
    max_retries = 5  # Define the maximum number of retries  
    backoff_factor = 1.5  # Define the backoff factor to increase wait time  
    retry = 0  # Initial retry count  
      
    while True:  
        try:  
            response = client.chat.completions.create(    
                model=gpt_4t_model,    
                messages=messages,    
                temperature=temperature,    
                max_tokens=max_tokens,    
                top_p=top_p,    
                frequency_penalty=frequency_penalty,    
                presence_penalty=presence_penalty,    
                stop=stop    
            )    
            content = response.choices[0].message.content    
            return content    
  
        except Exception as e:  # Catching any exception  
            if retry < max_retries:  
                wait_time = backoff_factor * (2 ** retry)  
                # Optional: add randomness to the wait time  
                wait_time += random.uniform(0, 0.1 * wait_time)  
                print(f"Request failed with error {e}. Retrying in {wait_time} seconds...")  
                time.sleep(wait_time)  
                retry += 1  
            else:  
                print(f"Max retries reached. Last error: {e}")  
                raise  

  

def parse_expression(expression):
    stack = []
    current = {}
    for token in re.findall(r'Step \d+|AND|OR|\(|\)', expression):
        if token.startswith('Step'):
            if 'steps' not in current:
                current['steps'] = []
            current['steps'].append(int(token.split()[1]))
        elif token in ('AND', 'OR'):
            current['logic'] = token
        elif token == '(':
            stack.append(current)
            current = {}
        elif token == ')':
            closed = current
            current = stack.pop()
            if 'steps' not in current:
                current['steps'] = []
            current['steps'].append(closed)
    return current



def fetch_args(args_lookup, logic_exp):
    out = copy.deepcopy(logic_exp)
    assert 'steps' in logic_exp.keys()
    for s, step in enumerate(logic_exp['steps']):
        if isinstance(step, int):
            out['steps'][s] = args_lookup[step]
        elif isinstance(step, dict):
            out['steps'][s] = fetch_args(args_lookup, step)
    return out



def plan_to_args(plan, keyword = 'Step', lkey = 'execution order'):
    args = []
    lines = plan.split('\n')
    for line in lines:
        if line.startswith(keyword): args.append(re.sub(r'{} \d+: '.format(keyword), '', line))
        if lkey in line.lower():
            logic = line.split(': ')[-1]
    args_lookup = {i+1: args[i] for i in range(len(args))}
    try:
        return fetch_args(args_lookup, parse_expression(logic))
    except: 
        return {'steps': args, 'logic': 'AND'}


def planner(query_list):  
    """Generate an abstract plan for the provided user query."""  
    user_prompt = {
		"role": "user",
		"content": f"Given user query list for a Note Purchase and Guarantee Agreement document:  \n```  \n{query_list}\n``` \n\nCome up with an abstract plan to perform this task in a couple of steps. The agent can only execute one query at a time.  \nEnsure each step can be understood independently and mentions the specific action to be taken.  \nWhen stating the execution order, ensure that 'AND'/'OR' statements are properly nested using brackets '()' .\nAnd please follow the Think-Step format while generating a plan."
	}
 
  
    planner_system_prompt.append(user_prompt)  
      
    plan = get_completion(messages=planner_system_prompt)  
    # print(plan)
    
  
    return plan_to_args(plan)


def get_extracted_data(file_path = 'document_schema.txt'):
    
    # Initialize a variable to store the text  
    file_text = ''  
    
    # Open the text file and read its contents  
    try:  
        # with open(file_path, 'r', encoding='utf-8') as file:  
        with open(file_path, 'r') as file:  
            file_text = file.read()
        return file_text  
    except FileNotFoundError:  
        print(f"The file at {file_path} was not found.")  
    except Exception as e:  
        print(f"An error occurred while reading the file: {e}")



def step_decomposer(failed_step, n=3):
    schema = get_extracted_data()
    query_transformation_user_prompt = 		{
		"role": "user",
		"content": f"You are an advanced assistant designed to create distinct and optimized search queries within a structured document. When provided with a user's query, the schema of the document (Table of Contents), and a parameter 'n' indicating the number of unique transformed queries required, your task is to generate 'n' different queries. Each transformed query must include a relevant section name from the document's schema, identified through a similarity search in the vector store of the document's content.  \n  \nEach new query should be unique, targeting a different part of the document or a different aspect of the user's initial query to ensure a comprehensive search that covers various potential answers.  \n  \nHere is the document schema (Table of Contents) to guide your query transformations:  \n{schema}  \n  \nPlease generate {n} distinct transformed queries in the following format for the given input query:  \nInput Query: {failed_step}  \n  \nTransformed Queries:  \nStep 1: transformed_query_1  \nStep 2: transformed_query_2  \nStep 3: transformed_query_3  \n...  \nStep n: transformed_query_n  \n  \nEnsure that each transformed query is different from the others to enable a broad and effective similarity search within the document.  \n  \nPlease structure the execution order as follows:  \nexecution order: (Step 1 OR Step 2 OR Step 3 OR ... Step n-1 OR Step n)  \n  \nNote: Only generate the transformed queries as specified above without any additional conversational text.  "
	}

    query_transformation_system_prompt.append(query_transformation_user_prompt)
      
    plan = get_completion(messages=query_transformation_system_prompt)  
    # print(plan)
    # print(plan_to_args(plan))
  
    return plan_to_args(plan)




