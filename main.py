import os
import random
import datetime
import requests
import re
from bs4 import BeautifulSoup
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

# --- SETUP ---
# Firebase Credentials Load
cred_dict = json.loads(os.environ.get("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

# AI Setup
client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# --- 1. NEW FUNCTION: MODEL URL GENERATOR ---
def create_model_button(star_name, image_url):
    # Name ko URL Slug banao (e.g. "Sunny Leone" -> "sunny-leone")
    slug = star_name.lower().strip().replace(" ", "-")
    
    # Direct Model Page URL
    model_url = f"https://freepornx.site/index.html?tab=video&path=models%2F{slug}"
    
    # Button Design
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

# --- 2. IMAGE SEARCHER ---
def get_star_image(star_name):
    print(f"🔍 Searching image for: {star_name}...")
    try:
        with DDGS() as ddgs:
            # 2-3 keywords try karenge taaki result pakka mile
            queries = [f"{star_name} model photoshoot hd", f"{star_name} wallpaper"]
            for q in queries:
                results = list(ddgs.images(q, max_results=1, safesearch='off'))
                if results:
                    return results[0]['image']
    except Exception as e:
        print(f"❌ Image Error: {e}")
    return random.choice(FALLBACK_IMAGES)

# --- 3. HELPER FUNCTIONS ---
def inject_internal_links(html_content):
    modified_content = html_content
    for word, link in KEYWORD_LINKS.items():
        pattern = re.compile(fr'(?<!href=")(?<!>)\b{re.escape(word)}\b', re.IGNORECASE)
        replacement = f'<a href="{link}" style="color:#e50914; font-weight:bold;">{word}</a>'
        modified_content = pattern.sub(replacement, modified_content)
    return modified_content

def get_page_image(soup):
    try:
        img = soup.find("meta", property="og:image")
        if img and img.get("content"): return img["content"]
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"): return img_tag["src"]
    except: pass
    return random.choice(FALLBACK_IMAGES)

def get_ai_content(prompt):
    try:
        # Google ka free model use kar rahe hain jo fast hai
        response = client.chat.completions.create(
            model="google/gemma-2-9b-it:free",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def save_to_firebase(title, content, slug, tag, image):
    try:
        doc_ref = db.collection("articles").document(slug)
        if not doc_ref.get().exists:
            data = {
                "title": title, "content": content, "slug": slug,
                "createdAt": datetime.datetime.now(), "tags": [tag],
                "views": random.randint(100, 1000), "thumbnail": image
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
        
        # 1. Image
        star_image = get_star_image(star)
        
        # 2. Button
        model_button = create_model_button(star, star_image)

        # 3. Content
        prompt = f"""
        Write a detailed HTML biography of adult star "{star}".
        Structure:
        - <h2>Introduction</h2>
        - <table> with rows for: Age, Height, Nationality, Figure.
        - <h2>Career & Early Life</h2>
        - <h2>Why She is Famous</h2>
        Output HTML ONLY. No <html> or <body> tags.
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
        with open("sites.txt", "r") as f: sites = [s.strip() for s in f.readlines() if s.strip()]
        if not sites: return

        url = random.choice(sites)
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        img = get_page_image(soup)
        topics = [h.text.strip() for h in soup.find_all(['h1', 'h2']) if len(h.text.strip()) > 15]
        
        if topics:
            topic = random.choice(topics)
            print(f"📝 Writing Article: {topic}")
            
            prompt = f"Write a SEO friendly HTML blog post about '{topic}'. Use tags like Viral, MMS, Leaked. No <html> tags."
            content = get_ai_content(prompt)
            
            if content:
                content = inject_internal_links(content)
                slug = topic.lower().replace(" ", "-")[:60]
                save_to_firebase(topic, content, slug, "News", img)
    except Exception as e:
        print(f"Article Error: {e}")

if __name__ == "__main__":
    post_biography()
    time.sleep(2) # Thoda wait taki server crash na ho
    post_article()
