import streamlit as st
import pandas as pd
import random
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import requests

# ----------------------------
# Config
# ----------------------------
DATA_FILE = "TataCapital_200_customers.csv"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # set in env or Streamlit secrets
DEFAULT_MODEL = "openai/gpt-4o-mini"  # can switch to "anthropic/claude-3-sonnet" or "meta-llama/llama-3-8b-instruct"

# ----------------------------
# Load Dataset
# ----------------------------
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "CustomerID","Name","Age","City","Employment",
        "Salary","EMI","CreditScore","PreApprovedLimit(₹)"
    ])

# ----------------------------
# OpenRouter LLM API
# ----------------------------
def llm_response(user_query, model=DEFAULT_MODEL):
    """Fallback to LLM via OpenRouter"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:8501",   # replace with your hosted app URL
            "X-Title": "TataCapital Loan Chatbot"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful Tata Capital personal loan assistant. Be polite, concise, and explain loans clearly."},
                {"role": "user", "content": user_query}
            ]
        }
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"(LLM error: {e})"

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("💬 Tata Capital - Personal Loan Chatbot")

# Select model (user can switch)
model_choice = st.sidebar.selectbox(
    "Choose LLM Model",
    ["openai/gpt-4o-mini", "openai/gpt-4o", "anthropic/claude-3-sonnet", "meta-llama/llama-3-8b-instruct"]
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "new_customer" not in st.session_state:
    st.session_state.new_customer = None

def add_message(sender, text):
    st.session_state.messages.append({"sender": sender, "text": text})

# Display chat history
for m in st.session_state.messages:
    st.chat_message(m["sender"]).markdown(m["text"])

# ----------------------------
# Helper: Generate sanction letter PDF
# ----------------------------
def generate_sanction_letter(name, amount, tenure, emi):
    file_name = f"Sanction_Letter_{name}.pdf"
    c = canvas.Canvas(file_name, pagesize=letter)
    c.drawString(100, 750, "Tata Capital - Loan Sanction Letter")
    c.drawString(100, 700, f"Dear {name},")
    c.drawString(100, 670, f"We are pleased to sanction your loan of ₹{amount}.")
    c.drawString(100, 640, f"Tenure: {tenure} months")
    c.drawString(100, 610, f"Monthly EMI: ₹{emi}")
    c.drawString(100, 580, "Congratulations and thank you for choosing Tata Capital!")
    c.save()
    return file_name

# ----------------------------
# Chat Input
# ----------------------------
if prompt := st.chat_input("Ask about a personal loan..."):
    add_message("user", prompt)
    st.chat_message("user").markdown(prompt)

    response = ""

    # Step 1: Loan intent
    if "loan" in prompt.lower():
        response = "Sure, I can help with that. Can I know your Customer ID to check pre-approved offers?"

    # Step 2: CustomerID check
    elif prompt.startswith("C"):
        if prompt in df["CustomerID"].values:
            cust = df[df["CustomerID"] == prompt].iloc[0]
            response = f"Customer {cust['Name']} found from {cust['City']}. Pre-approved limit: ₹{cust['PreApprovedLimit(₹)']}, Credit Score: {cust['CreditScore']}."
            if cust['CreditScore'] < 700:
                response += " Unfortunately, your credit score is below 700, so this loan may be declined."
            else:
                response += " You are eligible for quick approval. Please upload your salary slip (simulated)."
        else:
            # New customer onboarding
            st.session_state.new_customer = {"CustomerID": prompt}
            response = "It looks like you are a new customer. Please provide your details below."

            with st.form("new_customer_form"):
                name = st.text_input("Full Name")
                age = st.number_input("Age", 18, 70)
                city = st.text_input("City")
                employment = st.selectbox("Employment Type", ["Salaried","Self-Employed"])
                salary = st.number_input("Monthly Salary (₹)", 10000, 500000)
                emi = st.number_input("Existing EMI (₹)", 0, 200000)
                kyc = st.file_uploader("Upload KYC Document")
                slip = st.file_uploader("Upload Salary Slip")
                submitted = st.form_submit_button("Submit")

                if submitted:
                    # Mock credit score
                    credit_score = random.randint(650,850)
                    pre_limit = 1.5 * salary

                    new_row = {
                        "CustomerID": prompt,
                        "Name": name,
                        "Age": age,
                        "City": city,
                        "Employment": employment,
                        "Salary": salary,
                        "EMI": emi,
                        "CreditScore": credit_score,
                        "PreApprovedLimit(₹)": pre_limit
                    }

                    df.loc[len(df)] = new_row
                    df.to_csv(DATA_FILE, index=False)

                    response = f"Thank you {name}! Your profile has been created. Assigned Credit Score: {credit_score}. Pre-approved limit: ₹{pre_limit}."
                    response += " Please upload your salary slip to proceed."

    # Step 3: Salary Slip Upload
    elif "upload" in prompt.lower() or "salary slip" in prompt.lower():
        # Example underwriting
        loan_amount = 200000
        tenure = 24
        salary = 50000
        emi = 9500

        if loan_amount <= 1.5 * salary and emi <= 0.5 * salary:
            decision = "Approved ✅"
            response = f"Salary slip uploaded successfully. Loan {decision}! Generating sanction letter..."
            file_name = generate_sanction_letter("Customer", loan_amount, tenure, emi)
            st.success("Sanction letter generated.")
            with open(file_name, "rb") as f:
                st.download_button("📄 Download Sanction Letter", f, file_name)
        else:
            response = "Based on underwriting rules, your loan is not approved automatically. It will be sent for manual review."

    else:
        # Fallback → OpenRouter LLM
        response = llm_response(prompt, model_choice)

    add_message("assistant", response)
    st.chat_message("assistant").markdown(response)
