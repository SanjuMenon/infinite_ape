import streamlit as st
import os
from llm_fsm import API
from dotenv import load_dotenv
from llm_fsm.handlers import HandlerTiming
from counterfactual_models import query_model
import time

# Load environment variables
load_dotenv()

def add_custom_css():
    """Add custom CSS to center the chat and improve styling"""
    st.markdown("""
    <style>
    .main {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .stChatInput {
        position: fixed;
        bottom: 2rem;
        left: 50%;
        transform: translateX(-50%);
        width: 80%;
        max-width: 600px;
        z-index: 1000;
    }
    
    .chat-container {
        margin-bottom: 100px;
    }
    
    .results-section {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_causal_agent():
    """Initialize the causal agent API"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        st.error("Please set your OPENAI_API_KEY environment variable")
        return None
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fsm_path = os.path.join(current_dir, "form_filling.json")
    
    try:
        api = API.from_file(
            path=fsm_path,
            model="gpt-4",
            api_key=api_key,
            temperature=0.3
        )
        
        # Register the causal response generator handler
        api.register_handler(
            api.create_handler("CausalResponseGenerator")
                .at(HandlerTiming.CONTEXT_UPDATE)
                .when_keys_updated("summary")
                .with_priority(10)
                .do(generate_causal_response)
        )
        
        return api
    except Exception as e:
        st.error(f"Error initializing causal agent: {str(e)}")
        return None

def generate_causal_response(context):
    """Extract entities from conversation and generate causal scenarios"""
    user_input = context.get("summary", "")
    scenarios = []
    
    try:
        for summary in query_model(
            options_file="saved_models_synthetic\synthetic_dataset_th0_0_Margin_Utilisation_Category_available_options.yaml", 
            prompt=user_input
        ):
            scenarios.append(summary)
    except Exception as e:
        scenarios.append(f"Error generating scenarios: {str(e)}")
    
    return {"scenarios": scenarios}

def process_user_message(api, user_input, conversation_id):
    """Process user input and return system response"""
    try:
        # Store user message in context for logic conditions
        context = api.get_data(conversation_id)
        context["user_message"] = user_input.lower()
        
        # Process the user input
        response = api.converse(user_input, conversation_id)
        return response, None
    except Exception as e:
        return None, str(e)

def display_conversation_results(api, conversation_id):
    """Display the final classification and variables"""
    try:
        data = api.get_data(conversation_id)
        
        # Filter out system keys and display relevant information
        classification_data = {
            k: v for k, v in data.items() 
            if not k.startswith('_') 
            and k not in ['user_message']
            and k in ['user_question', 'question_type', 'target_variable', 'input_variables', 'scenarios']
        }
        
        if classification_data:
            st.markdown('<div class="results-section">', unsafe_allow_html=True)
            st.subheader("📊 Analysis Results")
            for key, value in classification_data.items():
                if key == 'scenarios' and isinstance(value, list):
                    st.write(f"**{key.replace('_', ' ').title()}:**")
                    for i, scenario in enumerate(value, 1):
                        st.write(f"{i}. {scenario}")
                else:
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying results: {str(e)}")

def main():
    st.set_page_config(
        page_title="Causal Agent",
        page_icon="🧠",
        layout="centered"
    )
    
    # Add custom CSS
    add_custom_css()
    
    # Center the title and description
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>🧠 Causal Agent</h1>
        <p style="font-size: 1.1rem; color: #666;">Ask me what-if questions and I'll help you understand causal relationships!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if "api" not in st.session_state:
        st.session_state.api = initialize_causal_agent()
    
    if "conversation_id" not in st.session_state:
        if st.session_state.api:
            st.session_state.conversation_id, initial_response = st.session_state.api.start_conversation()
            st.session_state.messages = [{"role": "assistant", "content": initial_response}]
        else:
            st.session_state.messages = []
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Create a container for the chat messages
    chat_container = st.container()
    
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat messages from history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Check if conversation has ended
        if st.session_state.api and st.session_state.conversation_id:
            if st.session_state.api.has_conversation_ended(st.session_state.conversation_id):
                # Display final results
                display_conversation_results(st.session_state.api, st.session_state.conversation_id)
                
                # Add restart button centered
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔄 Start New Conversation", use_container_width=True):
                        st.session_state.conversation_id, initial_response = st.session_state.api.start_conversation()
                        st.session_state.messages = [{"role": "assistant", "content": initial_response}]
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input at the bottom
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process message and display response
        if st.session_state.api and st.session_state.conversation_id:
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    response, error = process_user_message(
                        st.session_state.api, 
                        prompt, 
                        st.session_state.conversation_id
                    )
                    
                    if error:
                        st.error(f"Error: {error}")
                    else:
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            with st.chat_message("assistant"):
                st.error("Causal agent not initialized. Please check your API key.")

if __name__ == "__main__":
    main()