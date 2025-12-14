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

# --- TARGET WEBSITES (Source for News) ---
TARGET_SITES = [
    "avn.com",
    "pornstars.tube",
    "redbled.com",
    "thelordofporn.com",
    "erotom.com",
    "frolicme.com",
    "eroticatale.com",
    "sexwithemily.com",
    "erikalust.com"
]

# --- GUARANTEED WORKING IMAGES ---
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
        <p>{title} has taken the internet by storm. Known for her captivating performances and stunning looks, she has carved a niche for herself in the adult entertainment industry. From her early beginnings to becoming a top-searched star, her journey is nothing short of fascinating. Fans around the world are always eager to know more about her life, career, and personal details.</p>
        
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
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Movies</strong></td><td style="padding:10px; border:1px solid #444;">Various Web Scenes</td></tr>
        </table>

        <h2>Early Life & Background</h2>
        <p>{title} was born with a passion for the camera. While specific details about her early childhood are kept private, it is known that she always aspired to be in the limelight. Growing up, she was active in various extracurricular activities which helped build her confidence.</p>
        <p>She entered the industry at a young age and quickly learned the ropes. Her dedication and hard work made her stand out from the crowd.</p>

        <h2>Career Journey</h2>
        <p>The rise of {title} in the industry has been meteoric. Her debut scene grabbed attention immediately, showcasing her natural talent and screen presence. Directors and producers were quick to notice her potential, leading to contracts with major studios.</p>
        <p>She has worked with some of the most prestigious production houses in the industry. Her ability to adapt to different roles and genres sets her apart.</p>

        <h2>Conclusion</h2>
        <p>{title} is undoubtedly a star to watch out for. Her journey from a newcomer to a sensation is inspiring for many. Don't forget to check out her exclusive video collection linked below.</p>
        """
    else: # News Fallback
        return f"""
        <h2>Breaking News: {title}</h2>
        <p>The internet is buzzing today with the latest viral sensation involving <strong>{title}</strong>. Private videos often leak on platforms like Telegram, Reddit, and Twitter, causing a massive storm on social media.</p>
        
        <h2>The Viral Clip: What Happened?</h2>
        <p>It all started when a video clip surfaced online. Within hours, the clip was shared thousands of times. The nature of the content has sparked intense debate, with many users searching for the original link.</p>

        <h2>Analysis: The Dark Side of the Web</h2>
        <p>This incident sheds light on the dark side of the internet. Private content, once leaked, is almost impossible to remove completely.</p>

        <h2>Conclusion</h2>
        <p>As the story develops, more details are expected to emerge. Stay tuned to our website for the latest updates.</p>
        """

def get_ai_content(prompt, topic_type="Bio", title="Unknown"):
    print("🤖 Phase 1: Trying OpenRouter...")
    for model_name in OPENROUTER_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a professional adult industry writer. Write 2000-WORD detailed content. Use <h2> headings and <table> for stats."},
                    {"role": "user", "content": prompt}
                ],
                timeout=45
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
        
        star_image = get_guaranteed_image(f"{star} model wallpaper", type="Bio")
        model_button = create_model_button(star, star_image)

        # 2000 WORDS PROMPT - UPDATED TABLE INSTRUCTIONS
        prompt = f"""
        Write a massive, 2000-WORD detailed HTML biography for the adult star "{star}".
        
        REQUIRED HTML STRUCTURE:
        1. <h2>Introduction</h2>
        2. <h2>Personal Details</h2>: A DETAILED HTML Table <table> with rows: 
           - Real Name, Profession, Date of Birth, Birth Place, Nationality, 
           - Religion, Height, Languages, Debut Year, Popular Movies/TV Shows. 
           (Style with border="1")
        3. <h2>Early Life</h2> (Write 500 words)
        4. <h2>Career Journey</h2> (Write 800 words)
        5. <h2>Social Media & Fame</h2>
        6. <h2>Conclusion</h2>
        
        Output raw HTML only.
        """
        content = get_ai_content(prompt, "Bio", star)
        
        if content:
            content = inject_internal_links(content)
            final_content = content + model_button
            slug = f"{star.lower().replace(' ', '-')}-biography"
            save_to_firebase(f"{star}: Porn Star Biography & Videos", final_content, slug, "Bio", star_image)
    except Exception as e:
        print(f"Bio Error: {e}")

def post_article():
    try:
        # 1. Pick a random site from your list
        source_site = random.choice(TARGET_SITES)
        
        # 2. Search specific site for trends
        query = f"site:{source_site} latest news"
        print(f"🔍 Searching Trending Topic from: {source_site}...")
        
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
                "New Viral Trend: Private Videos Leaking on Twitter"
            ]
            topic = random.choice(backup_topics)

        img = get_guaranteed_image("Breaking News Viral Scandal", type="News")
            
        # 2000 WORDS PROMPT FOR NEWS
        prompt = f"""
        Write an investigative, deep-dive 2000-WORD news article about "{topic}".
        Source inspiration: {source_site}
        
        INSTRUCTIONS:
        - Analyze the incident in extreme detail (Who, What, Where).
        - Discuss digital privacy and internet security.
        - Include 'Expert Opinions' and 'Social Media Reactions'.
        
        STRUCTURE:
        - <h2>Breaking Story</h2>
        - <h2>The Viral Event in Detail</h2>
        - <h2>Public Outrage & Reactions</h2>
        - <h2>Analysis</h2>
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
