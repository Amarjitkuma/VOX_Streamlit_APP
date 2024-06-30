import streamlit as st
import requests
import time
import swagger_client
import os
import json
import uuid
import logging

# Set page title and favicon
st.set_page_config(page_title='Vox Service', page_icon=':microphone:')

# Define custom CSS for the welcome text and sidebar
custom_css = """
    <style>
    .welcome-text {
        text-align: center;
        font-size: 3.5em;
        background: linear-gradient(to right, #ff00cc, #3333ff, #00ffcc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .logo {
        width: 150px; /* Adjust this value to change the size of the logo */
        display: inline-block;
        vertical-align: middle;
        margin-left: 10px;
    }
    .sidebar .sidebar-content {
        background: #f0f2f6;
        padding: 20px;
    }
    .sidebar .sidebar-content h2 {
        color: #3333ff;
    }
    .sidebar .sidebar-content a {
        font-size: 1.2em;
        color: #ff00cc;
        text-decoration: none;
        transition: color 0.3s ease;
    }
    .sidebar .sidebar-content a:hover {
        color: #3333ff;
    }
    .transcribe-section {
        font-family: Arial, sans-serif;
        color: #333;
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    .transcribe-section label {
        font-size: 1.2em;
        color: #555;
    }
    .transcribe-section input, .transcribe-section select {
        font-size: 1em;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ddd;
        margin-top: 10px;
        margin-bottom: 20px;
        width: 100%;
        background-color: #e8eaf6; /* Adjust input background color */
    }
    .transcribe-button {
        background-color: #3333ff;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-size: 1.2em;
        cursor: pointer;
        transition: background-color 0.3s ease;
        display: inline-block;
        margin-top: 20px;
        position: relative;
        font-size: 1em; /* Smaller button text */
        padding: 8px 16px; /* Smaller button size */
    }
    .transcribe-button:hover {
        background-color: #ff00cc;
    }
    .output-space {
        margin-top: 20px;
        padding: 20px;
        background-color: #f0f2f6;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    </style>
"""

# Inject the custom CSS
st.markdown(custom_css, unsafe_allow_html=True)

# Sidebar with menu and logo
st.sidebar.markdown('<img src="https://github.com/Amarjitkuma/Speaker_diarization_Project/blob/main/max_life_logo.png?raw=true" class="logo">', unsafe_allow_html=True)
st.sidebar.markdown("<h2>Menu</h2>", unsafe_allow_html=True)
menu_option = st.sidebar.radio("Select an option", ("Home", "Settings", "Transcribe"))

if menu_option == "Home":
    st.write("This is the Home section.")
elif menu_option == "Settings":
    st.sidebar.markdown("### Settings")
    setting_option = st.sidebar.selectbox("Select a setting option", ("Model Feature", "Pricing", "Vernacular Language Support"))
    if setting_option == "Model Feature":
        st.write("Settings - Model Feature")
    elif setting_option == "Pricing":
        st.write("Settings - Pricing")
    elif setting_option == "Vernacular Language Support":
        st.write("Settings - Vernacular Language Support")
elif menu_option == "Transcribe":
    st.markdown('<div class="transcribe-section">', unsafe_allow_html=True)
    st.markdown("<h2>Transcription Section</h2>", unsafe_allow_html=True)  # Add a heading for the transcription section
    
    blob_url = st.text_input("Enter blob storage URL of audio file", placeholder="e.g., https://blobstorage.com/audiofile.wav")
    lang = st.selectbox("Select language of audio", ["hi-IN", "en-US", "es-ES", "fr-FR"])  # Azure language codes
    
    st.markdown('<label>Diarization</label>', unsafe_allow_html=True)
    diarization = st.radio("", ("Yes", "No"))
    
    speakers = st.number_input("Number of speakers in audio", min_value=1, max_value=10, step=1)
    output_lang = st.selectbox("Select transcription output language", ["Hinglish", "English", "Spanish", "French"])
    output_format = st.selectbox("Select output format", ["JSON", "TXT"])

    transcribe_button = st.button('Transcribe')

    if transcribe_button:
        st.write("Starting transcription...")

        # Define region and subscription key globally
        transcription_key = os.getenv('transcription_API_key')
        transcription_region =os.getenv('region')

        NAME = "Simple transcription"
        DESCRIPTION = "Simple transcription description"
        LOCALE = lang
        RECORDINGS_CONTAINER_URI = blob_url

        def parse_time_string(time_str):
            """
            Parse the time string formatted as PT#M#.#S to seconds as a float.
            Example: 'PT1M10.54S' -> 70.54
            """
            time_str = time_str[2:]  # Remove the 'PT' prefix
            minutes = 0
            seconds = 0
            
            if 'M' in time_str:
                parts = time_str.split('M')
                minutes = float(parts[0])
                if 'S' in parts[1]:
                    seconds = float(parts[1].rstrip('S'))
            elif 'S' in time_str:
                seconds = float(time_str.rstrip('S'))
            
            total_seconds = minutes * 60 + seconds
            return total_seconds

        def transcribe_from_container(uri, properties):
            """
            Transcribe all files in the container located at `uri` using the settings specified in `properties`
            using the base model for the specified locale.
            """
            transcription_definition = swagger_client.Transcription(
                display_name=NAME,
                description=DESCRIPTION,
                locale=LOCALE,
                content_container_url=uri,
                properties=properties
            )

            return transcription_definition

        def _paginate(api, paginated_object):
            """
            The autogenerated client does not support pagination. This function returns a generator over
            all items of the array that the paginated object `paginated_object` is part of.
            """
            yield from paginated_object.values
            typename = type(paginated_object).__name__
            auth_settings = ["api_key"]
            while paginated_object.next_link:
                link = paginated_object.next_link[len(api.api_client.configuration.host):]
                paginated_object, status, headers = api.api_client.call_api(link, "GET",
                    response_type=typename, auth_settings=auth_settings)

                if status == 200:
                    yield from paginated_object.values
                else:
                    raise Exception(f"could not receive paginated data: status {status}")

        def delete_all_transcriptions(api):
            """
            Delete all transcriptions associated with your speech resource.
            """
            logging.info("Deleting all existing completed transcriptions.")

            # get all transcriptions for the subscription
            transcriptions = list(_paginate(api, api.get_transcriptions()))

            # Delete all pre-existing completed transcriptions.
            # If transcriptions are still running or not started, they will not be deleted.
            for transcription in transcriptions:
                transcription_id = transcription._self.split('/')[-1]
                logging.debug(f"Deleting transcription with id {transcription_id}")
                try:
                    api.delete_transcription(transcription_id)
                except swagger_client.rest.ApiException as exc:
                    logging.error(f"Could not delete transcription {transcription_id}: {exc}")

        logging.info("Starting transcription client...")

        # configure API key authorization: subscription_key
        configuration = swagger_client.Configuration()
        configuration.api_key["Ocp-Apim-Subscription-Key"] = transcription_key
        configuration.host = f"https://{transcription_region}.api.cognitive.microsoft.com/speechtotext/v3.1"

        # create the client object and authenticate
        client = swagger_client.ApiClient(configuration)

        # create an instance of the transcription api class
        api = swagger_client.CustomSpeechTranscriptionsApi(api_client=client)

        # Specify transcription properties
        properties = swagger_client.TranscriptionProperties()
        properties.diarization_enabled = diarization == "Yes"
        properties.diarization = swagger_client.DiarizationProperties(
            swagger_client.DiarizationSpeakersProperties(min_count=1, max_count=speakers))

        # Transcribe all files from a container
        transcription_definition = transcribe_from_container(RECORDINGS_CONTAINER_URI, properties)

        created_transcription, status, headers = api.transcriptions_create_with_http_info(transcription=transcription_definition)

        transcription_id = headers["location"].split("/")[-1]

        logging.info(f"Created new transcription with id '{transcription_id}' in region {transcription_region}")
        logging.info("Checking status.")

        completed = False

        while not completed:
            time.sleep(5)
            transcription = api.transcriptions_get(transcription_id)
            logging.info(f"Transcriptions status: {transcription.status}")

            if transcription.status in ("Failed", "Succeeded"):
                completed = True

            if transcription.status == "Succeeded":
                if properties.destination_container_url is not None:
                    logging.info("Transcription succeeded. Results are located in your Azure Blob Storage.")
                    break

                pag_files = api.transcriptions_list_files(transcription_id)
                for file_data in _paginate(api, pag_files):
                    if file_data.kind != "Transcription":
                        continue

                    audiofilename = file_data.name
                    results_url = file_data.links.content_url
                    results = requests.get(results_url)

                    results_json = results.json()
                    transcripts = []
                    for phrase in results_json.get('recognizedPhrases', []):
                        speaker = phrase.get('speaker', 'Unknown')
                        offset = parse_time_string(phrase.get('offset', ''))
                        duration = parse_time_string(phrase.get('duration', ''))
                        text = phrase['nBest'][0].get('display', '')
                        confidence = phrase['nBest'][0].get('confidence', '')

                        transcript = {
                            "speaker": speaker,
                            "sentence": text,
                            "start_time": offset,
                            "end_time": duration + offset,
                            "confidence": confidence  
                        }
                        transcripts.append(transcript)

                    output_filename = f"transcription.json"
                    with open(output_filename, 'w', encoding='utf-8') as json_file:
                        json.dump(transcripts, json_file, ensure_ascii=False, indent=4)
                    logging.info(f"Transcription saved to {output_filename}") 
            
            elif transcription.status == "Failed":
                logging.info(f"Transcription failed: {transcription.properties.error.message}")

        st.write("Transcription complete.")
        
        # Transliteration process
        st.write("Starting transliteration...")

        transliteration_key = os.getenv('translation_API_key')
        transliteration_region = os.getenv('region')
        transliteration_endpoint = 'https://api.cognitive.microsofttranslator.com/'

        transliteration_path = '/transliterate?api-version=3.0'
        transliteration_params = '&language=hi&fromScript=deva&toScript=latn'
        constructed_url = transliteration_endpoint + transliteration_path + transliteration_params

        headers = {
            'Ocp-Apim-Subscription-Key': transliteration_key,
            'Ocp-Apim-Subscription-Region': transliteration_region,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        def transliterate_text(text):
            body = [{'text': text}]
            response = requests.post(constructed_url, headers=headers, json=body)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error: {response.status_code}, {response.text}")
                return None

        # Read the JSON file
        input_file = 'transcription.json'  # Ensure your JSON file is named correctly
        output_file = 'transliteration.json'
        audio_file_name = "OUT-1234000.txt"  # Replace with your actual audio file name if needed

        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Prepare the output structure
        output_data = {
            "audio_file_name": audio_file_name,
            "SentList": []
        }

        # Iterate through the JSON data and transliterate the text
        for entry in data:
            if isinstance(entry, dict):  # Ensure it's a valid entry
                original_text = entry['sentence']
                transliterated_response = transliterate_text(original_text)
                
                if transliterated_response and 'text' in transliterated_response[0]:
                    transliterated_text = transliterated_response[0]['text']
                else:
                    transliterated_text = original_text  # Fallback to the original text if transliteration fails
                
                new_entry = {
                    "speaker": entry['speaker'],
                    "sentence": transliterated_text,
                    "start_time": entry['start_time'],
                    "end_time": entry['end_time'],
                    "confidence": entry['confidence']
                }
                output_data["SentList"].append(new_entry)

        # Write the new JSON data with transliterated text to a new file
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(output_data, file, ensure_ascii=False, indent=4)

        st.write(f"Transliteration complete. Output saved to {output_file}")

        # Display transliteration results in Streamlit
        st.write("Transliteration Results:")
        for sentence in output_data["SentList"]:
            st.write(f"Speaker {sentence['speaker']} ({sentence['start_time']}-{sentence['end_time']}s): {sentence['sentence']} (Confidence: {sentence['confidence']})")

# Create a three-column layout for logos and welcome text
col1, col2, col3 = st.columns([1, 3, 1])

# Display the welcome text in the center column
with col2:
    st.markdown('<h1 class="welcome-text">Welcome to Vox Service</h1>', unsafe_allow_html=True)

# Display the main image below the header
st.image('https://github.com/Amarjitkuma/Speaker_diarization_Project/blob/main/theem.jpg?raw=true', use_column_width=True)

st.write("This is your main content area.")
