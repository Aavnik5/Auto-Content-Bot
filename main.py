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

# --- GUARANTEED BACKUP TOPICS (Agar search fail ho jaye) ---
BACKUP_NEWS_TITLES = [
    "Viral Scandal: Famous Influencer Private Video Leaked on Telegram",
    "College Girl MMS Goes Viral: Social Media in Shock",
    "OnlyFans Model Account Hacked: Full Folder Leaked Online",
    "Desi Bhabhi Viral Video: WhatsApp Groups Flooded with Link",
    "Big Boss Contestant MMS Scandal: Truth Behind the Viral Clip",
    "Bathroom Video Leak: New Scandal Shakes the Internet",
    "Gym Trainer and Student Private Video Leaked on Twitter",
    "TikTok Star Oops Moment: Live Stream Goes Wrong",
    "Telegram Group 'Desi Viral' Exposed: Thousands of Videos Leaked",
    "Hotel Room Spy Cam Scandal: Couple Video Goes Viral",
    "Bollywood Actress Deepfake vs Real Video: Internet Confused",
    "Instagram Model Private DM Video Leaked by Ex-Boyfriend",
    "Hostel Girl MMS Viral: Police Investigating the Source",
    "Reality Show Star Private Tape Leaked on Reddit",
    "Famous YouTuber Private Call Recording and Video Leaked"
]

# --- GUARANTEED WORKING IMAGES ---
BIO_IMAGES_LIST = [
    "https://i.ebayimg.com/images/g/MKgAAOSwsLtVe5GY/s-l400.jpg",

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
    try:
        with DDGS(timeout=5) as ddgs:
            results = list(ddgs.images(query, max_results=1, safesearch='off'))
            if results and 'image' in results[0] and results[0]['image']:
                print("✅ Live Image Found!")
                return results[0]['image']
    except Exception as e:
        print(f"⚠️ Search Failed ({e}). Switching to Backup.")

    print("🚀 Using GUARANTEED HD Image.")
    if type == "Bio":
        return random.choice(BIO_IMAGES_LIST)
    else:
        return random.choice(NEWS_IMAGES_LIST)

def get_star_stats(star_name):
    query = f"{star_name} height weight bra size measurements wiki bio"
    print(f"📊 Searching Stats for: {star_name}...")
    try:
        with DDGS(timeout=10) as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                stats_data = "\n".join([r['body'] for r in results])
                print("✅ Stats Found!")
                return stats_data
    except Exception as e:
        print(f"⚠️ Stats Search Failed: {e}")
    return "Data not found online. Estimate based on typical model stats."

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
    print("⚠️ Using PRO Fallback Content (Long Version)")
    
    if topic_type == "Bio":
        return f"""
        <h2>Introduction to the Star</h2>
        <p>{title} has taken the internet by storm. Known for her captivating performances...</p>
        
        <h2>Personal Details</h2>
        <table border="1" style="width:100%; border-collapse: collapse;">
            <tr><td><strong>Name</strong></td><td>{title}</td></tr>
            <tr><td><strong>Profession</strong></td><td>Adult Actress</td></tr>
        </table>
        
        <h3>Physical Appearance</h3>
        <table border="1" style="width:100%; border-collapse: collapse;">
            <tr><td><strong>Height</strong></td><td>5 ft 5 in</td></tr>
            <tr><td><strong>Weight</strong></td><td>55 kg</td></tr>
        </table>

        <h2>Conclusion</h2>
        <p>Don't forget to check out her exclusive video collection linked below.</p>
        """
    else: 
        return f"""
        <h2>Breaking News: {title}</h2>
        <p>The internet is buzzing today with the latest viral sensation involving <strong>{title}</strong>. Private videos often leak on platforms like Telegram, Reddit, and Twitter, causing a massive storm on social media. This recent incident has once again highlighted the issues of digital privacy and internet security.</p>
        
        <h2>The Viral Clip: What Exactly Happened?</h2>
        <p>It all started when a video clip surfaced online late last night. Within hours, the clip was shared thousands of times across various social media groups and channels. The nature of the content has sparked intense debate, with many users searching for the original link.</p>

        <h2>Analysis: The Dark Side of the Web</h2>
        <p>This incident sheds light on the dark side of the internet. Private content, once leaked, is almost impossible to remove completely.</p>

        <h2>Conclusion</h2>
        <p>As the story develops, more details are expected to emerge regarding the source of the leak.</p>
        """

def get_ai_content(prompt, topic_type="Bio", title="Unknown"):
    print("🤖 Phase 1: Trying OpenRouter...")
    for model_name in OPENROUTER_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a professional long-form content writer. Write EXTREMELY DETAILED, 2000-WORD content. Do not stop early. Use <h2> headings and <table> for stats."},
                    {"role": "user", "content": prompt}
                ],
                timeout=55
            )
            content = response.choices[0].message.content
            if content and len(content) > 1000:
                print("✅ OpenRouter Success!")
                return content
        except Exception:
            pass 
    
    print("🚨 Phase 1 Failed. Switching to Google Gemini REST...")
    google_models = ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro"]
    
    for gm in google_models:
        print(f"   👉 Trying {gm}...")
        content = generate_gemini_rest(prompt, gm)
        if content and len(content) > 1000:
            print(f"✅ Google Gemini ({gm}) Success!")
            return content.replace("```html", "").replace("```", "")

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
        
        stats_data = get_star_stats(star)
        star_image = get_guaranteed_image(f"{star} model wallpaper", type="Bio")
        model_button = create_model_button(star, star_image)

        prompt = f"""
        Write a massive, 2000-WORD detailed HTML biography for the adult star "{star}".
        
        HERE IS REAL DATA FOUND ONLINE FOR "{star}":
        {stats_data}
        
        REQUIRED HTML STRUCTURE:
        1. <h2>Introduction</h2>
        2. <h2>Personal Details</h2>: A DETAILED HTML Table <table> with rows:
           - Real Name, Profession, Date of Birth, Birth Place, Grew Up In, Nationality, Religion, Ethnicity, Current City, Debut Year, Notable Movies.
           (Style with border="1")
        
        3. <h2>Physical Appearance</h2>: A SECOND HTML Table <table>. Use the REAL DATA provided above:
           - Height, Weight, Bra Size, Body Measurements, Waist Size, Hip Size, Shoe Size, Dress Size, Hair Color, Eye Color.
           (Style with border="1")
           
        4. <h2>Early Life</h2> (Write 500 words)
        5. <h2>Career Journey</h2> (Write 800 words)
        6. <h2>Social Media & Fame</h2>
        7. <h2>Conclusion</h2>
        
        Output raw HTML only.
        """
        content = get_ai_content(prompt, "Bio", star)
        
        if content:
            content = inject_internal_links(content)
            final_content = content + model_button
            slug = f"{star.lower().replace(' ', '-')}-biography"
            save_to_firebase(f"{star}: Porn Star Biography & Video", final_content, slug, "Bio", star_image)
    except Exception as e:
        print(f"Bio Error: {e}")

def post_article():
    try:
        # Search queries
        search_terms = ["site:avn.com news", "latest leaked mms viral"]
        query = random.choice(search_terms)
        
        print(f"🔍 Searching Trending Topic for: {query}...")
        topic = None
        
        # Try finding a topic
        try:
            with DDGS(timeout=10) as ddgs:
                results = list(ddgs.text(query, region='in-en', max_results=1)) 
                if results:
                    topic = results[0]['title']
                    print(f"🔥 Found Trending Topic: {topic}")
        except Exception:
            pass

        # === CRITICAL FIX: GUARANTEED TOPIC SELECTION ===
        if not topic:
            print("⚠️ Search failed/empty. Using GUARANTEED BACKUP TOPIC.")
            topic = random.choice(BACKUP_NEWS_TITLES)
            print(f"✅ Selected Backup Topic: {topic}")

        img = get_guaranteed_image("Breaking News Viral Scandal", type="News")
            
        # 2000 WORDS PROMPT FOR NEWS
        prompt = f"""
        Write an investigative, deep-dive 2000-WORD news article about "{topic}".
        
        INSTRUCTIONS FOR LENGTH:
        - Analyze the incident in extreme detail (Who, What, Where).
        - Discuss the broader issue of digital privacy and internet security.
        - Include fictional 'Expert Opinions' and 'Cyber Security Analysis'.
        - Describe social media reactions in depth.
        
        STRUCTURE:
        - <h2>Breaking Story</h2>
        - <h2>The Viral Event in Detail</h2>
        - <h2>Public Outrage & Reactions</h2>
        - <h2>Cyber Security Expert Analysis</h2>
        - <h2>Conclusion</h2>
        
        Output strictly valid HTML.
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
