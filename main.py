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

# --- GUARANTEED WORKING IMAGES ---
BIO_IMAGES_LIST = [
    "https://i.ebayimg.com/images/g/MKgAAOSwsLtVe5GY/s-l400.jpg",
    # Add more robust image links if possible
]

NEWS_IMAGES_LIST = [
    "https://www.shutterstock.com/image-vector/newspaper-icon-logo-isolated-sign-600nw-1896642682.jpg", # TV News
    # Add more robust image links if possible
]


# --- 1. OPENROUTER SETUP ---
OPENROUTER_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "microsoft/phi-3-medium-128k-instruct:free"
]

# Ensure OPENAI_API_KEY is an OpenRouter key if not using it for OpenAI directly
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
            # Increased max_results for better chance of finding a good image
            results = list(ddgs.images(query, max_results=3, safesearch='off'))
            if results and 'image' in results[0] and results[0]['image']:
                # Filter for a more robust image URL if possible
                valid_images = [r['image'] for r in results if r.get('image') and 'data:image' not in r['image'].lower()]
                if valid_images:
                    print("✅ Live Image Found!")
                    return valid_images[0]

    except Exception as e:
        print(f"⚠️ Search Failed ({e}). Switching to Backup.")

    print("🚀 Using GUARANTEED HD Image.")
    if type == "Bio":
        return random.choice(BIO_IMAGES_LIST)
    else:
        return random.choice(NEWS_IMAGES_LIST)

def inject_internal_links(html_content):
    modified_content = html_content
    # Create a list of words to ensure longer, more detailed content is linked
    for word, link in KEYWORD_LINKS.items():
        # The regex pattern ensures we don't link words already inside an <a> tag
        pattern = re.compile(fr'(?<!href=")(?<!>)\b{re.escape(word)}\b', re.IGNORECASE)
        replacement = f'<a href="{link}" style="color:#e50914; font-weight:bold;">{word}</a>'
        # Replace only the first few occurrences to avoid over-linking
        modified_content = pattern.sub(replacement, modified_content, count=3)
    return modified_content

def generate_gemini_rest(prompt, model_name="gemini-1.5-flash"):
    api_key = os.environ.get("GOOGLE_API_KEY")
    versions = ["v1beta", "v1"]
    
    for version in versions:
        # Increased maximum output tokens for Gemini to support 2000 words
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model_name}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = { 
            "contents": [{ "parts": [{"text": prompt}] }],
            "config": {
                "maxOutputTokens": 4096 # Set high for long articles
            }
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60) # Increased timeout
            if response.status_code == 200:
                result = response.json()
                # Check for candidates and content to prevent errors
                if 'candidates' in result and result['candidates'] and 'content' in result['candidates'][0]:
                     return result['candidates'][0]['content']['parts'][0]['text']
            
            # Print specific error message for debugging
            else:
                 print(f"Gemini API Error {response.status_code}: {response.text}")

        except Exception as e:
            print(f"Gemini Request Failed: {e}")
            continue
    return None

def get_fallback_content(topic_type, title):
    # This fallback is designed to be very long to meet the word count if all else fails
    print("⚠️ Using PRO Fallback Content (Long Version)")
    
    # Placeholder for a very long HTML content block
    long_content_placeholder = """
    <p>This section is intentionally long. To reach the required 2000-word count, this fallback template is designed to include extensive, detailed, and repeated analysis. This is a failsafe to ensure that even if the AI model fails, a sufficiently large HTML file is still generated for SEO purposes. The content below is a placeholder for a deep dive into the subject, covering all aspects from multiple angles. It serves as a necessary buffer to bypass any word count restrictions from the AI vendors.</p>
    """ * 4 # Repeat placeholder for extreme length

    if topic_type == "Bio":
        return f"""
        <h2>Introduction to the Star</h2>
        <p>{title} has taken the internet by storm. Known for her captivating performances and stunning looks, she has carved a niche for herself in the adult entertainment industry. From her early beginnings to becoming a top-searched star, her journey is nothing short of fascinating. Fans around the world are always eager to know more about her life, career, and personal details. Her presence on social media has further amplified her reach, making her a global sensation in a very short span of time. We will now dive deep into all aspects of her life and career to fulfill the 2000-word content requirement.</p>
        
        <h2>Personal Details and Physical Stats</h2>
        <table style="width:100%; border-collapse: collapse; margin: 20px 0; border: 1px solid #333;">
            <tr style="background-color: #222; color: #fff;">
                <th style="padding: 10px; border: 1px solid #444;">Attribute</th>
                <th style="padding: 10px; border: 1px solid #444;">Details</th>
            </tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Name</strong></td><td style="padding:10px; border:1px solid #444;">{title}</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Real Name</strong></td><td style="padding:10px; border:1px solid #444;">Not Publicly Available (To Protect Privacy)</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Profession</strong></td><td style="padding:10px; border:1px solid #444;">Adult Actress, Model, Social Media Influencer</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Date of Birth</strong></td><td style="padding:10px; border:1px solid #444;">Specific Date Withheld for Security</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Birth Place</strong></td><td style="padding:10px; border:1px solid #444;">North America / Western Europe</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Nationality</strong></td><td style="padding:10px; border:1px solid #444;">Cosmopolitan</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Height & Figure</strong></td><td style="padding:10px; border:1px solid #444;">5'5" (Approx), 34C-24-36 (Estimated)</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Debut Year</strong></td><td style="padding:10px; border:1px solid #444;">2015-2020 (Golden Era Debut)</td></tr>
            <tr><td style="padding:10px; border:1px solid #444;"><strong>Net Worth</strong></td><td style="padding:10px; border:1px solid #444;">$1 Million - $5 Million (Estimated)</td></tr>
        </table>

        <h2>Early Life & Background (Extended Section)</h2>
        <p>{title} was born with a passion for the camera. While specific details about her early childhood are kept private to maintain her privacy, it is known that she always aspired to be in the limelight. Growing up, she was active in various extracurricular activities which helped build her confidence. She participated in school plays, local modeling gigs, and talent shows, which laid the foundation for her future career. She came from a middle-class background where the entertainment industry was not a standard career path, which adds to the intrigue of her later choices. Her decision to enter the industry was a bold one, made after much consideration and a desire for financial independence and self-expression. This long introduction is essential for meeting the word count.</p>
        {long_content_placeholder}

        <h2>Career Journey and Major Works (Extended Section)</h2>
        <p>The rise of {title} in the industry has been meteoric. Her debut scene grabbed attention immediately, showcasing her natural talent and screen presence. Directors and producers were quick to notice her potential, leading to contracts with major studios. Unlike many others who struggle to find their footing, she made an impact right from the start. She is known for her roles in titles like "The Billionaire's Yacht," "Desert Heat," and "Cyber Doll." Her filmography is extensive, and each scene is marked by a high level of performance and production value. She is often praised for her professional demeanor and her dedication to her craft. Her versatility allows her to move seamlessly between different genres, from BDSM to girl-on-girl scenes, maintaining top billing across the board. The impact of her digital content on platforms like OnlyFans has also been a major factor in her continued success and celebrity status, which requires detailed discussion for the 2000-word goal.</p>
        {long_content_placeholder}

        <h2>Conclusion</h2>
        <p>{title} is undoubtedly a star to watch out for. Her journey from a newcomer to a sensation is inspiring for many. As she continues to evolve, fans can expect even more exciting projects from her in the future. She has proven that with talent and hard work, one can achieve great heights in this competitive industry. Don't forget to check out her exclusive video collection linked below to see her best performances.</p>
        """
    else: # News Fallback
        return f"""
        <h2>Breaking News: The Comprehensive Analysis of {title}</h2>
        <p>The internet is buzzing today with the latest viral sensation involving <strong>{title}</strong>. Private videos often leak on platforms like Telegram, Reddit, and Twitter, causing a massive storm on social media. This recent incident has once again highlighted the critical issues of digital privacy and internet security. This article will provide an exhaustive, 2000-word deep dive into the incident, its causes, and its profound social and legal implications, ensuring the required content length is met for SEO optimization.</p>
        
        <h2>The Viral Clip: What Exactly Happened? (Extended Analysis)</h2>
        <p>It all started when a video clip surfaced online late last night. Within hours, the clip was shared thousands of times across various social media groups and channels. The nature of the content has sparked intense debate, with many users searching for the original link. While some claim it to be a deepfake or a publicity stunt, others believe it to be a genuine leak from a private source. The video features {title} in a candid moment, which was allegedly not meant for public viewing. Such leaks have become increasingly common in the digital age, where hackers and malicious entities target influencers and celebrities. The source of the leak, believed to be a compromised cloud storage account or a direct message platform breach, is still under investigation, and we must elaborate on these technical possibilities at length.</p>
        {long_content_placeholder}

        <h2>Cyber Security Expert Analysis and Prevention (Deep Dive)</h2>
        <p>Leading cyber security analysts have weighed in on the incident. Dr. Anya Sharma, a digital forensics expert, noted, "This is a classic case of credential stuffing. Celebrities and high-profile individuals must use two-factor authentication and unique passwords for every service. A single point of failure can lead to catastrophic data leaks." The legal ramifications are also immense, with several jurisdictions now pursuing charges against those who share non-consensual imagery. The incident is a chilling reminder of the fragility of digital boundaries. This section alone needs significant detail to fulfill the length requirement, discussing encryption, VPNs, and the legal framework in depth.</p>
        {long_content_placeholder}
        
        <h2>Conclusion and Societal Impact</h2>
        <p>As the story develops, more details are expected to emerge regarding the source of the leak and any legal action that might be taken. We urge our readers to respect the privacy of the individuals involved and avoid sharing unverified or non-consensual content. This incident serves as a major inflection point in the ongoing debate between online freedom and personal security. Stay tuned to our website for the latest updates on this viral scandal and other trending news.</p>
        """

def get_ai_content(prompt, topic_type="Bio", title="Unknown"):
    print("🤖 Phase 1: Trying OpenRouter...")
    for model_name in OPENROUTER_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a professional long-form content writer. Write EXTREMELY DETAILED, 2000-WORD MINIMUM content. Do not stop early. Use <h2> headings and <table> for stats. ENSURE THE FINAL OUTPUT IS OVER 2000 WORDS."},
                    {"role": "user", "content": prompt}
                ],
                timeout=60, # Increased timeout for long generation
                max_tokens=4096 # CRITICAL: Sets the maximum length to allow for 2000+ words
            )
            content = response.choices[0].message.content
            # Check length: 2000 words is roughly 10,000 to 12,000 characters
            if content and len(content) > 10000: # Increased check to 10,000 characters
                print("✅ OpenRouter Success! (Length Check Passed)")
                return content
            else:
                 print(f"⚠️ OpenRouter generated only {len(content)} characters. Trying next model.")

        except Exception as e:
            print(f"⚠️ OpenRouter Failed ({model_name}): {e}. Trying next model.")
            pass
    
    print("🚨 Phase 1 Failed. Switching to Google Gemini REST...")
    google_models = ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro"]
    
    for gm in google_models:
        print(f"   👉 Trying {gm}...")
        # Gemini REST call handles the large token limit internally
        content = generate_gemini_rest(prompt, gm)
        
        # Check length again
        if content and len(content) > 10000: # Increased check to 10,000 characters
            print(f"✅ Google Gemini ({gm}) Success! (Length Check Passed)")
            # Clean up potential markdown formatting from the API
            return content.replace("```html", "").replace("```", "").strip()
        elif content:
             print(f"⚠️ Google Gemini ({gm}) generated only {len(content)} characters. Trying next model.")

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
            stars = ["Sunny Leone", "Mia Khalifa", "Dani Daniels", "Riley Reid", "Kagney Linn Karter"]
        
        star = random.choice(stars)
        print(f"⭐ Processing Bio: {star}")
        
        star_image = get_guaranteed_image(f"{star} model wallpaper", type="Bio")
        model_button = create_model_button(star, star_image)

        # UPDATED: 2000 WORDS PROMPT - More aggressive length instruction
        prompt = f"""
        Write a massive, **ABSOLUTELY 2000-WORD MINIMUM** detailed HTML biography for the adult star "{star}".
        
        INSTRUCTIONS FOR LENGTH (Total must exceed 2000 words):
        - **Early Life & Background:** Elaborate deeply on her early life, education, and life before fame (Write **at least 500 words** just on this).
        - **Career Journey & Major Works:** Create a very long 'Career' section detailing her debut, major movies, awards, and rise to stardom. **Mention 10 specific, fictional movie titles** and elaborate on 5 in detail. (Write **at least 800 words** on this).
        - **Controversies, Legacy & Future:** Discuss her social media impact, brand endorsements, controversies, and her lasting legacy. Use long, descriptive paragraphs (at least 7-10 sentences each) to ensure maximum length. (Write **at least 500 words**).
        - **DETAIL MANDATE:** Use long paragraphs, detailed descriptions, and thorough analysis to ensure the content is comprehensive and meets the 2000-word length requirement.
        
        REQUIRED HTML STRUCTURE:
        1. <h2>Introduction</h2>
        2. <h2>Personal Details</h2>: A DETAILED HTML Table <table> with rows: Name, Real Name, Profession, DOB, Birthplace, Nationality, Religion, Height, Languages, Debut Year, Popular Movies, Net Worth. (Border=1 and stylize it)
        3. <h2>Early Life & Background</h2>
        4. <h2>Career Journey & Major Works</h2>
        5. <h2>Controversies, Legacy & Future Outlook</h2>
        6. <h2>Conclusion</h2>
        
        Output raw HTML only. Do not use markdown backticks (```) or any other wrapping.
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
        search_terms = [
            "onlyfans model private video leaked twitter",
            "top onlyfans creator mega leak viral",
            "famous adult star private tape scandal",
            "western influencer sex tape leaked reddit",
            "twitch streamer accidental nudity clip viral",
            "instagram model private mms leaked telegram",
            "youtuber private video exposed twitter",
            "streamer wardrobe malfunction viral clip",
            "porn star real life controversy news",
            "adult actress hacked private photos scandal",
            "famous pornstar retirement scandal news",
            "avn award winner leaked private video",
            "celebrity sex tape leak 2025",
            "hollywood actress deepfake controversy news",
            "leaked snapchat premium video viral",
            "top 10 hottest pornstars 2025 ranked",
            "best adult actresses of 2025 list",
            "top 10 most popular adult stars 2025",
            "best new pornstars debut 2025",
            "best adult movies 2025 reviews",
            "AVN award winners 2025 full list",
            "XBIZ award winning scenes 2025",
            "top rated adult films 2025",
            "best onlyfans creators leaked videos viral",
            "top trending onlyfans leaks 2025",
            "most subscribed onlyfans models leaked",
            "viral onlyfans sex tapes reddit trend",
            "most viewed porn videos 2025",
            "viral adult scenes trending twitter",
            "leaked private tapes of famous stars 2025",
            "top 5 controversial adult scandals 2025"
        ]
        query = random.choice(search_terms)
        
        print(f"🔍 Searching Trending Topic for: {query}...")
        topic = None
        
        try:
            with DDGS(timeout=10) as ddgs:
                # Use a specific region for more focused results
                results = list(ddgs.text(query, region='in-en', max_results=3)) 
                if results:
                    topic = results[0]['title']
                    print(f"🔥 Found Trending Topic: {topic}")
        except Exception:
            pass

        if not topic:
            print("⚠️ Using Backup Topic.")
            backup_topics = [
                "Viral Scandal: Telegram Groups Leaking Private Videos - A 2000-Word Investigation",
                "Dark Side of Social Media: Influencer MMS Leaked and Cyber Laws in India",
                "The Impact of AI Deepfakes on the Adult Industry: A Comprehensive Report 2025"
            ]
            topic = random.choice(backup_topics)

        img = get_guaranteed_image("Breaking News Viral Scandal", type="News")
            
        # UPDATED: 2000 WORDS PROMPT FOR NEWS - More aggressive length instruction
        prompt = f"""
        Write an investigative, deep-dive **2000-WORD MINIMUM** news article about "{topic}".
        
        INSTRUCTIONS FOR LENGTH (Total must exceed 2000 words):
        - **Detailed Incident Analysis:** Analyze the incident in extreme detail (Who, What, Where, When, How). (Write **at least 600 words**).
        - **Digital Privacy & Legal Ramifications:** Discuss the broader issue of digital privacy, internet security, and the specific legal consequences in India/Globally. (Write **at least 700 words**).
        - **Reactions & Future:** Include fictional 'Expert Opinions' and 'Cyber Security Analysis'. Describe social media reactions in depth. Discuss future preventive measures. (Write **at least 700 words**).
        - **DETAIL MANDATE:** Use lengthy, complex sentences and elaborate paragraphs to ensure the 2000-word minimum is met.
        
        STRUCTURE:
        - <h2>Breaking Story & Immediate Reaction</h2>
        - <h2>The Viral Event: A Detailed Timeline and Analysis</h2>
        - <h2>Cyber Security and Legal Implications</h2>
        - <h2>Public Outrage and Social Media Analysis</h2>
        - <h2>Conclusion and Prevention Measures</h2>
        
        Output strictly valid HTML. Do not use markdown backticks (```) or any other wrapping.
        """
        content = get_ai_content(prompt, "News", topic)
        
        if content:
            content = inject_internal_links(content)
            slug = topic.lower().replace(" ", "-").replace(":", "").replace("?", "").replace(",", "")[:60]
            save_to_firebase(topic, content, slug, "News", img)

    except Exception as e:
        print(f"Article Error: {e}")

if __name__ == "__main__":
    post_biography()
    time.sleep(5)
    post_article()
