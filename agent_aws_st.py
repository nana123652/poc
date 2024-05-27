import streamlit as st
import agent_setup  # Import your agent setup module here
from agent_setup import start_agent
@st.cache_resource
def load_agent():
    """
    Load the agent

    Returns:
        agent (HFagent): The agent object
    """
    return start_agent()

def sidebar() -> None:
    """
    Shows the sidebar
    """
    st.sidebar.image(
        "https://d1.awsstatic.com/gamedev/Programs/OnRamp/gt-well-architected.4234ac16be6435d0ddd4ca693ea08106bc33de9f.png",
        use_column_width=True,
    )
    st.sidebar.markdown(
        "Agent AWS is an automated, AI-powered agent that uses HuggingFace Transformers paired with numerous different foundation models"
    )

def app() -> None:
    """
    Controls the app flow
    """
    # Spin up the sidebar
    sidebar()

    agent = load_agent()

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # User input
    chat_input = st.text_input("Ask a question:")
    if chat_input:
        # Append user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": chat_input})

        # Generate agent's response
        with st.spinner("Generating..."):
            answer = agent.run(chat_input)

            # Append agent's response to chat history
            st.session_state.chat_history.append({"role": "AI Agent", "content": answer})

    # Display chat messages
    for message in st.session_state.chat_history:
        st.write(f"{message['role']}: {message['content']}")

def main() -> None:
    """
    Controls the flow of the Streamlit app
    """
    # Start the Streamlit app
    st.title("Agent AWS")
    st.subheader("Ask and Learn")
    app()

if __name__ == "__main__":
    main()
