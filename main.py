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
cred_dict = json.loads(os.environ.get("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# --- 1. NEW FUNCTION: GENERATE MODEL URL ---
def create_model_button(star_name, image_url):
    # Name ko URL format me badalna (e.g. "Dani Daniels" -> "dani-daniels")
    slug = star_name.lower().strip().replace(" ", "-")
    
    # Ye wo link hai jo aapne manga
    model_url = f"https://freepornx.site/index.html?tab=video&path=models%2F{slug}"
    
    # HTML Button Design
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

# --- 2. IMAGE SEARCHER (DuckDuckGo) ---
def get_star_image(star_name):
    print(f"🔍 Searching image for: {star_name}...")
    try:
        with DDGS() as ddgs:
            # Model photoshoot search karenge achi quality ke liye
            results = list(ddgs.images(f"{star_name} model photoshoot hd", max_results=1, safesearch='off'))
            if results:
                print("✅ Image Found")
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
        response = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct:free",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e: return None

def save_to_firebase(title, content, slug, tag, image):
    doc_ref = db.collection("articles").document(slug)
    if not doc_ref.get().exists:
        data = {
            "title": title, "content": content, "slug": slug,
            "createdAt": datetime.datetime.now(), "tags": [tag],
            "views": random.randint(100, 1000), "thumbnail": image
        }
        doc_ref.set(data)
        print(f"🚀 Published: {title}")
    else: print("⚠️ Exists, Skipping.")

# --- TASKS ---
def post_biography():
    # Stars list se naam uthayega
    with open("stars.txt", "r") as f: stars = [s.strip() for s in f.readlines() if s.strip()]
    star = random.choice(stars)
    print(f"⭐ Processing Bio: {star}")
    
    # 1. Image Search
    star_image = get_star_image(star)
    
    # 2. Button Create (Model URL wala)
    model_button_html = create_model_button(star, star_image)

    # 3. AI Bio Write
    prompt = f"""
    Write a HTML biography of adult star "{star}". 
    Use <h2> for headings and <p> for text.
    Include a <table> for stats (Age, Height, Nationality). 
    Do NOT include <html>, <head>, or <body> tags.
    """
    content = get_ai_content(prompt)
    
    if content:
        content = inject_internal_links(content)
        
        # Article = Bio Text + Model Button
        final_content = content + model_button_html
        
        save_to_firebase(
            title=f"{star}: Biography, Wiki & All Videos (2025)", 
            content=final_content, 
            slug=f"{star}-bio".lower().replace(' ', '-'), 
            tag="Bio", 
            image=star_image
        )

def post_article():
    with open("sites.txt", "r") as f: sites = [s.strip() for s in f.readlines() if s.strip()]
    url = random.choice(sites)
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        img = get_page_image(soup)
        topics = [h.text.strip() for h in soup.find_all(['h1', 'h2']) if len(h.text.strip()) > 15]
        if topics:
            topic = random.choice(topics)
            print(f"📝 Writing Article: {topic}")
            prompt = f"Write a SEO HTML blog post about '{topic}'. Use keywords Viral, MMS. No <html> tags."
            content = get_ai_content(prompt)
            if content:
                content = inject_internal_links(content)
                save_to_firebase(topic, content, topic.lower().replace(" ", "-")[:50], "News", img)
    except: pass

if __name__ == "__main__":
    post_biography()
    post_article()