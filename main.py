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
    "Video": "/index.html",
    "Leaked": "/tags/leaked",
    "Scandal": "/tags/scandal"
}

# --- GUARANTEED WORKING IMAGES (Direct Unsplash Links) ---
BIO_IMAGES_LIST = [

    

    "https://ih1.redbubble.net/image.5328373552.3326/st,small,507x507-pad,600x600,f8f8f8.u3.webp",

]

NEWS_IMAGES_LIST = [
    "https://www.shutterstock.com/image-vector/newspaper-icon-logo-isolated-sign-600nw-1896642682.jpg", # TV News
   
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

def get_guaranteed_image(query, type="Bio"):
    print(f"🔍 Searching image for: {query}...")
    
    # 1. Try DuckDuckGo
    try:
        with DDGS(timeout=5) as ddgs:
            results = list(ddgs.images(query, max_results=1, safesearch='off'))
            if results and 'image' in results[0] and results[0]['image']:
                print("✅ Live Image Found!")
                return results[0]['image']
    except Exception as e:
        print(f"⚠️ Search Failed ({e}). Switching to Backup.")

    # 2. FAILSAFE: Return Guaranteed Image
    print("🚀 Using GUARANTEED HD Image from List.")
    if type == "Bio":
        return random.choice(BIO_IMAGES_LIST)
    else:
        return random.choice(NEWS_IMAGES_LIST)

def inject_internal_links(html_content):
    modified_content = html_content
    for word, link in KEYWORD_LINKS.items():
        pattern = re.compile(fr'(?<!href=")(?<!>)\b{re.escape(word)}\b', re.IGNORECASE)
        replacement = f'<a href="{link}" style="color:#e50914; font-weight:bold;">{word}</a>'
        modified_content = pattern.sub(replacement, modified_content)
    return modified_content

def generate_gemini_rest(prompt, model_name="gemini-1.5-flash"):
    api_key = os.environ.get("GOOGLE_API_KEY")
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
            continue
    return None

def get_fallback_content(topic_type, title):
    print("⚠️ Using PRO Fallback Content")
    
    if topic_type == "Bio":
        # Updated Fallback Table with all details
        return f"""
        <h2>Introduction</h2>
        <p>{title} has taken the internet by storm. Known for her captivating performances and stunning looks, she has carved a niche for herself in the adult entertainment industry.</p>
        
        <h2>Personal Details</h2>
        <table style="width:100%; border-collapse: collapse; margin: 20px 0; border: 1px solid #333;">
            <tr style="background-color: #222; color: #fff;">
                <th style="padding: 10px; border: 1px solid #444;">Attribute</th>
                <th style="padding: 10px; border: 1px solid #444;">Details</th>
            </tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Name</strong></td><td style="padding:10px; border:1px solid #444;">{title}</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Real Name</strong></td><td style="padding:10px; border:1px solid #444;">Not Publicly Available</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Profession</strong></td><td style="padding:10px; border:1px solid #444;">Adult Actress, Model</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Date of Birth</strong></td><td style="padding:10px; border:1px solid #444;">1990s (Approx)</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Birth Place</strong></td><td style="padding:10px; border:1px solid #444;">United States / Europe</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Nationality</strong></td><td style="padding:10px; border:1px solid #444;">International</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Religion</strong></td><td style="padding:10px; border:1px solid #444;">Christianity</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Ethnicity</strong></td><td style="padding:10px; border:1px solid #444;">Caucasian / Mixed</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Current City</strong></td><td style="padding:10px; border:1px solid #444;">Los Angeles / Miami</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Languages</strong></td><td style="padding:10px; border:1px solid #444;">English</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Debut Year</strong></td><td style="padding:10px; border:1px solid #444;">2015-2020</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Movies & TV</strong></td><td style="padding:10px; border:1px solid #444;">Various Web Scenes</td></tr>
        </table>

        <h2>Career Journey</h2>
        <p>The rise of {title} in the industry has been meteoric. Her debut scene grabbed attention immediately, showcasing her natural talent and screen presence.</p>

        <h2>Conclusion</h2>
        <p>{title} is undoubtedly a star to watch out for. Don't forget to check out her exclusive video collection linked below.</p>
        """
    else: # News Fallback
        return f"""
        <h2>Breaking News: {title}</h2>
        <p>The internet is buzzing today with the latest viral sensation involving <strong>{title}</strong>. Private videos often leak on platforms like Telegram and Twitter.</p>
        
        <h2>The Viral Clip: What Happened?</h2>
        <p>It all started when a video clip surfaced online. Within hours, the clip was shared thousands of times.</p>

        <h2>Public Reactions</h2>
        <ul>
            <li><strong>Fans:</strong> Many fans are shocked by the leaked content.</li>
            <li><strong>Search Trends:</strong> The keyword "{title}" has become a top search query.</li>
        </ul>

        <h2>Conclusion</h2>
        <p>As the story develops, more details are expected to emerge. Stay tuned to our website for the latest updates.</p>
        """

def get_ai_content(prompt, topic_type="Bio", title="Unknown"):
    # PLAN A: OpenRouter
    print("🤖 Phase 1: Trying OpenRouter...")
    for model_name in OPENROUTER_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are an expert adult entertainment biographer. Output strictly valid HTML. Create detailed tables."},
                    {"role": "user", "content": prompt}
                ],
                timeout=30
            )
            content = response.choices[0].message.content
            if content and len(content) > 500:
                print("✅ OpenRouter Success!")
                return content
        except Exception:
            pass 
    
    # PLAN B: Google Gemini REST
    print("🚨 Phase 1 Failed. Switching to Google Gemini REST...")
    google_models = ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro"]
    
    for gm in google_models:
        print(f"   👉 Trying {gm}...")
        content = generate_gemini_rest(prompt, gm)
        if content and len(content) > 500:
            print(f"✅ Google Gemini ({gm}) Success!")
            return content.replace("```html", "").replace("```", "")

    # PLAN C: FINAL FALLBACK
    print("❌ All AI Models Failed. Using PRO Fallback Template.")
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
        stars = []
        if os.path.exists("stars.txt"):
            with open("stars.txt", "r") as f: 
                stars = [s.strip() for s in f.readlines() if s.strip()]
        
        if not stars:
            print("⚠️ stars.txt missing. Using Default List.")
            stars = ["Sunny Leone", "Mia Khalifa", "Dani Daniels", "Riley Reid"]
        
        star = random.choice(stars)
        print(f"⭐ Processing Bio: {star}")
        
        # Using Guaranteed Image Function
        star_image = get_guaranteed_image(f"{star} model wallpaper", type="Bio")
        
        model_button = create_model_button(star, star_image)

        # UPDATED PROMPT FOR DETAILED TABLE
        prompt = f"""
        Write a comprehensive HTML biography (at least 800 words) for the adult star "{star}".
        
        REQUIRED STRUCTURE (Use strictly HTML tags):
        1. <h2>Introduction</h2>: A long catchy intro about her fame.
        2. <h2>Personal Details</h2>: A DETAILED HTML Table <table> with the following rows:
           - Real Name
           - Date of Birth & Age
           - Birth Place & Residence
           - Nationality & Ethnicity
           - Religion & Zodiac Sign
           - Height & Figure
           - Languages Spoken
           - Debut Year & Years Active
           - Notable Movies/TV Shows (List 3-4 popular ones)
        
        Style the table with border="1" and make it look professional.
        
        3. <h2>Early Life</h2>: Detailed childhood and background.
        4. <h2>Career Journey</h2>: How she started and became famous.
        5. <h2>Why She is Popular</h2>: Bullet points <ul> about her style.
        6. <h2>Conclusion</h2>: Final thoughts.
        
        Output raw HTML only.
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
        search_terms = [
            "latest viral leaked mms news", 
            "private video leaked scandal", 
            "influencer viral video telegram", 
            "desi girl viral mms news"
        ]
        query = random.choice(search_terms)
        
        print(f"🔍 Searching Trending Topic for: {query}...")
        topic = None
        
        try:
            with DDGS(timeout=10) as ddgs:
                results = list(ddgs.text(query, region='in-en', max_results=1)) 
                if results:
                    topic = results[0]['title']
                    print(f"🔥 Found Trending Topic: {topic}")
        except Exception:
            pass

        if not topic:
            print("⚠️ Using Backup Topic.")
            backup_topics = [
                "Viral Scandal: Telegram Groups Leaking Private Videos",
                "Dark Side of Social Media: Influencer MMS Leaked",
                "New Viral Trend: Private Videos Leaking on Twitter",
                "Safety Alert: How Private Videos Get Leaked Online"
            ]
            topic = random.choice(backup_topics)

        img = get_guaranteed_image("Breaking News Viral Scandal", type="News")
            
        prompt = f"""
        Write a sensational 800-word news article about "{topic}".
        Focus on the viral/scandal nature of the story for an adult entertainment blog.
        Output strictly valid HTML.
        Structure: Breaking Story, Details of the Viral Event, Social Media Reactions, Conclusion.
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

