from typing import List
import streamlit as st
from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from htmlTemplates import css, bot_template, user_template
from langchain.llms import HuggingFaceHub


def get_pdf_text(pdf_docs) -> str:
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(raw_text:str) -> List[str]:
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size = 800,
        chunk_overlap = 200, 
        length_function = len
    )
    chunks = text_splitter.split_text(raw_text)
    return chunks 

def get_vectorstore(text_chuks: List[str]):
    # embeddings = OpenAIEmbeddings()
    embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_texts(texts=text_chuks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(vectorstore):
    # llm = ChatOpenAI()
    llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.6, "max_length":512})
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory,
    )
    return conversation_chain
    
def handle_user_input(user_query):
    response = st.session_state.conversation({'question': user_query})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.markdown(user_template.replace("{{MSG}}", f"{message.content}"), unsafe_allow_html=True) # bold user messages
        else:
            st.markdown(bot_template.replace("{{MSG}}", f"{message.content}"), unsafe_allow_html=True) # italic bot responses


def main():
    load_dotenv()
    st.set_page_config(page_title="Chat Documents", page_icon=":books:")   

    st.write(css, unsafe_allow_html=True)
    
    if 'conversation' not in st.session_state:
        st.session_state.conversation = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with multiple PDFS :books:")
    user_question = st.text_input("Ask a question about your documents:")

    if user_question:
        handle_user_input(user_question)

    with st.sidebar:
        st.image("./assets/subheader.png")  # add this line to display the image
        pdf_docs = st.file_uploader(
            "Upload your documents here and click on Process", accept_multiple_files=True)
        
        if st.button("Process"):
            with st.spinner("Processing"): # user friendly message. 
                
                # get the pdf text:
                raw_text = get_pdf_text(pdf_docs)
                
                # get the text chunks:
                text_chuks = get_text_chunks(raw_text)

                # create vector store:
                vectorstore = get_vectorstore(text_chuks)     
                
                # create conversation chain:
                st.session_state.conversation = get_conversation_chain(vectorstore)
                st.markdown("<h2 style='text-align: center; color: green;'>✔️</h2>", unsafe_allow_html=True) # using an emoji instead of a text message

                
        
    
if __name__ == "__main__":
    main()