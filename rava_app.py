import streamlit as st
from audiorecorder import audiorecorder
import os
import time
import ssl
import io
import pandas as pd
from datetime import datetime
import json
from pathlib import Path
from rava_backend import recognize_speech, generate_response, speak_response, calc_new_sr_p



def allowSelfSignedHttps(allowed):
  # bypass the server certificate verification on client side
  if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
    ssl._create_default_https_context = ssl._create_unverified_context

def main():
  # Agent Speech Rate Percentage. Initialized as zero to serve a s a flag that usre has not spoken yet
  # until they do, have a message to tell the user to speak at a normal and rate for their first time
  # Tell them to project their voice as if they are presenting something, and keeping a good (1ft) distance from
  #  their mics, possibly?
  if "agent_sr_p" not in st.session_state:
    st.session_state.agent_sr_p = 0
    st.session_state.agent_sr = 0
  
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
      width: 160px;
      height: 80px;
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
  
  col1, recordCol, buttonCol, col3 = st.columns(4)

  if "agent_history" not in st.session_state:
    st.session_state.agent_history = {"User Information":[], "Agent Information":[]}
  
  if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

  if "event_log" not in st.session_state:
    st.session_state.event_log = pd.DataFrame(columns=["Timestamp", "Message"])

  if "m_log" not in st.session_state:
    st.session_state.m_log = pd.DataFrame(columns=["Timestamp", "Message"])

  if "m_log_status" not in st.session_state:
    st.session_state.m_log_status = False

  agent_status_message = st.empty()

  with recordCol:
    handle_speaking_end()
    audio = audiorecorder("Click to record", "Click to stop recording", "Click to pause",
      custom_style={
        "display": "block",
        "justifyContent": "center",
        "alignItems": "center",
        "margin": "0 auto",
        "width": "160px",
        "height": "80px",
        "fontSize": "20px",
        "color": "white",
        "border": "none",
        "borderRadius": "7px"
      },
      start_style={
          "backgroundColor": "green",
      },
      pause_style={
          "backgroundColor": "orange",
      },
      stop_style={
          "backgroundColor": "red",
          "margin-top": "10px",
      },
      key="audio"
    )


  with buttonCol:
    handle_speaking_end()
    send_button = st.button("Send to RAVA", key="send", on_click=set_agent_state, args=("waiting",), disabled=(st.session_state.agent_status != "inactive"))
    end_button = st.button("End Conversation", key="end", on_click=set_agent_state, args=("inactive",), disabled = st.session_state.agent_status == "inactive")
    m_log_button = st.button("Log a misunderstanding", key="tag", on_click=log_misunderstanding, args=(), disabled = st.session_state.agent_status == "inactive")
    if send_button:
      
      if len(audio) > 0:
        audio.export(out_f = "user_input.wav", format = "wav")                    
        rava()

        # nothing after the rava call runs if the user logs a misunderstanding
        st.write(st.session_state.agent_history)
        st.session_state.agent_history = {"User Information":[], "Agent Information":[]}
      else :
        agent_status_message.text("No recording file detected. Try recording again.")
    
    if end_button:
      set_agent_state("inactive")
      st.write(st.session_state.agent_history)
      st.session_state.agent_history = {"User Information":[], "Agent Information":[]}
      st.write("Conversation ended.")

      handle_speaking_end()

      combined_log = pd.concat([st.session_state.m_log, st.session_state.event_log], ignore_index=True)
      final_log = combined_log.sort_values(by=combined_log.columns[0])

      csv_file = io.StringIO()
      final_log.to_csv(csv_file, index=False)
      csv_data = csv_file.getvalue()

      st.download_button(
          label="Download App Log (CSV)",
          data=csv_data,
          file_name="app_log.csv",
          mime="text/csv"
      )

def user_recording_present():
  my_file = Path("./user_input.wav")
  return my_file.is_file()

def log_stamp(misunderstanding, message):
  timestamp = datetime.now()
  log_data = pd.DataFrame({"Timestamp": [timestamp], "Message": [message]})

  if misunderstanding:
    st.session_state.m_log = pd.concat([st.session_state.m_log, log_data], ignore_index=True)
  else:
    st.session_state.event_log = pd.concat([st.session_state.event_log, log_data], ignore_index=True)

def log_misunderstanding():
  timestamp = datetime.now()
  st.session_state.m_log_status = not st.session_state.m_log_status

  # True = Start of the misunderstanding, False = end of the misunderstanding
  if st.session_state.m_log_status :
    log_stamp(True, "Start of user misunderstanding")
  else: 
    log_stamp(True, "End of user misunderstanding")

def handle_speaking_end():
  if os.path.exists("speech_state.json"):
    set_agent_state("inactive")
    try:
      with open("speech_state.json", "r") as f:
        state_data = json.load(f)
          
      # Add the log entry to the event log
      timestamp = datetime.fromisoformat(state_data["timestamp"])
      log_data = pd.DataFrame({"Timestamp": [timestamp], "Message": [state_data["message"]]})
      st.session_state.event_log = pd.concat([st.session_state.event_log, log_data], ignore_index=True)
          
      # Remove the state file after processing
      os.remove("speech_state.json")
    except Exception as e:
      print(f"Error processing speech state file: {e}")


def set_agent_state(s):
  st.session_state["agent_status"] = s 

def rava():
  if "agent_status" not in st.session_state:
    st.session_state.agent_status = "waiting"

  """Main voice agent loop."""
  agent_status_message = st.empty()

  log_stamp(False, "Started recording user")
  user_sr, user_input_text = recognize_speech(st.session_state.agent_history)
  log_stamp(False, f'Finished recording user, speech rate: {user_sr} (syllables/sec), input: {user_input_text}')
  agent_status_message = st.empty()

  if user_input_text:
    st.session_state.agent_status = "responding"
  else:
    st.session_state.agent_status = "waiting"
      
  if st.session_state.agent_status == "responding":
    agent_status_message.text("Agent responding...")
    response = generate_response(user_input_text, st.session_state.messages) # still working on this
    # response = "Voila une reponse"
    

    if st.session_state.agent_sr_p == 0:
      st.session_state.agent_sr, st.session_state.agent_sr_p = calc_new_sr_p(5, 8, user_sr)
    else:
      st.session_state.agent_sr, st.session_state.agent_sr_p = calc_new_sr_p(st.session_state.agent_sr_p,
                                                                              st.session_state.agent_sr, 
                                                                              user_sr)

    # print(f'Debugging: {st.session_state.agent_status} is barring noting a mark for misunderstanding')
    log_stamp(False, f'Agent starts speaking: {response}, speech rate: {st.session_state.agent_sr}, synth rate: {st.session_state.agent_sr_p}')
    speak_response(response, st.session_state.agent_sr_p)

    # Use a file to write to avoid Streamlit's re-execution of the code from the top when logging a misunderstanding
    state_data = {"timestamp": datetime.now().isoformat(),"message": "Agent done speaking to user"}
    with open("speech_state.json", "w") as f:
        json.dump(state_data, f)
    print("End file made.")
  elif st.session_state.agent_status == "waiting":
    agent_status_message.text("No input detected. Try recording again.")
  else:
    pass;

if __name__ == "__main__":
  main()