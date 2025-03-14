import streamlit as st
import os
import time
import ssl
import pandas as pd
impot
from datetime import datetime
from rava_backend import recognize_speech, speak_response




def allowSelfSignedHttps(allowed):
    # bypass the server certificate verification on client side
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

def main():
    st.set_page_config(page_title="Speech To Text", layout="wide")
    st.title('Rava App')
    allowSelfSignedHttps(True)
    if "agent_status" not in st.session_state:
        st.session_state.agent_status = "inactive"

    # Custom CSS to center the button and make it circular
    st.markdown("""
        <style>
        div.stButton>button:first-child {
            display: block;
            margin: 0 auto;
            justify-content: center;
            align-items: center;
            height: 100vh;
			border-radius: 50%;
            width: 160px;
            height: 160px;
            font-size: 20px;
            background-color:;
        }
        div.stButton>button:second-child {
            display: block;
            margin-top: 10px;
            justify-content: center;
            align-items: center;
            font-size: 12px;
        }
        div.stColumns columns {
            display: block; 
            margin: 0 auto;
        }

        </style>
    """, unsafe_allow_html=True)

    # st.markdown("""
    #     <style>
    #     div.stButton>button:second-child {
    #         display: block;
    #         margin-top: 10px;
    #         justify-content: center;
    #         align-items: center;
    #         font-size: 12px;
    #     }
    #     </style>
    # """, unsafe_allow_html=True)
    col1, buttonCol, col3 = st.columns(3)
    if "convo_history" not in st.session_state:
        st.session_state.convo_history = {"User Information":[], "Agent Information":[]}

    if "event_log" not in st.session_state:
        st.session_state.event_log = pd.DataFrame(columns=["Timestamp", "Message"])

    if "m_log_status" not in st.session_state:
        st.session_state.m_log_status = False
    # convo_history ={"User Information":[], "Agent Information":[]}
    # with instructionCol:
    #     st.write("Click the button below to start talking to RAVA")
    with buttonCol:	
        talk_button = st.button("Talk to RAVA", key="talk", on_click=set_agent_state, args=("waiting",), disabled=st.session_state.agent_status != "inactive")
        end_button = st.button("End Conversation", key="end", on_click=set_agent_state, args=("inactive",), disabled =st.session_state.agent_status == "inactive")
        m_log_button = st.button("Note a marker for misunderstanding", key="tag", on_click=log_misunderstanding, args=(), disabled =(st.session_state.agent_status == "inactive" or 
                                                                                                                                        st.session_state.agent_status == "waiting"))
        if talk_button:
            rava()
            st.write(st.session_state.convo_history)
            st.session_state.convo_history = {"User Information":[], "Agent Information":[]}
            time.sleep(5)
            st.experimental_rerun() 
        if end_button:
            st.write(st.session_state.convo_history)
            st.session_state.convo_history = {"User Information":[], "Agent Information":[]}
            st.write("Conversation ended.")
            csv_file = "log.csv"
            st.session_state.event_log.to_csv(csv_file, index=False)
            st.download_button(
                label="Download Log (CSV)",
                data=csv_data,
                file_name="app_log.csv",
                mime="text/csv"
            )
        if m_log_button:
            st.write("Noting mark.")

def log_stamp(message):
    timestamp = datetime.now()
    st.session_state.event_log = pd.concat([st.session_state.event_log, 
                                              pd.DataFrame({"Timestamp": [timestamp], 
                                                            "Message": [message]})], 
                                                            ignore_index=True)

def log_misunderstanding():
    timestamp = datetime.now()
    st.session_state.m_log_status = not st.session_state.m_log_status

    # True = Start of the misunderstanding, False = end of the misunderstanding
    
    if st.session_state.m_log_status :
        log_stamp("Start of user misunderstanding")
    else: 
        log_stamp("End of user misunderstanding")

def set_agent_state(s):
    st.session_state["agent_status"] = s 

def rava():
    
    if "agent_status" not in st.session_state:
        st.session_state.agent_status = "waiting"
    """Main voice agent loop."""
    non_response_count = 0
    agent_status_message = st.empty()
    while non_response_count < 3:
         log_stamp("Started recording user")
         user_input = recognize_speech(st.session_state.convo_history)
         log_stamp("Finished recording user")
         agent_status_message = st.empty()
         if user_input:
             non_response_count = 0
             st.session_state.agent_status = "responding"
         else:
             st.session_state.agent_status = "waiting"
             non_response_count += 1
             
         if st.session_state.agent_status == "responding":
              agent_status_message.text("Agent responding...")
              response = "Voila une reponse"
            #   print(f"Agent: {response}")
              log_stamp(f'Agent speaking to user: {response} ')
              speak_response(response)
              log_stamp(f'Agent done speaking to user')
         elif st.session_state.agent_status == "waiting":
              agent_status_message.text("No input detected. Please try again after one second.")
         else:
              pass;
    set_agent_state("inactive")
    # st.write(st.session_state.convo_history)
    agent_status_message.text("Agent timed out after 3 undetected user input. Resetting agent...")
    # return st.session_state.convo_history

def store_convo():
    pass

if __name__ == "__main__":
    main()