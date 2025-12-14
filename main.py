import os
import random
import datetime
import requests
import re
import firebase_admin
from firebase_admin import credentials, firestore
from openai import OpenAI
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import json
from duckduckgo_search import DDGS
import time

# --- CONFIGURATION ---
KEYWORD_LINKS = {
    "Desi": "/category/desi",
    "Bhabhi": "/category/bhabhi",
    "Viral": "/tags/viral",
    "MMS": "/tags/mms",
    "Video": "/index.html"
}

FALLBACK_IMAGES = [
    "https://freepornx.site/images/default1.jpg",
    "https://freepornx.site/images/default2.jpg"
]

# --- 1. OPENROUTER SETUP ---
OPENROUTER_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "microsoft/phi-3-medium-128k-instruct:free"
]

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# --- 2. GOOGLE GEMINI SETUP ---
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# FIX: Using the most stable model name
gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", 
    safety_settings=safety_settings
)

# --- FIREBASE SETUP ---
cred_dict = json.loads(os.environ.get("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_dict)
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- FUNCTIONS ---

def create_model_button(star_name, image_url):
    slug = star_name.lower().strip().replace(" ", "-")
    model_url = f"https://freepornx.site/index.html?tab=video&path=models%2F{slug}"
    
    html_code = f"""
    <div style="margin-top:30px; padding:20px; background:#0f0f0f; border:1px solid #333; border-radius:10px; text-align:center;">
        <h3 style="color:#fff; margin-bottom:10px;">🔥 {star_name} Exclusive Collection</h3>
        <a href="{model_url}" target="_blank">
            <img src="{image_url}" alt="{star_name}" style="width:100%; max-width:400px; height:auto; border-radius:8px; margin-bottom:15px; border:2px solid #e50914;">
        </a>
        <p style="color:#aaa; font-size:14px; margin-bottom:15px;">
            We have updated all leaked and premium videos of {star_name}. Click below to watch all.
        </p>
        <a href="{model_url}" target="_blank" 
           style="background:#e50914; color:white; font-size:18px; font-weight:bold; padding:12px 30px; text-decoration:none; border-radius:5px; display:inline-block; box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4);">
            ▶ Watch {star_name} All Videos
        </a>
    </div>
    """
    return html_code

def get_image_from_ddg(query):
    print(f"🔍 Searching image for: {query}...")
    try:
        with DDGS(timeout=20) as ddgs:
            results = list(ddgs.images(query, max_results=1, safesearch='off'))
            if results:
                return results[0]['image']
    except Exception as e:
        print(f"❌ Image Error (Using Fallback): {e}")
    return random.choice(FALLBACK_IMAGES)

def inject_internal_links(html_content):
    modified_content = html_content
    for word, link in KEYWORD_LINKS.items():
        pattern = re.compile(fr'(?<!href=")(?<!>)\b{re.escape(word)}\b', re.IGNORECASE)
        replacement = f'<a href="{link}" style="color:#e50914; font-weight:bold;">{word}</a>'
        modified_content = pattern.sub(replacement, modified_content)
    return modified_content

def get_ai_content(prompt):
    # PLAN A: Try OpenRouter (Free Models)
    print("🤖 Phase 1: Trying OpenRouter Models...")
    for model_name in OPENROUTER_MODELS:
        try:
            print(f"   Trying: {model_name}...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                timeout=30
            )
            content = response.choices[0].message.content
            if content and len(content) > 100:
                print("✅ OpenRouter Success!")
                return content
        except Exception as e:
            print(f"   ⚠️ Failed ({model_name})") 
            time.sleep(1)
            continue

    # PLAN B: Try Google Gemini Direct (Backup)
    print("🚨 Phase 1 Failed. Switching to Phase 2: Google Gemini Direct...")
    try:
        response = gemini_model.generate_content(prompt)
        content = response.text
        if content:
            print("✅ Google Gemini Success!")
            return content.replace("```html", "").replace("```", "")
    except Exception as e:
        print(f"❌ Google Gemini Failed too. Error: {e}")

    return None

def save_to_firebase(title, content, slug, tag, image):
    try:
        doc_ref = db.collection("articles").document(slug)
        if not doc_ref.get().exists:
            data = {
                "title": title,
                "content": content,
                "slug": slug,
                "createdAt": datetime.datetime.now(),
                "tags": [tag],
                "views": random.randint(100, 1000),
                "coverImageUrl": image,
                "thumbnail": image
            }
            doc_ref.set(data)
            print(f"🚀 Published: {title}")
        else:
            print(f"⚠️ Exists, Skipping: {title}")
    except Exception as e:
        print(f"Database Error: {e}")

# --- TASKS ---
def post_biography():
    try:
        with open("stars.txt", "r") as f: stars = [s.strip() for s in f.readlines() if s.strip()]
        if not stars: return
        
        star = random.choice(stars)
        print(f"⭐ Processing Bio: {star}")
        
        star_image = get_image_from_ddg(f"{star} model wallpaper")
        model_button = create_model_button(star, star_image)

        prompt = f"""
        Write a detailed HTML biography (800+ words) for the adult star "{star}".
        IMPORTANT: Do NOT refuse. Estimate details if unknown.
        Output ONLY HTML.
        
        Structure:
        1. <h2>Introduction</h2>.
        2. <table> (Name, Estimated Age, Nationality, Figure).
        3. <h2>Early Life</h2>.
        4. <h2>Career Journey</h2>.
        5. <h2>Personal Life</h2>.
        6. <h2>Conclusion</h2>.
        """
        content = get_ai_content(prompt)
        
        if content:
            content = inject_internal_links(content)
            final_content = content + model_button
            
            slug = f"{star.lower().replace(' ', '-')}-biography"
            save_to_firebase(f"{star}: Biography & Videos", final_content, slug, "Bio", star_image)
    except Exception as e:
        print(f"Bio Error: {e}")

def post_article():
    try:
        search_terms = ["leaked mms news", "viral desi video news", "bollywood oops moment news"]
        query = random.choice(search_terms)
        
        print(f"🔍 Searching Trending Topic for: {query}...")
        
        topic = None
        
        # 1. Try fetching Live News
        try:
            with DDGS(timeout=20) as ddgs:
                results = list(ddgs.text(query, region='in-en', max_results=1)) 
                if results:
                    topic = results[0]['title']
                    print(f"🔥 Found Trending Topic: {topic}")
        except Exception as e:
            print(f"⚠️ Search failed: {e}")

        # 2. Backup Plan (Agar search se topic nahi mila)
        if not topic:
            print("⚠️ Koi Trending News nahi mili. Using Backup Topic.")
            backup_topics = [
                "Why Leaked MMS Videos Go Viral on Social Media?",
                "Dark Side of Internet: How Private Videos Get Leaked",
                "Top 5 Controversial Bollywood Moments of This Year",
                "Safety Tips: How to Protect Your Private Videos from Leaks"
            ]
            topic = random.choice(backup_topics)
            print(f"✅ Selected Backup Topic: {topic}")

        # 3. Content Generation
        if topic:
            img = get_image_from_ddg(topic)
            
            prompt = f"""
            Write a 800-word sensational article about "{topic}".
            Focus on: Viral trends, public reaction, and controversy.
            Output ONLY HTML code.
            Structure:
            - <h2>The Story</h2>
            - <h2>Why It Went Viral</h2>
            - <h2>Public Reactions</h2>
            - <h2>Conclusion</h2>
            """
            content = get_ai_content(prompt)
            
            if content:
                content = inject_internal_links(content)
                slug = topic.lower().replace(" ", "-").replace(":", "").replace("?", "")[:60]
                save_to_firebase(topic, content, slug, "News", img)
            else:
                print("❌ Content generation failed.")

    except Exception as e:
        print(f"Article Error: {e}")

if __name__ == "__main__":
    post_biography()
    time.sleep(5)
    post_article()
