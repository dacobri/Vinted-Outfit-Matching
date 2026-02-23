"""
pages/2_Upload_and_Match.py — Vinted Outfit Match
Three ways to describe an item and get outfit recommendations.
"""

import streamlit as st
from PIL import Image
import os
import sys
import json
import cohere

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from matching_engine import OutfitMatcher

st.set_page_config(
    page_title="Upload & Match — Vinted",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }
html, body, [data-testid="stAppViewContainer"] { background-color: #f5f5f5; color: #1a1a1a; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }

.navbar {
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
    padding: 12px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 999;
}
.navbar-logo { font-size: 24px; font-weight: 700; color: #007782; letter-spacing: -0.5px; }
.navbar-logo span { color: #09a89e; }
.navbar-tagline { font-size: 13px; color: #888; font-weight: 400; }

.page-content { padding: 24px 32px; max-width: 1200px; margin: 0 auto; }
.section-title { font-size: 20px; font-weight: 600; color: #1a1a1a; margin-bottom: 4px; }
.section-subtitle { font-size: 13px; color: #888; margin-bottom: 24px; }

.option-card { background: #ffffff; border: 2px solid #ebebeb; border-radius: 12px; padding: 20px; cursor: pointer; transition: all 0.2s; text-align: center; height: 100%; }
.option-card:hover { border-color: #09a89e; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.option-card-active { border-color: #007782 !important; background: #f0f9f9 !important; }
.option-icon { font-size: 32px; margin-bottom: 8px; }
.option-title { font-size: 15px; font-weight: 600; color: #1a1a1a; }
.option-desc { font-size: 12px; color: #888; margin-top: 4px; }

.form-card { background: #ffffff; border: 1px solid #ebebeb; border-radius: 16px; padding: 28px; margin-top: 20px; }

.match-card { background: #ffffff; border-radius: 12px; border: 1px solid #ebebeb; overflow: hidden; transition: all 0.2s ease; }
.match-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); border-color: #09a89e; transform: translateY(-2px); }
.match-card-body { padding: 10px 12px 14px; }
.match-why { font-size: 11px; color: #09a89e; font-weight: 500; margin-top: 4px; line-height: 1.4; }
.same-seller-banner { background: #e8f5f4; border-top: 1px solid #b2dfdb; padding: 5px 12px; font-size: 11px; color: #007782; font-weight: 600; }

.item-card-badge { display: inline-block; font-size: 10px; padding: 2px 7px; border-radius: 20px; margin-top: 6px; font-weight: 500; }
.badge-new      { background: #e8f5e9; color: #2e7d32; }
.badge-likenew  { background: #e3f2fd; color: #1565c0; }
.badge-good     { background: #fff8e1; color: #f57f17; }
.badge-fair     { background: #fce4ec; color: #c62828; }

.stButton > button { background-color: #007782 !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 14px !important; padding: 10px 20px !important; }
.stButton > button:hover { background-color: #09a89e !important; }

hr { border-color: #ebebeb !important; margin: 24px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
ARTICLE_TYPES = sorted([
    "Tshirts", "Shirts", "Casual Shoes", "Watches", "Sports Shoes",
    "Kurtas", "Tops", "Handbags", "Heels", "Sunglasses", "Wallets",
    "Flip Flops", "Sandals", "Belts", "Backpacks", "Socks",
    "Formal Shoes", "Jeans", "Shorts", "Trousers", "Jackets",
    "Sweaters", "Sweatshirts", "Blazers", "Dresses", "Skirts",
    "Leggings", "Track Pants", "Sports Sandals", "Capris",
    "Earrings", "Necklace and Chains", "Bracelet", "Scarves", "Caps",
])
COLOURS    = sorted(["Black", "White", "Blue", "Brown", "Grey", "Red", "Green", "Pink", "Navy Blue", "Purple", "Silver", "Yellow", "Beige", "Gold", "Maroon", "Orange", "Olive", "Multi", "Cream"])
OCCASIONS  = ["Casual", "Formal", "Sports", "Ethnic", "Smart Casual", "Party", "Travel"]
SEASONS    = ["Summer", "Fall", "Winter", "Spring"]
GENDERS    = ["Men", "Women", "Unisex"]
CONDITIONS = ["New", "Like new", "Good", "Fair"]

COHERE_API_KEY = st.secrets.get("COHERE_API_KEY", os.getenv("COHERE_API_KEY", ""))
IMAGE_DIR = "data/images"

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading catalog...")
def load_matcher():
    return OutfitMatcher()

def get_catalog_image(item_id):
    path = os.path.join(IMAGE_DIR, f"{int(item_id)}.jpg")
    if os.path.exists(path):
        try:
            return Image.open(path)
        except Exception:
            return None
    return None

def condition_badge(cond):
    mapping = {
        "New":      ("badge-new",     "🟢 New"),
        "Like new": ("badge-likenew", "🔵 Like new"),
        "Good":     ("badge-good",    "🟡 Good"),
        "Fair":     ("badge-fair",    "🟠 Fair"),
    }
    cls, label = mapping.get(cond, ("badge-good", cond))
    return f'<span class="item-card-badge {cls}">{label}</span>'

def navbar():
    st.markdown("""
    <div class="navbar">
        <div>
            <div class="navbar-logo">vinted <span>✦ outfit match</span></div>
            <div class="navbar-tagline">AI-powered styling for second-hand fashion</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns([6, 1])
    with col1:
        pass
    with col2:
        st.page_link("app.py", label="🏠 Browse")
        st.page_link("pages/2_Upload_and_Match.py", label="📸 Upload & Match")

def parse_with_cohere(description: str) -> dict:
    if not COHERE_API_KEY:
        raise RuntimeError("COHERE_API_KEY is not set. Add it to Streamlit secrets or an environment variable.")
    client = cohere.ClientV2(api_key=COHERE_API_KEY)
    prompt = f"""You are a fashion item classifier. Extract clothing attributes from this description.

Description: "{description}"

Return ONLY a JSON object with exactly these keys (no explanation, no markdown, just JSON):
{{
  "articleType": one of {ARTICLE_TYPES},
  "baseColour": one of {COLOURS},
  "usage": one of {OCCASIONS},
  "season": one of {SEASONS},
  "gender": one of {GENDERS}
}}

If unsure about a field, pick the closest match from the allowed values. Never return null."""

    response = client.chat(
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def show_results(item_desc: dict, uploaded_image=None):
    matcher = load_matcher()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Your item + outfit matches</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Items from our catalog that pair well with what you described</div>', unsafe_allow_html=True)

    left, right = st.columns([1, 2])
    with left:
        if uploaded_image:
            st.image(uploaded_image, width="stretch")
        else:
            st.markdown('<div style="background:#f0f0f0;border-radius:12px;height:220px;display:flex;align-items:center;justify-content:center;font-size:60px;">👕</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div style="font-size:20px;font-weight:700;margin-bottom:12px;">Your item</div>', unsafe_allow_html=True)
        tags_html = ""
        for val in [item_desc.get("articleType"), item_desc.get("baseColour"),
                    item_desc.get("gender"), item_desc.get("usage"), item_desc.get("season")]:
            if val:
                tags_html += f'<span style="display:inline-block;background:#f0f9f9;color:#007782;border:1px solid #b2dfdb;border-radius:20px;font-size:12px;padding:3px 10px;margin:2px;font-weight:500;">{val}</span>'
        st.markdown(tags_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    df = matcher.df
    candidates = df.copy()
    if item_desc.get("gender") and item_desc["gender"] != "Unisex":
        gender_compat = {"Men": ["Men", "Unisex"], "Women": ["Women", "Unisex"]}
        candidates = candidates[candidates["gender"].isin(
            gender_compat.get(item_desc["gender"], [item_desc["gender"], "Unisex"])
        )]
    if item_desc.get("articleType"):
        type_match = candidates[candidates["articleType"] == item_desc["articleType"]]
        if len(type_match) > 0:
            candidates = type_match

    if len(candidates) == 0:
        st.warning("No items found matching your description. Try adjusting the fields.")
        return

    if item_desc.get("baseColour"):
        colour_match = candidates[candidates["baseColour"] == item_desc["baseColour"]]
        if len(colour_match) > 0:
            candidates = colour_match

    seed_row = candidates.sample(1, random_state=42).iloc[0]
    seed_id = seed_row["id"]

    tab1, tab2 = st.tabs(["✨ Match with", "👗 Build complete outfit"])

    with tab1:
        st.markdown('<div style="font-size:16px;font-weight:600;margin-bottom:4px;">Items that match well with this</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;color:#888;margin-bottom:20px;">Based on colour harmony, occasion, and style compatibility</div>', unsafe_allow_html=True)

        with st.spinner("Finding matches..."):
            matches = matcher.get_matches(seed_id, num_matches=6)

        if not matches:
            st.info("No matches found. Try a different item type.")
        else:
            cols = st.columns(3)
            for i, match in enumerate(matches):
                with cols[i % 3]:
                    match_img = get_catalog_image(match["id"])
                    same_seller = match["seller"] == seed_row["seller"]
                    st.markdown('<div class="match-card">', unsafe_allow_html=True)
                    if match_img:
                        st.image(match_img, width="stretch")
                    else:
                        st.markdown('<div style="background:#f0f0f0;height:160px;display:flex;align-items:center;justify-content:center;font-size:40px;">👚</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="match-card-body">
                        <div style="font-size:16px;font-weight:700;">€{match['price']}</div>
                        <div style="font-size:12px;color:#555;margin-top:2px;">{match['name'][:45]}</div>
                        <div class="match-why">✦ {match['explanation']}</div>
                        {condition_badge(match['condition'])}
                    </div>
                    """, unsafe_allow_html=True)
                    if same_seller:
                        st.markdown('<div class="same-seller-banner">📦 Same seller — bundle & save!</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div style="font-size:16px;font-weight:600;margin-bottom:4px;">Complete outfit built around your item</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;color:#888;margin-bottom:20px;">One piece per role — top, bottom, shoes, and accessory</div>', unsafe_allow_html=True)

        with st.spinner("Building your outfit..."):
            bundle = matcher.get_outfit_bundle(seed_id, num_items=4)

        if not bundle:
            st.info("Could not build a full outfit for this item type.")
        else:
            total_price = matcher.get_total_price(bundle)
            same_seller_items = matcher.get_same_seller_items(bundle)

            st.markdown(f"""
            <div style="background:#f0f9f9;border:1px solid #b2dfdb;border-radius:12px;
                        padding:14px 20px;margin-bottom:20px;display:flex;
                        align-items:center;justify-content:space-between;">
                <div>
                    <div style="font-size:13px;color:#555;">Complete outfit total</div>
                    <div style="font-size:20px;font-weight:700;color:#007782;">€{total_price}</div>
                </div>
                <div style="font-size:13px;color:#007782;font-weight:500;">
                    {len(same_seller_items)} item(s) from same seller 📦
                </div>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(len(bundle))
            for col, piece in zip(cols, bundle):
                with col:
                    piece_img = get_catalog_image(piece["id"])
                    is_seed = piece.get("is_seed", False)
                    border = "2px solid #09a89e" if is_seed else "1px solid #ebebeb"
                    st.markdown(f'<div style="background:#fff;border-radius:12px;border:{border};overflow:hidden;">', unsafe_allow_html=True)
                    if piece_img:
                        st.image(piece_img, width="stretch")
                    else:
                        st.markdown('<div style="background:#f0f0f0;height:140px;display:flex;align-items:center;justify-content:center;font-size:36px;">👕</div>', unsafe_allow_html=True)
                    role_label = piece["role"].capitalize()
                    seed_label = " · Your item" if is_seed else ""
                    st.markdown(f"""
                    <div style="padding:10px 12px 14px;">
                        <div style="font-size:10px;font-weight:600;color:#09a89e;text-transform:uppercase;">{role_label}{seed_label}</div>
                        <div style="font-size:12px;color:#555;margin-top:2px;">{piece['name'][:40]}</div>
                        <div style="font-size:15px;font-weight:700;margin-top:4px;">€{piece['price']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            if len(same_seller_items) > 1:
                with st.expander("💡 Bundle tip — save on shipping"):
                    st.write(f"**{len(same_seller_items)} items** are from the same seller.")
                    for si in same_seller_items:
                        st.write(f"  • {si['name'][:50]} — €{si['price']}")


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for key, default in [
    ("upload_option", None), ("item_desc", None), ("uploaded_image", None),
    ("cohere_parsed", None), ("show_results", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────
navbar()
st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown('<div class="section-title">Find matches for your item</div>', unsafe_allow_html=True)
st.markdown("<div class=\"section-subtitle\">Tell us about an item you own — we'll find what pairs with it from the Vinted catalog</div>", unsafe_allow_html=True)

st.markdown("**How would you like to describe your item?**")
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    active1 = "option-card-active" if st.session_state.upload_option == "photo" else ""
    st.markdown(f"""
    <div class="option-card {active1}">
        <div class="option-icon">📸</div>
        <div class="option-title">Upload a photo</div>
        <div class="option-desc">Upload your item — autofill coming in v2</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Choose Photo", key="btn_photo", width="stretch"):
        st.session_state.upload_option = "photo"
        st.session_state.show_results = False
        st.rerun()

with col2:
    active2 = "option-card-active" if st.session_state.upload_option == "dropdowns" else ""
    st.markdown(f"""
    <div class="option-card {active2}">
        <div class="option-icon">🎛️</div>
        <div class="option-title">Select with filters</div>
        <div class="option-desc">Use dropdowns and buttons to describe your item</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Choose Filters", key="btn_dropdowns", width="stretch"):
        st.session_state.upload_option = "dropdowns"
        st.session_state.show_results = False
        st.rerun()

with col3:
    active3 = "option-card-active" if st.session_state.upload_option == "text" else ""
    st.markdown(f"""
    <div class="option-card {active3}">
        <div class="option-icon">✍️</div>
        <div class="option-title">Describe in words</div>
        <div class="option-desc">Type naturally — AI fills the fields for you</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Choose Text", key="btn_text", width="stretch"):
        st.session_state.upload_option = "text"
        st.session_state.show_results = False
        st.rerun()

# ── STEP 2: Form ──────────────────────────────
if st.session_state.upload_option:
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    # ── OPTION 1: PHOTO ──
    if st.session_state.upload_option == "photo":
        st.markdown("### 📸 Upload your item photo")
        uploaded_file = st.file_uploader("photo", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")

        if uploaded_file:
            img = Image.open(uploaded_file)
            st.session_state.uploaded_image = img
            col_img, col_notice = st.columns([1, 2])
            with col_img:
                st.image(img, width="stretch")
            with col_notice:
                st.markdown("""
                <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:10px;padding:16px 20px;margin-top:8px;">
                    <div style="font-size:15px;font-weight:600;color:#f57f17;margin-bottom:6px;">🚧 Autofill coming in v2</div>
                    <div style="font-size:13px;color:#555;line-height:1.6;">
                        In the next version, uploading a photo will automatically detect your item type,
                        colour, and style using AI image recognition.<br><br>
                        For now, please fill in the details manually below.
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Fill in your item details:**")
        c1, c2 = st.columns(2)
        with c1:
            article_type = st.selectbox("Item type", ARTICLE_TYPES, key="p_type")
            colour       = st.selectbox("Colour", COLOURS, key="p_colour")
            gender       = st.selectbox("Gender", GENDERS, key="p_gender")
        with c2:
            occasion  = st.selectbox("Occasion", OCCASIONS, key="p_occasion")
            season    = st.selectbox("Season", SEASONS, key="p_season")
            condition = st.selectbox("Condition", CONDITIONS, key="p_condition")

        if st.button("🔍 Find matches", key="submit_photo"):
            st.session_state.item_desc = {"articleType": article_type, "baseColour": colour, "gender": gender, "usage": occasion, "season": season, "condition": condition}
            st.session_state.show_results = True

    # ── OPTION 2: DROPDOWNS ──
    elif st.session_state.upload_option == "dropdowns":
        st.markdown("### 🎛️ Describe your item with filters")
        st.session_state.uploaded_image = None

        c1, c2 = st.columns(2)
        with c1:
            article_type = st.selectbox("Item type", ARTICLE_TYPES, key="d_type")
            colour       = st.selectbox("Colour", COLOURS, key="d_colour")
            gender       = st.selectbox("Gender", GENDERS, key="d_gender")
        with c2:
            season    = st.selectbox("Season", SEASONS, key="d_season")
            condition = st.selectbox("Condition", CONDITIONS, key="d_condition")
            occasion = st.selectbox("Occasion", OCCASIONS, key="d_occasion")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Find matches", key="submit_dropdowns"):
            st.session_state.item_desc = {"articleType": article_type, "baseColour": colour, "gender": gender, "usage": occasion, "season": season, "condition": condition}
            st.session_state.show_results = True

    # ── OPTION 3: TEXT + COHERE ──
    elif st.session_state.upload_option == "text":
        st.markdown("### ✍️ Describe your item in plain language")
        st.session_state.uploaded_image = None

        st.markdown('<div style="font-size:13px;color:#888;margin-bottom:12px;">Examples: "navy blue casual jeans for men", "black formal blazer for women", "white summer dress"</div>', unsafe_allow_html=True)

        description = st.text_area("desc", placeholder="e.g. dark blue slim fit casual jeans for men...", height=100, label_visibility="collapsed")

        if st.button("🤖 Parse with AI", key="parse_cohere") and description.strip():
            with st.spinner("Analysing with Cohere AI..."):
                try:
                    parsed = parse_with_cohere(description)
                    st.session_state.cohere_parsed = parsed
                except Exception as e:
                    st.error(f"Could not parse description: {e}")
                    st.session_state.cohere_parsed = None

        if st.session_state.cohere_parsed:
            parsed = st.session_state.cohere_parsed
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background:#f0f9f9;border:1px solid #b2dfdb;border-radius:10px;padding:16px 20px;margin-bottom:16px;">
                <div style="font-size:14px;font-weight:600;color:#007782;margin-bottom:8px;">
                    ✦ AI detected the following — verify and adjust if needed:
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                article_type = st.selectbox("Item type", ARTICLE_TYPES,
                    index=ARTICLE_TYPES.index(parsed.get("articleType", ARTICLE_TYPES[0])) if parsed.get("articleType") in ARTICLE_TYPES else 0,
                    key="t_type")
                colour = st.selectbox("Colour", COLOURS,
                    index=COLOURS.index(parsed.get("baseColour", COLOURS[0])) if parsed.get("baseColour") in COLOURS else 0,
                    key="t_colour")
                gender = st.selectbox("Gender", GENDERS,
                    index=GENDERS.index(parsed.get("gender", "Unisex")) if parsed.get("gender") in GENDERS else 2,
                    key="t_gender")
            with c2:
                occasion = st.selectbox("Occasion", OCCASIONS,
                    index=OCCASIONS.index(parsed.get("usage", "Casual")) if parsed.get("usage") in OCCASIONS else 0,
                    key="t_occasion")
                season = st.selectbox("Season", SEASONS,
                    index=SEASONS.index(parsed.get("season", "Summer")) if parsed.get("season") in SEASONS else 0,
                    key="t_season")
                condition = st.selectbox("Condition", CONDITIONS, key="t_condition")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Find matches", key="submit_text"):
                st.session_state.item_desc = {"articleType": article_type, "baseColour": colour, "gender": gender, "usage": occasion, "season": season, "condition": condition}
                st.session_state.show_results = True

    st.markdown('</div>', unsafe_allow_html=True)

# ── STEP 3: Results ──────────────────────────
if st.session_state.show_results and st.session_state.item_desc:
    show_results(st.session_state.item_desc, uploaded_image=st.session_state.get("uploaded_image"))
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Start over", key="reset"):
        for key in ["upload_option", "item_desc", "uploaded_image", "cohere_parsed", "show_results", "selected_occasion"]:
            st.session_state.pop(key, None)
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)