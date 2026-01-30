import streamlit as st
import pandas as pd
import time
import random
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="TCET Student Library", page_icon="📚", layout="wide")

# --- 2. REAL AUTHENTICATION (CSV DATABASE) ---
USER_DB_FILE = "users.csv"

def load_users():
    if not os.path.exists(USER_DB_FILE):
        return pd.DataFrame(columns=["username", "password", "name", "mobile"])
    return pd.read_csv(USER_DB_FILE)

def save_user(username, password, name, mobile):
    users = load_users()
    if username in users['username'].values:
        return False 
    new_user = pd.DataFrame([[username, password, name, mobile]], columns=["username", "password", "name", "mobile"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_DB_FILE, index=False)
    return True

def check_login(username, password):
    users = load_users()
    if users.empty: return None
    user_record = users[(users['username'] == username) & (users['password'] == password)]
    if not user_record.empty:
        return user_record.iloc[0]['name']
    return None

# --- 3. SESSION STATE ---
if 'history' not in st.session_state: st.session_state.history = []
if 'favorites' not in st.session_state: st.session_state.favorites = []
if 'user' not in st.session_state: 
    st.session_state.user = {"logged_in": False, "name": "", "otp_active": False, "otp": 0, "temp_data": {}}

# --- 4. LOAD DATA (OPTIMIZED) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("mega_library.csv")
        df = df.drop_duplicates(subset=['Title'])
        weights = [0.70, 0.30]
        statuses = random.choices(['Available', 'On Loan'], weights=weights, k=len(df))
        df['Status'] = statuses
        df['Return_Days'] = [random.randint(1, 7) if s == 'On Loan' else 0 for s in statuses]
        return df
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("❌ 'mega_library.csv' not found!")
    st.stop()

# --- 5. CUSTOM CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #0078FF !important; color: white !important; }
    [data-testid="stChatMessage"]:nth-child(even) { background-color: #262730 !important; color: white !important; }
    [data-testid="stChatMessage"] p { color: white !important; }
    .verified-badge { background-color: #d1fae5; color: #065f46; padding: 5px 10px; border-radius: 15px; font-weight: bold; font-size: 12px; border: 1px solid #34d399; }
    .available { color: #4CAF50; font-weight: bold; background-color: rgba(76, 175, 80, 0.1); padding: 4px; border-radius: 4px;}
    .issued { color: #FF5252; font-weight: bold; background-color: rgba(255, 82, 82, 0.1); padding: 4px; border-radius: 4px;}
    [data-testid="stPopover"] { position: fixed; bottom: 30px; right: 30px; z-index: 9999; }
    [data-testid="stPopover"] > button { width: 60px; height: 60px; border-radius: 50%; background-color: #0078FF; color: white; border: none; font-size: 24px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3); }
    </style>
    """, unsafe_allow_html=True)

# --- 6. AI ENGINE (LITE VERSION FOR CLOUD) ---
@st.cache_resource
def setup_ai_engine(data_descriptions):
    """Calculates the AI Matrix once and stores it in RAM. 
    Limited to 10k to prevent 'Oh no' crash on Streamlit Cloud."""
    tfidf = TfidfVectorizer(stop_words='english')
    
    # LIMIT TO 10,000 BOOKS (RAM Safety)
    # The Search Bar still finds all 30k, but the AI math only uses 10k.
    tfidf_matrix = tfidf.fit_transform(data_descriptions.fillna('')[:10000]) 
    
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
    return tfidf, tfidf_matrix, cosine_sim

# Initialize the engine
tfidf, tfidf_matrix, cosine_sim = setup_ai_engine(df['Description'])

def get_recommendations(title):
    try:
        idx_series = pd.Series(df.index, index=df['Title']).drop_duplicates()
        if title not in idx_series: return pd.DataFrame()
        
        idx = idx_series[title]
        if isinstance(idx, pd.Series): idx = idx.iloc[0]
        
        # If the book is outside the AI's 10,000 limit, return empty to avoid errors
        if idx >= 10000:
            return pd.DataFrame()
            
        sim_scores = sorted(list(enumerate(cosine_sim[idx])), key=lambda x: x[1], reverse=True)[1:17]
        book_indices = [i[0] for i in sim_scores]
        results = df.iloc[book_indices].copy()
        results['Match_Score'] = [i[1] for i in sim_scores]
        return results
    except Exception: 
        return pd.DataFrame()

def chat_with_library(query):
    try:
        query_vec = tfidf.transform([query])
        similarity = linear_kernel(query_vec, tfidf_matrix).flatten()
        top_indices = similarity.argsort()[-3:][::-1]
        
        if similarity[top_indices[0]] < 0.1: 
            return "Try asking about Engineering, Medical, or Entrance Exams."
        
        response = f"**Top 3 picks for '{query}':**\n\n"
        for idx in top_indices:
            book = df.iloc[idx]
            status = "✅ Available" if book['Status'] == 'Available' else f"❌ On Loan (Back in {int(book['Return_Days'])} days)"
            response += f"📘 **{book['Title']}**\n_{book['Description'][:90]}..._\n**Status:** {status}\n[Read Now]({book['Link']})\n\n"
        return response
    except: 
        return "I am analyzing the library..."

# --- 7. SIDEBAR (FILTERS & PUBLIC OTP LOGIN) ---
with st.sidebar:
    st.header("🔍 Library Filters")
    all_genres = sorted(df['Genre'].unique())
    selected_genre = st.selectbox("Select Department:", ["All Departments"] + all_genres)
    st.divider()
    
    st.header("📜 Reading History")
    if len(st.session_state.history) > 0:
        with st.expander(f"Recent ({len(st.session_state.history)})", expanded=True):
            for book in reversed(st.session_state.history[-5:]): st.markdown(f"• {book}")
    else: st.caption("No books read yet.")
    st.divider()

    st.header("❤️ Saved Books")
    if len(st.session_state.favorites) > 0:
        with st.expander(f"Favorites ({len(st.session_state.favorites)})", expanded=True):
            for book in st.session_state.favorites:
                status_html = '<span class="status-read">✅ Completed</span>' if book in st.session_state.history else '<span class="status-unread">⏳ Unread</span>'
                st.markdown(f"**{book}**", unsafe_allow_html=True)
                st.markdown(status_html, unsafe_allow_html=True)
                st.markdown("---")
    else: st.caption("No favorites yet.")
    st.divider()

    # --- PUBLIC OTP AUTHENTICATION ---
    st.header("👤 Account Access")
    
    if st.session_state.user["logged_in"]:
        st.success(f"Welcome, {st.session_state.user['name']}!")
        st.markdown('<span class="verified-badge">✅ Verified Student</span>', unsafe_allow_html=True)
        if st.button("Log Out"):
            st.session_state.user = {"logged_in": False, "name": "", "otp_active": False, "otp": 0, "temp_data": {}}
            st.rerun()

    else:
        auth_mode = st.radio("Select Mode:", ["Login", "Sign Up"], horizontal=True)
        
        if auth_mode == "Login":
            with st.form("login_form"):
                user_input = st.text_input("Username")
                pass_input = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    name = check_login(user_input, pass_input)
                    if name:
                        st.session_state.user["logged_in"] = True
                        st.session_state.user["name"] = name
                        st.balloons()
                        st.rerun()
                    else: st.error("Invalid Username or Password")
        
        elif auth_mode == "Sign Up":
            # Step 1: Enter Details
            if not st.session_state.user["otp_active"]:
                st.caption("Create Account")
                new_name = st.text_input("Full Name")
                new_mobile = st.text_input("Mobile Number")
                new_user = st.text_input("Choose Username")
                new_pass = st.text_input("Choose Password", type="password")
                
                if st.button("Send OTP"):
                    if new_name and len(new_mobile) == 10 and new_user and new_pass:
                        real_otp = random.randint(1000, 9999)
                        
                        st.session_state.user["otp"] = real_otp
                        st.session_state.user["otp_active"] = True
                        st.session_state.user["temp_data"] = {
                            "name": new_name, "mobile": new_mobile, "user": new_user, "pass": new_pass
                        }
                        
                        # --- PUBLIC SIMULATION: SHOW OTP ON SCREEN ---
                        st.toast(f"📩 SMS Received: Your OTP is {real_otp}", icon="📱")
                        st.info(f"📱 [Simulation] SMS sent to {new_mobile}. OTP: **{real_otp}**")
                        
                    else:
                        st.warning("Please enter valid details (Mobile must be 10 digits).")
            
            # Step 2: Verify OTP
            else:
                st.info(f"Enter OTP sent to {st.session_state.user['temp_data']['mobile']}")
                otp_input = st.text_input("Enter 4-Digit OTP", max_chars=4)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Verify"):
                        if otp_input == str(st.session_state.user["otp"]):
                            data = st.session_state.user["temp_data"]
                            if save_user(data["user"], data["pass"], data["name"], data["mobile"]):
                                st.success("Account Created! Please Login.")
                                st.session_state.user["otp_active"] = False 
                            else:
                                st.error("Username already exists.")
                        else:
                            st.error("Wrong OTP!")
                with col_b:
                    if st.button("Cancel"):
                        st.session_state.user["otp_active"] = False
                        st.rerun()

# --- 8. MAIN UI ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try: st.image("tcet_logo.png", width=110)
    except: st.write("🎓") 
with col_title:
    st.title("TCET Student Library")
    st.markdown("### Your Gateway to Over 30,000+ Academic Resources")

if selected_genre == "All Departments": filtered_df = df
else: filtered_df = df[df['Genre'] == selected_genre]

col1, col2 = st.columns([3, 1])
with col1:
    search_options = filtered_df['Title'].values[:10000]
    selected_book = st.selectbox("Search for a Book:", search_options)
with col2:
    st.write("")
    st.write("")
    if st.button("🚀 Search", use_container_width=True):
        st.session_state.last_book = selected_book

# --- 9. RESULTS GRID ---
if 'last_book' in st.session_state:
    rec_df = get_recommendations(st.session_state.last_book)
    st.divider()
    st.subheader(f"Results for: {st.session_state.last_book}")
    
    for i in range(0, len(rec_df), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(rec_df):
                row = rec_df.iloc[i + j]
                book_title = row['Title']
                with cols[j]:
                    with st.container(border=True):
                        st.write(f"**{book_title}**")
                        if row['Status'] == 'Available': st.markdown(f'<p class="available">✅ Available</p>', unsafe_allow_html=True)
                        else: st.markdown(f'<p class="issued">❌ On Loan ({int(row["Return_Days"])} Days)</p>', unsafe_allow_html=True)
                        st.caption(f"📂 {row['Genre']}")
                        st.progress(int(row['Match_Score']*100))
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("❤️ Save", key=f"save_{i}_{j}"):
                                if book_title not in st.session_state.favorites: st.session_state.favorites.append(book_title); st.rerun()
                        with c2:
                            if st.button("✅ Read", key=f"read_{i}_{j}"):
                                if book_title not in st.session_state.history: st.session_state.history.append(book_title); st.rerun()
                        st.link_button("📖 Open", row['Link'], use_container_width=True)

# --- 10. FLOATING CHATBOT ---
with st.popover("💬", use_container_width=False):
    st.markdown("### 🤖 TCET Assistant")
    st.caption("Ask about books, availability, or syllabus!")
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if prompt := st.chat_input("Ex: Is the Physics Bible available?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Checking..."):
                time.sleep(0.5)
                response = chat_with_library(prompt)
                st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})