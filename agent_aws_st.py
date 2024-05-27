import streamlit as st
import agent_setup  # Import your agent setup module here
from agent_setup import start_agent
from PIL import Image  # Import the Image class from PIL

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

def display_response(answer) -> None:
    """
    Display the agent's response based on its type

    Args:
        answer: The agent's response
    """
    if isinstance(answer, str):
        st.write(answer)  # Display as plain text
    elif isinstance(answer, Image.Image):
        st.image(answer)  # Display as an image
    elif isinstance(answer, dict):
        st.markdown(answer["ans"])  # Display markdown content
        docs = answer["docs"].split("\n")
        with st.expander("Resources"):
            for doc in docs:
                st.write(doc)
    else:
        st.code(answer)  # Display as code

def beautify_chat_history(chat_history) -> None:
    """
    Beautify the chat history by separating conversations and truncating long agent responses

    Args:
        chat_history: List of chat messages (user and agent)
    """
    user_messages = []
    agent_messages = []
    for message in chat_history:
        if message["role"] == "user":
            user_messages.append(message["content"])
        elif message["role"] == "AI Agent":
            # Truncate long agent responses
            truncated_response = message["content"][:200] + "..." if len(message["content"]) > 200 else message["content"]
            agent_messages.append(truncated_response)

    # Display user messages
    st.write("**User Messages:**")
    for user_msg in user_messages:
        st.write(f"- {user_msg}")

    # Display agent responses
    st.write("**Agent Responses:**")
    for agent_resp in agent_messages:
        st.write(f"- {agent_resp}")

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

        # Display the response
        display_response(answer)

    # Beautify chat history
    beautify_chat_history(st.session_state.chat_history)

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
