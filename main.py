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
    print("⚠️ Using PRO Fallback Content (Long & Formatted)")
    
    if topic_type == "Bio":
        return f"""
        <h2>Introduction</h2>
        <p>{title} has taken the internet by storm. Known for her captivating performances and stunning looks, she has carved a niche for herself in the adult entertainment industry. From her early beginnings to becoming a top-searched star, her journey is nothing short of fascinating. Fans around the world are always eager to know more about her life, career, and personal details.</p>
        <p>In this detailed biography, we will explore everything you need to know about {title}, including her age, height, figure, and net worth.</p>
        
        <h2>Personal Details</h2>
        <table style="width:100%; border-collapse: collapse; margin: 20px 0; border: 1px solid #333;">
            <tr style="background-color: #222; color: #fff;">
                <th style="padding: 10px; border: 1px solid #444;">Attribute</th>
                <th style="padding: 10px; border: 1px solid #444;">Details</th>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #444;"><strong>Name</strong></td>
                <td style="padding: 10px; border: 1px solid #444;">{title}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #444;"><strong>Profession</strong></td>
                <td style="padding: 10px; border: 1px solid #444;">Actress & Model</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #444;"><strong>Nationality</strong></td>
                <td style="padding: 10px; border: 1px solid #444;">International</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #444;"><strong>Popularity</strong></td>
                <td style="padding: 10px; border: 1px solid #444;">Trending</td>
            </tr>
        </table>

        <h2>Early Life & Background</h2>
        <p>{title} was born with a passion for the camera. While specific details about her early childhood are kept private, it is known that she always aspired to be in the limelight. Growing up, she was active in various extracurricular activities which helped build her confidence.</p>
        <p>She entered the industry at a young age and quickly learned the ropes. Her dedication and hard work made her stand out from the crowd. Unlike many others, she focused on building a unique brand that resonated with her audience.</p>

        <h2>Career Journey</h2>
        <p>The rise of {title} in the industry has been meteoric. Her debut scene grabbed attention immediately, showcasing her natural talent and screen presence. Directors and producers were quick to notice her potential, leading to contracts with major studios.</p>
        <p>Over the years, she has worked with some of the biggest names in the business. Her versatility allows her to perform in various genres, making her a fan favorite. Whether it's a glamorous photoshoot or a high-production video, {title} gives her 100%.</p>
        <p>Social media has also played a huge role in her success. With millions of followers across platforms like Instagram and Twitter, she keeps her fans engaged with behind-the-scenes content and updates.</p>

        <h2>Why She is So Popular</h2>
        <p>There are several reasons why {title} remains a top trend:</p>
        <ul>
            <li><strong>Consistency:</strong> She regularly releases high-quality content.</li>
            <li><strong>Engagement:</strong> She interacts with her fanbase frequently.</li>
            <li><strong>Looks:</strong> Her distinct style and fitness regime keep her looking her best.</li>
        </ul>

        <h2>Conclusion</h2>
        <p>{title} is undoubtedly a star to watch out for. Her journey from a newcomer to a sensation is inspiring. As she continues to evolve, fans can expect even more exciting projects from her in the future. Don't forget to check out her exclusive video collection linked below.</p>
        """
    else: # News
        return f"""
        <h2>Breaking News: {title}</h2>
        <p>The internet is buzzing today with the latest viral sensation involving <strong>{title}</strong>. Social media platforms like Twitter, Reddit, and Instagram are flooded with reactions as fans and critics alike discuss the unfolding events. This story has quickly become one of the top trending topics of the day.</p>
        
        <h2>The Viral Clip: What Happened?</h2>
        <p>It all started when a video clip surfaced online, purportedly showing {title} in a candid moment. Within hours, the clip was shared thousands of times. The nature of the content has sparked intense debate, with some claiming it to be a publicity stunt while others believe it to be a genuine leak.</p>
        <p>Experts suggest that the rapid spread of this video highlights the power of social media algorithms in amplifying controversial content. The video quality suggests it was taken recently, adding to the speculation.</p>

        <h2>Public Reactions</h2>
        <p>The reaction from the public has been mixed. Here is what people are saying:</p>
        <ul>
            <li><strong>Fans:</strong> Many die-hard fans are supporting {title}, asking for privacy and respect.</li>
            <li><strong>Critics:</strong> Others are questioning the authenticity of the clip.</li>
            <li><strong>Memers:</strong> As always, the internet has turned parts of the incident into memes, further fueling the trend.</li>
        </ul>
        <p>Hashtags related to {title} are currently trending in multiple countries, showing the global impact of this news.</p>

        <h2>Impact on Social Media</h2>
        <p>This incident has once again brought up the discussion about digital privacy and the speed at which information travels. For influencers and celebrities, maintaining a private life is becoming increasingly difficult in the digital age.</p>

        <h2>Conclusion</h2>
        <p>As the story develops, more details are expected to emerge. Whether this will have a long-term impact on {title}'s career remains to be seen. Stay tuned to our website for the latest updates on this story and other viral news.</p>
        """

def get_ai_content(prompt, topic_type="Bio", title="Unknown"):
    # PLAN A: OpenRouter
    print("🤖 Phase 1: Trying OpenRouter...")
    for model_name in OPENROUTER_MODELS:
        try:
            # Added system prompt to enforce HTML structure
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are an expert entertainment writer. Output strictly valid HTML. Use <h2> for headings. Use <table> for stats. Write at least 800 words."},
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
        # Check if already exists
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
            print("⚠️ stars.txt missing or empty. Using Default List.")
            stars = ["Sunny Leone", "Mia Khalifa", "Dani Daniels", "Riley Reid", "Abella Danger", "Lana Rhoades"]
        
        star = random.choice(stars)
        print(f"⭐ Processing Bio: {star}")
        
        star_image = get_image_from_ddg(f"{star} model wallpaper")
        model_button = create_model_button(star, star_image)

        # Improved Prompt for AI
        prompt = f"""
        Write a comprehensive HTML biography (at least 800 words) for the adult star "{star}".
        
        REQUIRED STRUCTURE (Use strictly HTML tags):
        1. <h2>Introduction</h2>: A long catchy intro about her fame.
        2. <h2>Personal Details</h2>: A HTML Table <table> with rows for Name, Age (Approx), Nationality, Profession, and Figure. Style the table with border="1".
        3. <h2>Early Life</h2>: Detailed childhood and background.
        4. <h2>Career Journey</h2>: How she started and became famous.
        5. <h2>Why She is Popular</h2>: Bullet points <ul> about her style.
        6. <h2>Conclusion</h2>: Final thoughts.
        
        Do not output markdown code blocks. Output raw HTML only.
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
            Write a sensational 800-word news article about "{topic}".
            Output strictly valid HTML.
            Structure:
            - <h2>Breaking Story</h2>
            - <h2>Details of the Viral Event</h2>
            - <h2>Social Media Reactions</h2> (Use bullet points)
            - <h2>Expert Opinion</h2>
            - <h2>Conclusion</h2>
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
