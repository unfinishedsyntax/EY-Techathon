import streamlit as st
import pandas as pd

# Load dataset
df = pd.read_csv("TataCapital_200_customers.csv")

st.title("💬 Tata Capital - Personal Loan Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

def add_message(sender, text):
    st.session_state.messages.append({"sender": sender, "text": text})

# Chat display
for m in st.session_state.messages:
    st.chat_message(m["sender"]).markdown(m["text"])

# User input
if prompt := st.chat_input("Ask about a personal loan..."):
    add_message("user", prompt)
    st.chat_message("user").markdown(prompt)

    # Master Agent orchestration (simple simulation)
    response = ""
    if "loan" in prompt.lower():
        response = "Sure, I can help with that. Can I know your Customer ID to check pre-approved offers?"
    elif prompt.startswith("C"):
        if prompt in df["CustomerID"].values:
            cust = df[df["CustomerID"] == prompt].iloc[0]
            response = f"Customer {cust['Name']} found from {cust['City']}. Pre-approved limit: ₹{cust['PreApprovedLimit(₹)']}, Credit Score: {cust['CreditScore']}."
            if cust['CreditScore'] < 700:
                response += " Unfortunately, your credit score is below 700, so this loan may be declined."
            else:
                response += " You are eligible for quick approval. Please upload your salary slip (simulated)."
        else:
            response = "Sorry, I couldn't find that Customer ID."
    elif "upload" in prompt.lower():
        response = "Salary slip uploaded successfully ✅. Loan approved! Generating sanction letter..."
    else:
        response = "I'm here to guide you through Tata Capital personal loans. Try asking about 'loan offers'."

    add_message("assistant", response)
    st.chat_message("assistant").markdown(response)
