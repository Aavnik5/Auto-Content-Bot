import os
import random
import datetime
import requests
import re
import firebase_admin
from firebase_admin import credentials, firestore
from openai import OpenAI
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

def debug_list_google_models():
    """Ask Google which models are actually available for this Key"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("📋 Available Google Models for this Key:")
            for m in models:
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    print(f"   - {m['name']}")
        else:
            print(f"⚠️ Could not list models. Status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Debug Error: {e}")

def generate_gemini_rest(prompt, model_name="gemini-1.5-flash"):
    api_key = os.environ.get("GOOGLE_API_KEY")
    # Trying stable v1 first, then v1beta
    versions = ["v1beta", "v1"]
    
    for version in versions:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model_name}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = { "contents": [{ "parts": [{"text": prompt}] }] }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            continue # Try next version silently
            
    return None

def get_fallback_content(topic_type, title):
    """If AI fails completely, use this pre-written template so script doesn't crash."""
    print("⚠️ Using Generic Fallback Content (AI Failed)")
    
    if topic_type == "Bio":
        return f"""
        <h2>Introduction</h2>
        <p>{title} is a trending social media personality and adult film star who has gained immense popularity recently.</p>
        <h2>Career</h2>
        <p>She started her career in the entertainment industry and quickly rose to fame due to her stunning looks and performances.</p>
        <h2>Popularity</h2>
        <p>Her videos often go viral on social media platforms like Instagram and Twitter.</p>
        <h2>Conclusion</h2>
        <p>Watch her exclusive collection using the link below.</p>
        """
    else: # News
        return f"""
        <h2>Breaking News: {title}</h2>
        <p>A new video related to <strong>{title}</strong> has gone viral on social media today.</p>
        <h2>The Viral Clip</h2>
        <p>The video is being shared widely on WhatsApp, Reddit, and Twitter. Fans are reacting with shock and surprise.</p>
        <h2>Public Reaction</h2>
        <p>Many users are searching for the full video link. It has become a top trending topic on Google Trends.</p>
        <h2>Conclusion</h2>
        <p>Stay tuned for more updates on this story.</p>
        """

def get_ai_content(prompt, topic_type="Bio", title="Unknown"):
    # 1. Debug: Check models once
    # debug_list_google_models() # Uncomment if you want to see list in logs

    # PLAN A: OpenRouter
    print("🤖 Phase 1: Trying OpenRouter...")
    for model_name in OPENROUTER_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                timeout=20
            )
            content = response.choices[0].message.content
            if content and len(content) > 100:
                print("✅ OpenRouter Success!")
                return content
        except Exception:
            pass 
    
    # PLAN B: Google Gemini REST
    print("🚨 Phase 1 Failed. Switching to Google Gemini REST...")
    # List of models to brute force
    google_models = ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro"]
    
    for gm in google_models:
        print(f"   👉 Trying {gm}...")
        content = generate_gemini_rest(prompt, gm)
        if content:
            print(f"✅ Google Gemini ({gm}) Success!")
            return content.replace("```html", "").replace("```", "")

    # PLAN C: FINAL FALLBACK (Prevent Crash)
    print("❌ All AI Models Failed. Using Fallback Template.")
    return get_fallback_content(topic_type, title)

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
        Write a detailed HTML biography (800 words) for "{star}".
        Structure: Intro, Stats Table, Early Life, Career, Conclusion.
        Output ONLY HTML.
        """
        content = get_ai_content(prompt, "Bio", star)
        
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
        
        try:
            with DDGS(timeout=20) as ddgs:
                results = list(ddgs.text(query, region='in-en', max_results=1)) 
                if results:
                    topic = results[0]['title']
                    print(f"🔥 Found Trending Topic: {topic}")
        except Exception:
            pass

        if not topic:
            print("⚠️ Using Backup Topic.")
            backup_topics = [
                "Why Leaked MMS Videos Go Viral on Social Media?",
                "Dark Side of Internet: How Private Videos Get Leaked",
                "Top 5 Controversial Bollywood Moments of This Year",
                "Safety Tips: How to Protect Your Private Videos from Leaks"
            ]
            topic = random.choice(backup_topics)

        if topic:
            img = get_image_from_ddg(topic)
            prompt = f"""
            Write a 800-word juicy article about "{topic}".
            Focus on viral trends. Output ONLY HTML.
            """
            content = get_ai_content(prompt, "News", topic)
            
            if content:
                content = inject_internal_links(content)
                slug = topic.lower().replace(" ", "-").replace(":", "").replace("?", "")[:60]
                save_to_firebase(topic, content, slug, "News", img)

    except Exception as e:
        print(f"Article Error: {e}")

if __name__ == "__main__":
    post_biography()
    time.sleep(5)
    post_article()
