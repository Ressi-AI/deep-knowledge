import os
import uuid
import streamlit as st
import sqlite3
from datetime import datetime
import tempfile
from contextlib import suppress
from dotenv import load_dotenv
from decouple import config as environ
from deep_knowledge.summary import Summary
from deep_knowledge.generic_llm_provider import GenericLLMProvider, _SUPPORTED_PROVIDERS
from demo.writers import write_md_to_pdf

# Load environment variables
load_dotenv()


# Setup database
def init_db():
    conn = sqlite3.connect('deep_knowledge_history.sqlite3', check_same_thread=False)
    c = conn.cursor()
    # Add new columns if they don't exist (simple approach for existing dbs)
    with suppress(sqlite3.OperationalError):
        c.execute('ALTER TABLE history ADD COLUMN one_shot INTEGER')
    with suppress(sqlite3.OperationalError):
        c.execute('ALTER TABLE history ADD COLUMN target_word_count INTEGER')
    with suppress(sqlite3.OperationalError):
        c.execute('ALTER TABLE history ADD COLUMN template TEXT')

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
        output TEXT,
        one_shot INTEGER,          -- Added
        target_word_count INTEGER, -- Added
        template TEXT              -- Added
    )
    ''')
    conn.commit()
    return conn


# Initialize the database (this will now try to add columns)
conn = init_db()


# Function to save a summary to the database (Updated)
def save_summary(provider, model, temperature, language, file_name, extra_instructions, output, one_shot, target_word_count, template):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c = conn.cursor()
    # Convert boolean one_shot to integer for SQLite
    one_shot_int = 1 if one_shot else 0
    # Ensure target_word_count is None or int
    word_count_val = int(target_word_count) if target_word_count is not None and target_word_count > 0 else None
    template_val = template if template else None # Store empty string as None

    c.execute('''
    INSERT INTO history (timestamp, provider, model, temperature, language, file_name, extra_instructions, output, one_shot, target_word_count, template)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, provider, model, temperature, language, file_name, extra_instructions, output, one_shot_int, word_count_val, template_val))
    conn.commit()


# Function to get all summaries from the database (No change needed here)
def get_summaries():
    c = conn.cursor()
    c.execute('SELECT id, timestamp, provider, model, file_name FROM history ORDER BY timestamp DESC')
    return c.fetchall()


# Function to get a specific summary from the database (No change needed, SELECT * gets all columns)
def get_summary(summary_id):
    c = conn.cursor()
    c.execute('SELECT * FROM history WHERE id = ?', (summary_id,))
    # Returns a tuple: (id, timestamp, provider, model, temperature, language, file_name, extra_instructions, output, one_shot, target_word_count, template)
    return c.fetchone()


def on_copy_click(text, context=None):
    if context is None:
        st.code(text)
    else:
        with context:
            st.code(text)
    st.toast("You'll see the message in a separate window from where you can perform the copy operation", icon='✅')
    return


# Initialize session state variables (add one for one_shot_content if needed, though maybe final_output is enough)
if 'mind_map_content' not in st.session_state:
    st.session_state.mind_map_content = ""
    st.session_state.summary_architect_content = ""
    st.session_state.content_synthesizer_content = ""
    st.session_state.final_output = ""
    st.session_state.current_stage = ""
    # Optional: Add state specific to one_shot if distinction is needed beyond final_output
    # st.session_state.one_shot_content = ""


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
    default_model = "gemini-2.5-pro-exp-03-25" if selected_provider == "google_genai" else "gpt-4o" if selected_provider == "openai" else ""
    default_model = environ("STREAMLIT_SUMMARY_DEFAULT_MODEL", default=default_model)
    model_name = st.text_input("Model Name", value=default_model)

    # Temperature slider
    temperature = st.slider("Temperature", 0.0, 1.0, environ("STREAMLIT_SUMMARY_DEFAULT_TEMPERATURE", cast=float, default=0.1), 0.1)

    # Auto mode checkbox
    use_auto_mode = st.checkbox("Use Auto Mode", value=environ("STREAMLIT_SUMMARY_DEFAULT_AUTO_LLM", cast=bool, default=False),
                                help="Automatically chooses the best available model based on API keys. Above settings will be ignored.")

    # ----- New Parameters -----
    st.header("Summary Configuration")

    use_emoji = st.checkbox("Use Emoji", value=False, help="Enable or disable emoji support in the summaries.")

    # One-shot mode checkbox
    one_shot_mode = st.checkbox("Use One-Shot Summarization", value=False, # Default to multi-agent
                                help="Generate the summary in a single step, bypassing the Mind Map and Architecture stages.")

    # Target Word Count
    word_count = st.number_input("Target Word Count (Optional)", min_value=0, value=0, step=50, format="%d",
                                help="Suggests a target word count for the final summary. Set to 0 for no specific target.")
    # Convert 0 to None for the Summary class
    target_word_count = word_count if word_count > 0 else None

    # Template Selection
    template_options = ["None", "extended", "story_spine"]
    selected_template = st.selectbox("Summary Template (Optional)", template_options, index=0,
                                     help="Choose a specific structure for the summary ('extended' or 'story_spine'). 'None' uses the default.")
    # Convert "None" string to actual None for the Summary class
    template = selected_template if selected_template != "None" else None
    # --------------------------

    # Language input
    language = st.text_input("Language", environ("STREAMLIT_SUMMARY_DEFAULT_LANGUAGE", default="English"))

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
    # Display selected summary from history (Updated)
    selected_index = history_options.index(selected_history)
    summary_id = summaries[selected_index][0]
    summary_record = get_summary(summary_id)

    # Unpack the record (assuming order from updated SELECT *)
    (rec_id, rec_timestamp, rec_provider, rec_model, rec_temperature, rec_language,
     rec_file_name, rec_extra_instructions, rec_output, rec_one_shot,
     rec_target_word_count, rec_template) = summary_record

    st.header(f"Summary: {rec_file_name}")
    st.markdown(f"**Generated on:** {rec_timestamp}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Configuration")
        st.markdown(f"**Provider:** {rec_provider}")
        st.markdown(f"**Model:** {rec_model}")
        st.markdown(f"**Temperature:** {rec_temperature}")
        st.markdown(f"**Language:** {rec_language}")
    with col2:
        st.markdown("#### Summary Settings")
        st.markdown(f"**One-Shot Mode:** {'Yes' if rec_one_shot == 1 else 'No'}")
        st.markdown(f"**Target Word Count:** {rec_target_word_count if rec_target_word_count else 'Not Set'}")
        st.markdown(f"**Template:** {rec_template if rec_template else 'None'}")

    st.subheader("Extra Instructions")
    st.markdown(rec_extra_instructions if rec_extra_instructions else "_None_")

    st.subheader("Summary Output")
    output_content = rec_output
    st.markdown(output_content)

    st.button(
        label="📋 Copy to clipboard",
        key=str(uuid.uuid4()),
        on_click=on_copy_click,
        args=(output_content,),
        help="Copy text response to clipboard"
    )
else:
    # Create new summary
    extra_instructions = st.text_area(
        "Extra Instructions", height=100, # Reduced height slightly
        placeholder="Add any specific instructions for the summarization process..."
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

        # --- Conditional Tab Creation ---
        if one_shot_mode:
            # Only show final output tab in one-shot mode
            final_output_tab = st.tabs(["Final Output"])[0] # Get the single tab object

            with final_output_tab:
                final_output_placeholder = st.empty()
                if st.session_state.final_output:
                    final_output_placeholder.markdown(st.session_state.final_output)

                st.button(
                    label="📋 Copy to clipboard",
                    key=str(uuid.uuid4()) + "_oneshot", # Unique key
                    on_click=on_copy_click,
                    args=(st.session_state.final_output,),
                    help="Copy text response to clipboard"
                )

        else:
            # Show all tabs for multi-agent mode
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

                st.button(
                    label="📋 Copy to clipboard",
                    key=str(uuid.uuid4()) + "_multi", # Unique key
                    on_click=on_copy_click,
                    args=(st.session_state.final_output,),
                    help="Copy text response to clipboard"
                )
        # -----------------------------

        # Define streaming callback (Updated for one_shot)
        def streaming_callback(data):
            if data["type"] == "generation":
                content = data["content"]

                # Append content based on current stage
                if st.session_state.current_stage == "mind_map" and not one_shot_mode:
                    st.session_state.mind_map_content += content
                    # Use suppress because placeholder might not exist in one-shot mode
                    with suppress(NameError):
                        mind_map_placeholder.markdown(st.session_state.mind_map_content)

                elif st.session_state.current_stage == "summary_architect" and not one_shot_mode:
                    st.session_state.summary_architect_content += content
                    with suppress(NameError):
                        architecture_placeholder.markdown(st.session_state.summary_architect_content)

                elif st.session_state.current_stage == "content_synthesizer" and not one_shot_mode:
                    st.session_state.content_synthesizer_content += content
                    with suppress(NameError):
                        summary_placeholder.markdown(st.session_state.content_synthesizer_content)

                elif st.session_state.current_stage == "one_shot" and one_shot_mode:
                    # In one-shot mode, generation events go directly to final output
                    st.session_state.final_output += content
                    # The final_output_placeholder always exists
                    final_output_placeholder.markdown(st.session_state.final_output)

            elif data["type"] == "event":
                event_type = data["event_type"]
                event_stage = data["stage"]
                event_content = data["content"]

                if event_type == "start":
                    # Update stage and progress based on event type
                    st.session_state.current_stage = event_stage # Set current stage

                    if event_stage == "mind_map" and not one_shot_mode:
                        progress_bar.progress(10)
                        status_text.text(event_content)
                        stage_info.info("Currently generating Mind Map - Check the Mind Map tab")

                    elif event_stage == "summary_architect" and not one_shot_mode:
                        progress_bar.progress(40)
                        status_text.text(event_content)
                        stage_info.info("Currently generating Summary Architecture - Check the Summary Architecture tab")

                    elif event_stage == "content_synthesizer" and not one_shot_mode:
                        progress_bar.progress(70)
                        status_text.text(event_content)
                        stage_info.info("Currently generating Full Summary - Check the Full Summary tab")

                    elif event_stage == "one_shot" and one_shot_mode:
                        progress_bar.progress(25) # Adjust progress for one-shot
                        status_text.text(event_content)
                        stage_info.info("Generating summary directly (One-Shot Mode)...")


        # Run button
        if st.button("Run Summarization"):
            # Reset the session state
            st.session_state.mind_map_content = ""
            st.session_state.summary_architect_content = ""
            st.session_state.content_synthesizer_content = ""
            st.session_state.final_output = ""
            st.session_state.current_stage = ""
            # st.session_state.one_shot_content = "" # Reset if using separate state

            # Clear placeholders (use try-except for conditional placeholders)
            try: mind_map_placeholder.empty()
            except NameError: pass
            try: architecture_placeholder.empty()
            except NameError: pass
            try: summary_placeholder.empty()
            except NameError: pass
            final_output_placeholder.empty() # This one always exists

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
                    llm_provider = GenericLLMProvider.from_provider(
                        provider=selected_provider,
                        model=model_name,
                        temperature=temperature
                    )
                    llm = llm_provider.llm
                    provider_display = selected_provider
                    model_display = model_name

                # Instantiate Summary with all parameters (Updated)
                s = Summary(
                    llm=llm,
                    input_path=file_path,
                    language=language,
                    stream=True,
                    extra_instructions=extra_instructions,
                    streaming_callback=streaming_callback,
                    one_shot=one_shot_mode,
                    target_word_count=target_word_count,
                    template=template,
                    use_emoji=use_emoji,
                )

                # Run the summarization
                s.run()

                # Display final output in its placeholder (redundant if streamed, but safe)
                st.session_state.final_output = s.output
                final_output_placeholder.markdown(st.session_state.final_output)
                write_md_to_pdf(s.output, filename=os.path.splitext(file_name)[0])

                # Update progress and status
                progress_bar.progress(100)
                status_text.text("Summarization complete!")
                if one_shot_mode:
                    stage_info.success("One-Shot Summarization complete! View the result in the Final Output tab")
                else:
                    stage_info.success("Multi-Agent Summarization complete! View the final result in the Final Output tab")

                # Save to database (Updated)
                save_summary(
                    provider=provider_display,
                    model=model_display,
                    temperature=temperature,
                    language=language,
                    file_name=file_name,
                    extra_instructions=extra_instructions,
                    output=s.output, # Save final output regardless of mode
                    one_shot=one_shot_mode,
                    target_word_count=target_word_count,
                    template=template
                )

                # Clean up temp file
                os.unlink(file_path)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                progress_bar.progress(0) # Reset progress on error
                status_text.text("Error during summarization.")
                stage_info.error("An error occurred during the process.")
                try:
                    # Clean up temp file
                    os.unlink(file_path)
                except:
                    pass
    else:
        st.info("Please upload a file in the sidebar to begin summarization.")