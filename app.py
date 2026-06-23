import streamlit as st
import litellm
import json
import os

# পেজ কনফিগারেশন
st.set_page_config(page_title="Super AI Platform", page_icon="🚀", layout="wide")

# সেশন স্টেট ইনিশিয়ালাইজেশন
if "custom_instructions" not in st.session_state:
    st.session_state.custom_instructions = "You are a highly intelligent assistant. Respond accurately."

if "messages" not in st.session_state:
    st.session_state.messages = []

# মডেল এবং তাদের API Key ম্যাপিং (সবচেয়ে গুরুত্বপূর্ণ অংশ)
# এখানে মডেলের নাম এবং কোন এনভায়রনমেন্ট ভ্যারিয়েবল থেকে কী নেবে তা ডিফাইন করা হয়েছে
MODEL_CONFIG = {
    "Claude 4.8 opuse": {
        "model": "claude-4.8-opuse 20240307", 
        "api_key_env": "ANTHROPIC_API_KEY"
    },
    "DeepSeek Chat": {
        "model": "deepseek V4 pro thinking",
        "api_key_env": "DEEPSEEK_API_KEY"
    },
   "GLM-5.2": {
        "model": "openrouter/thudm/glm-5.2", 
        "api_key_env": "OPENROUTER_API_KEY"    },
    "GPT-5.5 Mini (OpenRouter)": {
        "model": "openrouter/openai/gpt-5.5-mini", 
        "api_key_env": "OPENROUTER_API_KEY"
    }
}

# সাইডবার ডিজাইন
with st.sidebar:
    st.title("⚙️ সেটিংস")
    
    # মডেল সিলেক্ট ড্রপডাউন
    selected_model_name = st.selectbox("মডেল সিলেক্ট করুন", list(MODEL_CONFIG.keys()))
    
    # কাস্টম ইনস্ট্রাকশন
    custom_inst = st.text_area("কাস্টম ইনস্ট্রাকশন", value=st.session_state.custom_instructions, height=120)
    st.session_state.custom_instructions = custom_inst
    
    st.divider()
    
    # চ্যাট হিস্ট্রি ম্যানেজমেন্ট
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ হিস্ট্রি মুছুন"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        # হিস্ট্রি ডাউনলোড বাটন (যেহেতু ক্লাউডে সেভ থাকে না, তাই ব্যাকআপ নেওয়ার জন্য)
        if st.session_state.messages:
            chat_json = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)
            st.download_button("📥 হিস্ট্রি সেভ", chat_json, "chat_history.json", "application/json")

    # পুরানো হিস্ট্রি আপলোড করার অপশন
    uploaded_file = st.file_uploader("📤 পুরানো হিস্ট্রি লোড করুন", type=["json"])
    if uploaded_file is not None:
        try:
            stringio = uploaded_file.read().decode("utf-8")
            st.session_state.messages = json.loads(stringio)
            st.success("হিস্ট্রি লোড হয়েছে!")
            st.rerun()
        except Exception:
            st.error("ফাইলটি সঠিক নয়।")

# মূল চ্যাট ইন্টারফেস
st.title("🚀 সুপার ইন্টেলিজেন্ট AI প্ল্যাটফর্ম")

# আগের চ্যাট দেখানো
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ইউজার ইনপুট
if prompt := st.chat_input("আপনার প্রশ্ন বা কোডিং প্রম্পট লিখুন..."):
    # ইউজার মেসেজ স্ক্রিনে দেখানো
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # API তে পাঠানোর জন্য মেসেজ ফরম্যাট
    api_messages = [{"role": "system", "content": st.session_state.custom_instructions}]
    api_messages.extend(st.session_state.messages)

    # সিলেক্টেড মডেলের কনফিগারেশন নেওয়া
    config = MODEL_CONFIG[selected_model_name]
    selected_model = config["model"]
    api_key_env = config["api_key_env"]
    
    # Streamlit Secrets থেকে নির্দিষ্ট মডেলের API Key নিয়ে আসা
    # st.secrets অটোমেটিক্যালি .streamlit/secrets.toml ফাইল বা ক্লাউড সিক্রেটস থেকে ভ্যালু পড়ে
    try:
        dynamic_api_key = st.secrets[api_key_env]
    except KeyError:
        dynamic_api_key = os.environ.get(api_key_env, "API_KEY_NOT_FOUND")

    # AI থেকে রেসপন্স আনা
    with st.chat_message("assistant"):
        with st.spinner("🧠 চিন্তা করছি..."):
            try:
                if dynamic_api_key == "API_KEY_NOT_FOUND":
                    raise Exception(f"{api_key_env} সেট করা হয়নি। অনুগ্রহ করে Secrets চেক করুন।")
                
                # Litellm দিয়ে ডাইনামিক API কল
                response = litellm.completion(
                    model=selected_model,
                    messages=api_messages,
                    api_key=dynamic_api_key
                )
                ai_response = response.choices[0].message.content
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            except Exception as e:
                st.error(f"এরর হয়েছে: {e}")
