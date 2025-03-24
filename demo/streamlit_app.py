import os
import streamlit as st
import sqlite3
from datetime import datetime
import tempfile
from dotenv import load_dotenv
from decouple import config as environ
from deep_knowledge.summary import Summary
from deep_knowledge.generic_llm_provider import GenericLLMProvider, _SUPPORTED_PROVIDERS

# Load environment variables
load_dotenv()


# Setup database
def init_db():
    conn = sqlite3.connect('deep_knowledge_history.sqlite3', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        provider TEXT,
        model TEXT,
        temperature REAL,
        language TEXT,
        file_name TEXT,
        extra_instructions TEXT,
        output TEXT
    )
    ''')
    conn.commit()
    return conn


# Initialize the database
conn = init_db()


# Function to save a summary to the database
def save_summary(provider, model, temperature, language, file_name, extra_instructions, output):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c = conn.cursor()
    c.execute('''
    INSERT INTO history (timestamp, provider, model, temperature, language, file_name, extra_instructions, output)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, provider, model, temperature, language, file_name, extra_instructions, output))
    conn.commit()


# Function to get all summaries from the database
def get_summaries():
    c = conn.cursor()
    c.execute('SELECT id, timestamp, provider, model, file_name FROM history ORDER BY timestamp DESC')
    return c.fetchall()


# Function to get a specific summary from the database
def get_summary(summary_id):
    c = conn.cursor()
    c.execute('SELECT * FROM history WHERE id = ?', (summary_id,))
    return c.fetchone()


# Initialize session state variables
if 'mind_map_content' not in st.session_state:
    st.session_state.mind_map_content = ""
    st.session_state.summary_architect_content = ""
    st.session_state.content_synthesizer_content = ""
    st.session_state.final_output = ""
    st.session_state.current_stage = ""

# Streamlit app
st.set_page_config(layout="wide", page_title="Deep Knowledge Summarization")

# Sidebar
with st.sidebar:
    st.header("LLM Settings")

    # Provider selection
    provider_options = sorted(list(_SUPPORTED_PROVIDERS))
    default_provider = environ("STREAMLIT_SUMMARY_DEFAULT_PROVIDER", default="google_genai")
    selected_provider = st.selectbox(
        "Select Provider", provider_options,
        index=provider_options.index(default_provider) if default_provider in provider_options else 0
    )

    # Model name input
    default_model = "gemini-2.0-flash" if selected_provider == "google_genai" else "gpt-4o" if selected_provider == "openai" else ""
    default_model = environ("STREAMLIT_SUMMARY_DEFAULT_MODEL", default=default_model)
    model_name = st.text_input("Model Name", value=default_model)

    # Temperature slider
    temperature = st.slider("Temperature", 0.0, 1.0, environ("STREAMLIT_SUMMARY_DEFAULT_TEMPERATURE", cast=float, default=0.1), 0.1)

    # Auto mode checkbox
    use_auto_mode = st.checkbox("Use Auto Mode", value=environ("STREAMLIT_SUMMARY_DEFAULT_AUTO_LLM", cast=bool, default=False),
                                help="Automatically chooses the best available model based on API keys. Above settings will be ignored.")

    # Language input
    language = st.text_input("Language", environ("STREAMLIT_SUMMARY_DEFAULT_LANGUAGE", default="original language of the content"))

    # File uploader
    st.header("Upload Content")
    uploaded_file = st.file_uploader("Choose a document", type=["pdf", "txt", "docx", "md", "epub"])

    # History section
    st.header("History")
    summaries = get_summaries()
    history_options = [f"{timestamp} - {provider}/{model} - {file_name}" for _, timestamp, provider, model, file_name in
                       summaries]
    selected_history = st.selectbox("Past summaries", [""] + history_options, index=0)

# Main content area
if selected_history:
    # Display selected summary from history
    selected_index = history_options.index(selected_history)
    summary_id = summaries[selected_index][0]
    summary_record = get_summary(summary_id)

    st.header(f"Summary: {summary_record[6]}")  # file_name
    st.markdown(f"**Provider:** {summary_record[2]}")  # provider
    st.markdown(f"**Model:** {summary_record[3]}")  # model
    st.markdown(f"**Temperature:** {summary_record[4]}")  # temperature
    st.markdown(f"**Language:** {summary_record[5]}")  # language
    st.markdown(f"**Generated on:** {summary_record[1]}")  # timestamp

    st.subheader("Extra Instructions")
    st.markdown(summary_record[7])  # extra_instructions

    st.subheader("Summary Output")
    st.markdown(summary_record[8])  # output
else:
    # Create new summary
    extra_instructions = st.text_area(
        "Extra Instructions", height=150,
        placeholder="Add any specific instructions for the summarization process...\nThese instructions will be passed to the Summary Architect who will convert them into module assignments."
    )

    if uploaded_file is not None:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1])
        temp_file.write(uploaded_file.getvalue())
        temp_file.close()
        file_path = temp_file.name
        file_name = uploaded_file.name

        # Display current stage info first
        stage_info = st.empty()

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Create tabs for each stage
        tabs = st.tabs(["Mind Map", "Summary Architecture", "Full Summary", "Final Output"])
        mind_map_tab, architecture_tab, summary_tab, final_output_tab = tabs

        # Create placeholders for content in each tab
        with mind_map_tab:
            mind_map_placeholder = st.empty()
            if st.session_state.mind_map_content:
                mind_map_placeholder.markdown(st.session_state.mind_map_content)

        with architecture_tab:
            architecture_placeholder = st.empty()
            if st.session_state.summary_architect_content:
                architecture_placeholder.markdown(st.session_state.summary_architect_content)

        with summary_tab:
            summary_placeholder = st.empty()
            if st.session_state.content_synthesizer_content:
                summary_placeholder.markdown(st.session_state.content_synthesizer_content)

        with final_output_tab:
            final_output_placeholder = st.empty()
            if st.session_state.final_output:
                final_output_placeholder.markdown(st.session_state.final_output)


        # Define streaming callback
        def streaming_callback(data):
            if data["type"] == "generation":
                content = data["content"]

                # Append content to the appropriate container based on current stage
                if st.session_state.current_stage == "mind_map":
                    st.session_state.mind_map_content += content
                    mind_map_placeholder.markdown(st.session_state.mind_map_content)

                elif st.session_state.current_stage == "summary_architect":
                    st.session_state.summary_architect_content += content
                    architecture_placeholder.markdown(st.session_state.summary_architect_content)

                elif st.session_state.current_stage == "content_synthesizer":
                    st.session_state.content_synthesizer_content += content
                    summary_placeholder.markdown(st.session_state.content_synthesizer_content)

            elif data["type"] == "event":
                event_type = data["event_type"]
                event_stage = data["stage"]
                event_content = data["content"]

                if event_type == "start":
                    # Update stage and progress based on event type
                    if event_stage == "mind_map":
                        st.session_state.current_stage = "mind_map"
                        progress_bar.progress(10)
                        status_text.text(event_content)
                        stage_info.info("Currently generating Mind Map - Check the Mind Map tab")

                    elif event_stage == "summary_architect":
                        st.session_state.current_stage = "summary_architect"
                        progress_bar.progress(40)
                        status_text.text(event_content)
                        stage_info.info(
                            "Currently generating Summary Architecture - Check the Summary Architecture tab")

                    elif event_stage == "content_synthesizer":
                        st.session_state.current_stage = "content_synthesizer"
                        progress_bar.progress(70)
                        status_text.text(event_content)
                        stage_info.info("Currently generating Full Summary - Check the Full Summary tab")


        # Run button
        if st.button("Run Summarization"):
            # Reset the session state
            st.session_state.mind_map_content = ""
            st.session_state.summary_architect_content = ""
            st.session_state.content_synthesizer_content = ""
            st.session_state.final_output = ""
            st.session_state.current_stage = ""

            # Clear placeholders
            mind_map_placeholder.empty()
            architecture_placeholder.empty()
            summary_placeholder.empty()
            final_output_placeholder.empty()

            # Start the summarization process
            status_text.text("Starting summarization...")
            progress_bar.progress(5)

            try:
                # Setup LLM based on selection
                if use_auto_mode:
                    llm = "auto"
                    provider_display = "auto"
                    model_display = "auto"
                else:
                    # Create LLM using GenericLLMProvider
                    llm_provider = GenericLLMProvider.from_provider(
                        provider=selected_provider,
                        model=model_name,
                        temperature=temperature
                    )
                    llm = llm_provider.llm
                    provider_display = selected_provider
                    model_display = model_name

                s = Summary(
                    llm=llm,
                    input_path=file_path,
                    language=language if language.lower() != "original language of the content" else None,
                    stream=True,
                    extra_instructions=extra_instructions,
                    streaming_callback=streaming_callback,
                )

                # Run the summarization
                s.run()

                # Display final output
                st.session_state.final_output = s.output
                final_output_placeholder.markdown(st.session_state.final_output)

                # Update progress and status
                progress_bar.progress(100)
                status_text.text("Summarization complete!")
                stage_info.success("Summarization complete! View the final result in the Final Output tab")

                # Save to database
                save_summary(
                    provider=provider_display,
                    model=model_display,
                    temperature=temperature,
                    language=language,
                    file_name=file_name,
                    extra_instructions=extra_instructions,
                    output=s.output
                )

                # Clean up temp file
                os.unlink(file_path)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                try:
                    # Clean up temp file
                    os.unlink(file_path)
                except:
                    pass
    else:
        st.info("Please upload a file in the sidebar to begin summarization.")
