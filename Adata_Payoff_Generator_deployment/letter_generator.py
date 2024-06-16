# from hypergraph import get_semantic_frames
from template import new_payoff_template
from openai import AzureOpenAI
from app_secrets import gpt_4t_azure_endpoint, gpt_4t_azure_api_key, gpt_4t_model, gpt_4t_azure_api_version
import time  
from functools import wraps  



def get_extracted_data(file_path = './extracted_data.txt'):
    
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


client = AzureOpenAI(
    api_version= gpt_4t_azure_api_version,
    api_key=gpt_4t_azure_api_key,
    base_url= gpt_4t_azure_endpoint
)




# def get_completion(messages=None,
#                    temperature=0, max_tokens=4000, top_p=1, frequency_penalty=0,
#                    presence_penalty=0, stop=None):
#     # Set default values if parameters are not provided
#     messages = messages or []
    
#     # Make API call with provided parameters
#     response = client.chat.completions.create(
#         messages= messages,
#         model=gpt_4t_model,
#         temperature=temperature,
#         max_tokens=max_tokens,
#         top_p=top_p,
#         frequency_penalty=frequency_penalty,
#         presence_penalty=presence_penalty,
#         stop=stop
#     )
#     # print(response)
#     content = response.choices[0].message.content
#     return content

import time  
import random  

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


previous_section = ""

prompt_template = """
{previous}

Payoff letter Section to be generated: {section_name}
 
Section template must be followed:   
```  
{section_template}
```  

Information to be used:  
```
{section_info}
```

Now generate the given section using the provided information, only replace the placeholder in square brackets `[]` and try not to leave any placeholder in generated text.
REMEMBER: Only generate the asked section as this will be appended in original Payoff letter, do not generate any text beside the asked section.

"""


  
# Create a decorator to measure the execution time of a function  
def time_it(func):  
    @wraps(func)  
    def wrapper(*args, **kwargs):  
        start_time = time.time()  # Start time  
        result = func(*args, **kwargs)  # Call the decorated function  
        end_time = time.time()  # End time  
        execution_time = end_time - start_time  # Calculate the execution time  
        print(f"{func.__name__} executed in {execution_time:.4f} seconds.")  
        return result  
    return wrapper  




@time_it  
def get_section_generator():  
    global previous_section

    # exit()

    print("response generation completed...")
  
    print("constructing prompt and generating final text...")
    # for section_name, section_details in payoff_details.items():
    for section_name, section_details in new_payoff_template.items():
        section_info = get_extracted_data(file_path = 'extracted_data.txt')
        local_template = prompt_template
        # for info in section_details:
        #     section_info += str(info) + ": " + str(response_dict[info]) + "\n"  
  
        # section_template = payoff_template[str(section_name)]  
        section_template = section_details
  
        # Replace the placeholders with the given arguments  
        filled_template = local_template.format(
            previous = "Previous Section: \n"+ str(previous_section),
            section_name=str(section_name),  
            section_template=str(section_template),  
            section_info=section_info  
        )  
  
        acknowledgement = {"role": "user", "content": "Yes, please generate final result."}  
        messages = [{"role":"system","content":"You are an intelligent assistant with expertise in finance and legal documentation, specifically with a focus on loan agreements and payoff letters. You are to mimic the collaborative efforts of three experts in financial law using the 'Tree of Thoughts' approach. When provided with specific information, section names, and a template for a section of a payoff letter by the user, your task is to generate the corresponding sections of the payoff letter. You must simulate each 'expert' within you, detailing their thought process meticulously, considering the contributions of the others, and acknowledging any oversights. They will collaboratively refine and elaborate on one another's inputs, attributing proper credit to the preceding thoughts. This collaborative and iterative process continues until the requested section is drafted. As the final step, you must synthesize the entire simulated discussion among these 'experts' and produce a polished, precise section of a payoff letter. All user-provided details must be accurately incorporated, and the resulting text should conform to standard financial and legal formats and terminologies, showcasing the exceptional drafting skills of the three simulated 'experts'."},{"role":"user","content":"Payoff letter Section to be generated: Header Information  \n   \nSection template must be followed:     \n```    \nDate: [Date]    \n     \n[Issuer/Borrower Company Name]    \n[Issuer/Borrower Address Line 1]    \n[Issuer/Borrower Address Line 2]    \n[City, State, Zip Code]    \nAttn: [Issuer/Borrower Attention Name]    \n     \n[Holder/Lender/Agent Company Name]    \n[Holder/Lender/Agent Address Line 1]    \n[Holder/Lender/Agent Address Line 2]    \n[City, State, Zip Code]    \nAttn: [Holder/Lender/Agent Attention Name]    \n```    \n  \nInformation to be used:    \n```  \n[Issuer/Borrower Company Name]: MNX Intermediate Holding Corp.  \n[Issuer/Borrower Address Line 1 & 2]: New York, NY 10005  \n[City, State, Zip Code]: Chicago, Illinois 60603  \n[Attn]: Vikash Sahni  \n[Holder/Lender/Agent Company Name]: Northwestern Mutual Life Insurance Company  \n[Holder/Lender/Agent Address Line 1 & 2]: 1301 Avenue of the Americas, 34th Floor, New York, NY 10019  \n&nbsp;  \n```  \n&nbsp;  \nNow generate the given section using the provided information."},{"role":"assistant","content":"Expert 1:   \n  \nThe first step in drafting the Header Information section of the payoff letter is to insert the provided details into the given template. The date will be the current date, which can be represented as \"[Date]\". Then, we replace the template placeholders with the provided information. The \"[Issuer/Borrower Company Name]\" is \"MNX Intermediate Holding Corp.\" and their address is \"New York, NY 10005\", with attention to \"Vikash Sahni\". The \"[Holder/Lender/Agent Company Name]\" is \"Northwestern Mutual Life Insurance Company\", and their address is \"1301 Avenue of the Americas, 34th Floor, New York, NY 10019\".   \n  \nExpert 2:  \n   \nGood start, Expert 1. However, I noticed that there might be a misunderstanding with the issuer/borrower's address. The provided \"[Issuer/Borrower Address Line 1 & 2]\" and \"[City, State, Zip Code]\" seem to be conflicting. The address appears to be \"New York, NY 10005\", but the city, state, and zip code are \"Chicago, Illinois 60603\". We need to clarify this.  \n   \nExpert 3:  \n   \nNice catch, Expert 2. It seems there was a mistake in the provided information. For the sake of this exercise, let's assume that the issuer/borrower's address is in New York, and the city, state, and zip code are \"Chicago, Illinois 60603\" are for the Holder/Lender/Agent.   \n  \nWith these corrections, the header should be:  \n   \n```    \nDate: [Date]    \n  \nMNX Intermediate Holding Corp.  \nNew York, NY 10005    \nAttn: Vikash Sahni    \n  \nNorthwestern Mutual Life Insurance Company    \n1301 Avenue of the Americas, 34th Floor    \nChicago, Illinois 60603    \nAttn: [Holder/Lender/Agent Attention Name]    \n```    \n  \nExpert 1:  \n   \nGreat teamwork, Expert 2 and Expert 3. The \"[Holder/Lender/Agent Attention Name]\" placeholder is missing. As we don't have a specific person to address at the Northwestern Mutual Life Insurance Company, we can address it to the Loan Department or similar.  \n\nAsk user for final generation:\nCan we compile the Final Header?"},{"role":"user","content":"Yes, please generate final result."},{"role":"assistant","content":"Date: []    \n  \nMNX Intermediate Holding Corp.  \nNew York, NY 10005    \nAttn: Vikash Sahni    \n  \nNorthwestern Mutual Life Insurance Company    \n1301 Avenue of the Americas, 34th Floor    \nChicago, Illinois 60603    \nAttn: Loan Department    \n"}]
        messages.append({"role": "user", "content": filled_template})  
  
        print("generating response...")  
        response1 = get_completion(messages=messages)  
  
        messages.append({"role": "assistant", "content": response1})
        messages.append(acknowledgement)  
  
        response2 = get_completion(messages=messages)
        previous_section = response2

        # print(response2)
  
        yield response2  # Yield the response instead of writing to a file  
  


# for section in get_section_generator():
#     with open('Adapt_verified_Gastro_payoff_letter.txt', 'a') as file:  
#         file.write(f"{section}\n\n")