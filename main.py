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

# --- MODEL LIST ---
FREE_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-pro-1.5:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen-2-7b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free"
]

# --- SETUP ---
cred_dict = json.loads(os.environ.get("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_dict)
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)
db = firestore.client()

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

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
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=1, safesearch='off'))
            if results:
                return results[0]['image']
    except Exception as e:
        print(f"❌ Image Error: {e}")
    return random.choice(FALLBACK_IMAGES)

def inject_internal_links(html_content):
    modified_content = html_content
    for word, link in KEYWORD_LINKS.items():
        pattern = re.compile(fr'(?<!href=")(?<!>)\b{re.escape(word)}\b', re.IGNORECASE)
        replacement = f'<a href="{link}" style="color:#e50914; font-weight:bold;">{word}</a>'
        modified_content = pattern.sub(replacement, modified_content)
    return modified_content

def get_ai_content(prompt):
    for model_name in FREE_MODELS:
        try:
            print(f"🤖 Trying AI Model: {model_name}...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                timeout=50 # Increased timeout for long articles
            )
            content = response.choices[0].message.content
            if content:
                return content
        except Exception as e:
            print(f"⚠️ {model_name} Failed. Trying next...")
            time.sleep(2)
            continue 
            
    print("❌ All AI Models failed.")
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
                "coverImageUrl": image,  # <--- FIXED: Ye naam 'coverImageUrl' hona chahiye
                "thumbnail": image       # Backup ke liye thumbnail bhi rakh diya
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

        # UPDATED: Very Long Prompt
        prompt = f"""
        Write a VERY LONG, DETAILED, and SEO-optimized HTML biography (at least 1000 words) for the adult star "{star}".
        
        Use the following structure strictly (Output HTML ONLY, no <html>/<body> tags):
        
        1. <h2>Introduction</h2> (Write 2 long paragraphs about who she is, her popularity, and impact).
        2. <table> (Include: Name, Date of Birth, Age, Birthplace, Height, Weight, Figure/Measurements, Nationality, Active Years).
        3. <h2>Early Life & Background</h2> (Explain where she grew up, education, and life before the industry).
        4. <h2>Career Journey</h2> (How she started, first scene, famous studios, awards, and career growth. Make this very detailed).
        5. <h2>Personal Life & Relationships</h2> (Boyfriends, hobbies, interests outside work).
        6. <h2>Social Media & Fan Following</h2> (Talk about her Instagram, Twitter/X presence).
        7. <h2>Interesting Facts</h2> (Bullet points of 5-6 fun facts about her).
        8. <h2>Conclusion</h2>
        
        Make sure the tone is engaging and professional. Use paragraphs, not just lists.
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
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=1))
            if results:
                topic = results[0]['title']
                print(f"🔥 Found Trending Topic: {topic}")

        if topic:
            img = get_image_from_ddg(topic)
            
            # UPDATED: Long Article Prompt
            prompt = f"""
            Write a detailed, 800-word SEO news article about "{topic}".
            Focus on keywords: Viral Video, Leaked MMS, Desi Scandal, Social Media reaction.
            Structure:
            - <h2>Breaking News</h2> (What happened?)
            - <h2>Why it went Viral?</h2>
            - <h2>Public Reaction</h2>
            - <h2>Safety Tips</h2>
            Output valid HTML only.
            """
            content = get_ai_content(prompt)
            
            if content:
                content = inject_internal_links(content)
                slug = topic.lower().replace(" ", "-").replace(":", "")[:60]
                save_to_firebase(topic, content, slug, "News", img)
    except Exception as e:
        print(f"Article Error: {e}")

if __name__ == "__main__":
    post_biography()
    print("⏳ Waiting 10 seconds...")
    time.sleep(10)
    post_article()
