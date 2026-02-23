"""
app.py — Vinted Outfit Match
Main page: Browse catalog → click item → see outfit recommendations

Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
from PIL import Image
import os
import sys

sys.path.append(os.path.dirname(__file__))
from matching_engine import OutfitMatcher

st.set_page_config(
    page_title="Vinted Outfit Match",
    page_icon="👗",
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

.page-content { padding: 24px 32px; max-width: 1400px; margin: 0 auto; }
.section-title { font-size: 20px; font-weight: 600; color: #1a1a1a; margin-bottom: 4px; }
.section-subtitle { font-size: 13px; color: #888; margin-bottom: 20px; }

.filter-bar { background: #ffffff; border: 1px solid #e8e8e8; border-radius: 12px; padding: 16px 20px; margin-bottom: 24px; }

.item-card { background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #ebebeb; transition: all 0.2s ease; cursor: pointer; height: 100%; }
.item-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); transform: translateY(-2px); border-color: #09a89e; }
.item-card-body { padding: 10px 12px 12px; }
.item-card-price { font-size: 16px; font-weight: 700; color: #1a1a1a; }
.item-card-name { font-size: 12px; color: #555; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-card-badge { display: inline-block; font-size: 10px; padding: 2px 7px; border-radius: 20px; margin-top: 6px; font-weight: 500; }
.badge-new      { background: #e8f5e9; color: #2e7d32; }
.badge-likenew  { background: #e3f2fd; color: #1565c0; }
.badge-good     { background: #fff8e1; color: #f57f17; }
.badge-fair     { background: #fce4ec; color: #c62828; }

.detail-price { font-size: 28px; font-weight: 700; color: #1a1a1a; }
.detail-name { font-size: 18px; font-weight: 600; margin-bottom: 12px; line-height: 1.3; }
.detail-tag { display: inline-block; background: #f0f9f9; color: #007782; border: 1px solid #b2dfdb; border-radius: 20px; font-size: 12px; padding: 3px 10px; margin: 2px 2px 2px 0; font-weight: 500; }
.seller-pill { background: #f5f5f5; border-radius: 8px; padding: 10px 14px; margin-top: 16px; font-size: 13px; color: #555; }
.seller-name { font-weight: 600; color: #1a1a1a; }

.match-section-header { font-size: 18px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px; }
.match-section-sub { font-size: 13px; color: #888; margin-bottom: 20px; }

.match-card { background: #ffffff; border-radius: 12px; border: 1px solid #ebebeb; overflow: hidden; transition: all 0.2s ease; }
.match-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); border-color: #09a89e; transform: translateY(-2px); }
.match-card-body { padding: 10px 12px 14px; }
.match-why { font-size: 11px; color: #09a89e; font-weight: 500; margin-top: 4px; line-height: 1.4; }
.same-seller-banner { background: #e8f5f4; border-top: 1px solid #b2dfdb; padding: 5px 12px; font-size: 11px; color: #007782; font-weight: 600; }
.bundle-total { font-size: 20px; font-weight: 700; color: #007782; }

.stButton > button { background-color: #007782 !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 14px !important; padding: 10px 20px !important; transition: background 0.2s !important; }
.stButton > button:hover { background-color: #09a89e !important; }

.stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #e8e8e8; }
.stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0 !important; font-weight: 500 !important; color: #666 !important; padding: 8px 16px !important; }
.stTabs [aria-selected="true"] { color: #007782 !important; border-bottom: 2px solid #007782 !important; }

hr { border-color: #ebebeb !important; margin: 24px 0 !important; }
</style>
""", unsafe_allow_html=True)


IMAGE_DIR = "data/images"

@st.cache_resource(show_spinner="Loading catalog...")
def load_matcher():
    return OutfitMatcher()

@st.cache_data(show_spinner=False)
def load_catalog():
    df = pd.read_csv("data/vinted_catalog.csv", on_bad_lines="skip")
    df["usage"]      = df["usage"].fillna("Casual")
    df["season"]     = df["season"].fillna("Fall")
    df["baseColour"] = df["baseColour"].fillna("Multi")
    df = df[df["masterCategory"].isin(["Apparel", "Accessories", "Footwear"])].copy()
    return df.reset_index(drop=True)

def get_image(item_id):
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


if "selected_item_id" not in st.session_state:
    st.session_state.selected_item_id = None
if "show_bundle" not in st.session_state:
    st.session_state.show_bundle = False

navbar()
matcher = load_matcher()
df = load_catalog()


def show_browse():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Browse items</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Click any item to see what matches with it</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        with col1:
            search = st.text_input("search", placeholder="e.g. blue jeans, floral dress...", label_visibility="collapsed")
        with col2:
            gender_opts = ["All genders"] + sorted(df["gender"].dropna().unique().tolist())
            gender_f = st.selectbox("Gender", gender_opts, label_visibility="collapsed")
        with col3:
            cat_opts = ["All categories"] + sorted(df["masterCategory"].dropna().unique().tolist())
            cat_f = st.selectbox("Category", cat_opts, label_visibility="collapsed")
        with col4:
            usage_opts = ["All occasions"] + sorted(df["usage"].dropna().unique().tolist())
            usage_f = st.selectbox("Occasion", usage_opts, label_visibility="collapsed")
        with col5:
            season_opts = ["All seasons"] + sorted(df["season"].dropna().unique().tolist())
            season_f = st.selectbox("Season", season_opts, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    filtered = df.copy()
    if search:
        filtered = filtered[filtered["productDisplayName"].str.contains(search, case=False, na=False)]
    if gender_f != "All genders":
        filtered = filtered[filtered["gender"] == gender_f]
    if cat_f != "All categories":
        filtered = filtered[filtered["masterCategory"] == cat_f]
    if usage_f != "All occasions":
        filtered = filtered[filtered["usage"] == usage_f]
    if season_f != "All seasons":
        filtered = filtered[filtered["season"] == season_f]

    total = len(filtered)
    st.markdown(f'<div style="font-size:13px;color:#888;margin-bottom:16px;">{total:,} items found</div>', unsafe_allow_html=True)

    if total == 0:
        st.info("No items match your filters. Try broadening your search.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    sample = filtered.head(60)
    cols_per_row = 5
    rows = [sample.iloc[i:i+cols_per_row] for i in range(0, len(sample), cols_per_row)]

    for row_df in rows:
        cols = st.columns(cols_per_row)
        for col, (_, item) in zip(cols, row_df.iterrows()):
            with col:
                img = get_image(item["id"])
                st.markdown('<div class="item-card">', unsafe_allow_html=True)
                if img:
                    st.image(img, width="stretch")
                else:
                    st.markdown('<div style="background:#f0f0f0;height:180px;display:flex;align-items:center;justify-content:center;font-size:30px;">👕</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="item-card-body">
                    <div class="item-card-price">€{item['price']}</div>
                    <div class="item-card-name">{item['productDisplayName'][:45]}</div>
                    {condition_badge(item['condition'])}
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                if st.button("View", key=f"item_{item['id']}", width="stretch"):
                    st.session_state.selected_item_id = item["id"]
                    st.session_state.show_bundle = False
                    st.session_state.scroll_to_top = True
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def show_item_detail(item_id):
    st.components.v1.html("<script>window.parent.document.querySelector('section.main').scrollTo(0, 0);</script>", height=0)
    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    if st.button("← Back to browse"):
        st.session_state.selected_item_id = None
        st.session_state.show_bundle = False
        st.rerun()

    item_row = df[df["id"] == item_id]
    if item_row.empty:
        st.error("Item not found.")
        return
    item = item_row.iloc[0]

    left, right = st.columns([1, 2])
    with left:
        img = get_image(item_id)
        if img:
            st.image(img, width="stretch")
        else:
            st.markdown('<div style="background:#f0f0f0;border-radius:12px;height:320px;display:flex;align-items:center;justify-content:center;font-size:60px;">👕</div>', unsafe_allow_html=True)

    with right:
        st.markdown(f'<div class="detail-name">{item["productDisplayName"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-price">€{item["price"]}</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        tags_html = ""
        for tag in [item["articleType"], item["gender"], item["baseColour"], item["usage"], item["season"], item["condition"]]:
            if pd.notna(tag):
                tags_html += f'<span class="detail-tag">{tag}</span>'
        st.markdown(tags_html, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="seller-pill">
            👤 <span class="seller-name">{item['seller']}</span>
            &nbsp;·&nbsp; Seller on Vinted
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["✨ Match with", "👗 Build complete outfit"])

    with tab1:
        st.markdown('<div class="match-section-header">Items that match well with this</div>', unsafe_allow_html=True)
        st.markdown('<div class="match-section-sub">Based on colour harmony, occasion, and style compatibility</div>', unsafe_allow_html=True)

        with st.spinner("Finding matches..."):
            matches = matcher.get_matches(item_id, num_matches=6)

        if not matches:
            st.info("No matches found for this item type. Try a different item.")
        else:
            cols = st.columns(3)
            for i, match in enumerate(matches):
                with cols[i % 3]:
                    match_img = get_image(match["id"])
                    same_seller = match["seller"] == item["seller"]
                    st.markdown('<div class="match-card">', unsafe_allow_html=True)
                    if match_img:
                        st.image(match_img, width="stretch")
                    else:
                        st.markdown('<div style="background:#f0f0f0;height:160px;display:flex;align-items:center;justify-content:center;font-size:40px;">👚</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="match-card-body">
                        <div class="item-card-price">€{match['price']}</div>
                        <div class="item-card-name">{match['name'][:45]}</div>
                        <div class="match-why">✦ {match['explanation']}</div>
                        {condition_badge(match['condition'])}
                    </div>
                    """, unsafe_allow_html=True)
                    if same_seller:
                        st.markdown('<div class="same-seller-banner">📦 Same seller — bundle & save on shipping!</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="match-section-header">Complete outfit built around this item</div>', unsafe_allow_html=True)
        st.markdown('<div class="match-section-sub">One piece per role — top, bottom, shoes, and accessory</div>', unsafe_allow_html=True)

        with st.spinner("Building your outfit..."):
            bundle = matcher.get_outfit_bundle(item_id, num_items=4)

        if not bundle:
            st.info("Could not build a full outfit for this item.")
        else:
            total_price = matcher.get_total_price(bundle)
            same_seller_items = matcher.get_same_seller_items(bundle)

            st.markdown(f"""
            <div style="background:#f0f9f9;border:1px solid #b2dfdb;border-radius:12px;padding:14px 20px;
                        margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;">
                <div>
                    <div style="font-size:13px;color:#555;">Complete outfit total</div>
                    <div class="bundle-total">€{total_price}</div>
                </div>
                <div style="font-size:13px;color:#007782;font-weight:500;">
                    {len(same_seller_items)} item(s) from same seller 📦
                </div>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(len(bundle))
            for col, piece in zip(cols, bundle):
                with col:
                    piece_img = get_image(piece["id"])
                    is_seed = piece.get("is_seed", False)
                    border = "2px solid #09a89e" if is_seed else "1px solid #ebebeb"
                    st.markdown(f'<div style="background:#fff;border-radius:12px;border:{border};overflow:hidden;">', unsafe_allow_html=True)
                    if piece_img:
                        st.image(piece_img, width="stretch")
                    else:
                        st.markdown('<div style="background:#f0f0f0;height:140px;display:flex;align-items:center;justify-content:center;font-size:36px;">👕</div>', unsafe_allow_html=True)
                    role_label = piece["role"].capitalize()
                    seed_label = " · Selected item" if is_seed else ""
                    st.markdown(f"""
                    <div style="padding:10px 12px 14px;">
                        <div style="font-size:10px;font-weight:600;color:#09a89e;text-transform:uppercase;letter-spacing:0.5px;">{role_label}{seed_label}</div>
                        <div style="font-size:12px;color:#555;margin-top:2px;">{piece['name'][:40]}</div>
                        <div style="font-size:15px;font-weight:700;margin-top:4px;">€{piece['price']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            if len(same_seller_items) > 1:
                with st.expander("💡 Bundle tip — save on shipping"):
                    st.write(f"**{len(same_seller_items)} items** in this outfit are from the same seller **{same_seller_items[0]['seller']}**.")
                    st.write("Message the seller to buy them together and pay shipping only once!")
                    for si in same_seller_items:
                        st.write(f"  • {si['name'][:50]} — €{si['price']}")

    st.markdown('</div>', unsafe_allow_html=True)


if st.session_state.selected_item_id is None:
    show_browse()
else:
    show_item_detail(st.session_state.selected_item_id)