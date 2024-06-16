import os    
import streamlit as st
import time
from pathlib import Path
from SchemaExtractor.schema_extractor import extract_document_schema, extract_signature_page_data
from metadata_extract_and_index.LDA_metadata_extract import process_documents
from controller import controller, log_to_file
from planner import planner
from letter_generator import get_section_generator, get_extracted_data
from executor import setup_environment

DOC_PATH = "./documents"
VECTOR_STORE_PATH = "./vector_store"

def save_uploaded_file(uploaded_file, target_dir):  
    """Save the uploaded file to the target directory."""  
    try:  
        # Create the target directory if it doesn't already exist  
        os.makedirs(target_dir, exist_ok=True)  
          
        # Construct the full path to save the file  
        file_path = os.path.join(target_dir, uploaded_file.name)  
          
        # Write the uploaded file to the file system  
        with open(file_path, "wb") as f:  
            f.write(uploaded_file.getbuffer())  
        return True  
    except Exception as e:  
        print(e)  
        return False  

def clear_files():  
    # Define the list of files to clear within the function  
    files_to_clear = [  
        'extracted_data.txt',  
        'Adapt_verified_payoff_letter.txt',  
        'document_schema.txt'  
    ]  
  
    for file_name in files_to_clear:  
        try:  
            # Open the file in write mode to clear its contents  
            with open(file_name, 'w'):  
                pass  # No need to write anything; opening in 'w' mode clears the file  
            print(f"File {file_name} has been cleared.")  
        except Exception as e:  
            print(f"An error occurred while clearing {file_name}: {e}")  
  
import os  
  
def remove_files():  
    folders_to_remove = ["documents"]  
  
    for folder_name in folders_to_remove:  
        target_folder = os.path.join(os.getcwd(), folder_name)  
          
        if os.path.exists(target_folder):  
            for root, dirs, files in os.walk(target_folder):  
                for file_name in files:  
                    file_path = os.path.join(root, file_name)  
                    os.remove(file_path)  
                for dir_name in dirs:  
                    dir_path = os.path.join(root, dir_name)  
                    os.rmdir(dir_path)  
  



# User query and plan structure  
query_list = ["Extract Date of 'Agreement'",  
"Extract name of (the 'Initial Issuer')",  
"Extract name of (the 'Surviving Issuer')",  
"Extract name of (the 'Holdings') entity",  
"[Sponsor Name]",
"[The Sponsor address with the attention of person name] (From Notices section)",  
"[The Obligor address with the attention of person name] (From Notices section)",
"Extract date of Maturity or temination date",
"Extract section number of Expenses; Indemnification; Limitation of Liability section?",  
"Extract Governing Law section",  
"Extract date of Maturity from Authorization of Notes section",  
"Extract section number of Optional Prepayments section.",
"Extract the specific time by which funds must be credited on the due date.",
"Identify the location that is relevant to the timing of the wire transfer."]  


# Title  
st.title('Payoff Letter Generator')  
  
# Subtitle  
st.markdown('Powered by Adapt+') 

from datetime import datetime  

# Get the current date  
formatted_date = datetime.now()  
  
# Format the date  
current_date = formatted_date.strftime("%B %d, %Y")  


# Date input for payoff date with the accepted format 'MM/DD/YYYY'  
default_date = datetime.strptime('November 30, 2022', '%B %d, %Y')  
payoff_date = st.date_input(  
    "Payoff Date",  
    value=default_date,  
    format='MM/DD/YYYY'  
)

# Single file uploader that allows multiple files    
uploaded_files = st.file_uploader("Upload documents", accept_multiple_files=True, disabled=False)    
    
# Submit button for the form    
submit_button = st.button(label='Upload Documents', disabled=False)    
    
# If the user submits the form    
if submit_button and uploaded_files:  
    print("Cleaning the files...")
    clear_files()
    remove_files()

    # Display a generating message  
    with st.spinner('Saving uploaded documents...'):  
        success = False  
        for uploaded_file in uploaded_files:  
            saved = save_uploaded_file(uploaded_file, "documents")
            success = success or saved  # If at least one file is saved successfully, success will be True  
          
        # If any document was saved successfully, show success message    
        if success:  
            st.success('Documents uploaded successfully!')

        else:  
            st.error('No documents to upload. Please upload at least one document.')

else:  
    if submit_button:  # If the button was clicked but no files were uploaded  
        st.error('No documents to upload. Please upload at least one document.')
        
import executor

if st.button(label="Generate"):
    st.write("Payoff Letter generation will take time please wait...")

    st.write("extracting document Schema...")

    start_time = time.time()
    doc_schema, toc_range = extract_document_schema(DOC_PATH)
    end_time = time.time()

    execution_time = end_time - start_time
    print(f"extract_document_schema executed in {execution_time:.4f} seconds.")
    st.write(f"extract_document_schema executed in {execution_time:.4f} seconds.")

    st.write("extracting Signature Page data...")

    start_time = time.time()
    spd , spd_range = extract_signature_page_data(DOC_PATH)
    end_time = time.time()

    execution_time = end_time - start_time
    print(f"extract_signature_page_data executed in {execution_time:.4f} seconds.")
    st.write(f"extract_signature_page_data executed in {execution_time:.4f} seconds.")
    
    with open("extracted_data.txt", "a") as file:
        current_date = f"\nQ: Current date?\nA: {current_date}\n"
        data = f"\nQ: Payoff date ?\nA: The payoff date is {payoff_date}\n"
        file.write(data)

    # toc_range = [1,5]
    st.write("extracting metadata and creating vector index...")
    start_time = time.time()
    process_documents(doc_folder=DOC_PATH, storage_base_folder= VECTOR_STORE_PATH, toc_range= toc_range)
    end_time = time.time()

    execution_time = end_time - start_time
    print(f"process_documents executed in {execution_time:.4f} seconds.")
    st.write(f"process_documents executed in {execution_time:.4f} seconds.")
    
    setup_environment()  

    st.write("Adapt Extraction Initiated...")
    start_time = time.time()

    log_to_file(f"User query: {query_list}")  
    plan_structure = planner(query_list=query_list)  
    log_to_file(f"Generated plan: {plan_structure}")  
    

    # Call the controller function to execute the plan  
    execution_result = controller(plan_structure)  
    log_to_file(f"Execution result: {execution_result}")  
    # print("Execution result:", execution_result)  

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Adapt executed in {execution_time:.4f} seconds.")
    st.write(f"Adapt executed in {execution_time:.4f} seconds.")


    st.write("Payoff letter generation started...")
    start_time = time.time()

    for section in get_section_generator():
        with open('Adapt_verified_payoff_letter.txt', 'a') as file:  
            file.write(f"{section}\n\n")


    end_time = time.time()
    execution_time = end_time - start_time
    print(f"get_section_generator executed in {execution_time:.4f} seconds.")
    st.write(f"get_section_generator executed in {execution_time:.4f} seconds.")



    full_text = get_extracted_data(file_path="./Adapt_verified_payoff_letter.txt")
  
    # Provide a button to download the content  
    btn = st.download_button(  
        label="Download Letter",  
        data=full_text,  
        file_name="Adapt_verified_payoff_letter.txt",  
        mime="text/plain"  
    )

    st.write("Resource Clean-up")
    clear_files()
    remove_files()


  
# Run the app with `streamlit run your_script.py`
