import streamlit as st
import urllib.request
import json
import os
import ssl
from rava_backend import rava_loop

st.title('Rava App')

def allowSelfSignedHttps(allowed):
	# bypass the server certificate verification on client side
	if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
		ssl._create_default_https_context = ssl._create_unverified_context

def main():
	allowSelfSignedHttps(True)
	st.set_page_config(page_title="Speech To Text", layout="wide")
	if st.button('Start Rava Loop'):
		exchange = rava_loop()

def store_convo():
	pass
