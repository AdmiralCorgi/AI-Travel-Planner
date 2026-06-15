from html import escape

import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/plan"


def build_itinerary_html(destination, days, budget, interests, notes, places, day_plans):
    destination_text = escape(destination)
    budget_text = escape(budget)
    interest_text = escape(", ".join(interests) if interests else "General sightseeing")
    notes_html = (
        f"<p><strong>Traveler notes:</strong> {escape(notes)}</p>" if notes else ""
    )

    day_buttons = "\n".join(
        f'<button class="day-btn{" active" if index == 0 else ""}" '
        f'onclick="switchDay({plan["day"]}, event)">Day {plan["day"]}</button>'
        for index, plan in enumerate(day_plans)
    )

    day_sections = []
    for index, plan in enumerate(day_plans):
        day_sections.append(
            f"""
        <div id="day{plan["day"]}" class="day-content{" active" if index == 0 else ""}">
          <h3 class="day-heading">Day {plan["day"]}: {escape(plan["theme"])}</h3>
          <div class="itinerary-card">
            <div class="itinerary-time">Morning</div>
            <h3>Start the day</h3>
            <p>{escape(plan["morning"])}</p>
          </div>
          <div class="itinerary-card">
            <div class="itinerary-time">Afternoon</div>
            <h3>Continue exploring</h3>
            <p>{escape(plan["afternoon"])}</p>
          </div>
          <div class="itinerary-card">
            <div class="itinerary-time">Evening</div>
            <h3>Wrap up nearby</h3>
            <p>{escape(plan["evening"])}</p>
          </div>
          <div class="itinerary-card">
            <div class="itinerary-time">Food</div>
            <h3>Meal idea</h3>
            <p>{escape(plan["food"])}</p>
          </div>
          <div class="itinerary-card">
            <div class="itinerary-time">Transport</div>
            <h3>Route note</h3>
            <p>{escape(plan["transport"])}</p>
          </div>
        </div>
            """
        )

    place_cards = "\n".join(
        f"""
          <a class="place-card" href="{escape(place["maps_url"])}" target="_blank" rel="noopener">
            <i class="fas fa-map-marker-alt"></i>
            <h3>{escape(place["name"])}</h3>
            <p>{escape(place.get("description") or "A useful stop to research before finalizing your route.")}</p>
          </a>
        """
        for place in places
    )

    if not place_cards:
        place_cards = """
          <div class="place-card">
            <i class="fas fa-map-marker-alt"></i>
            <h3>Research local highlights</h3>
            <p>Check current opening hours, location, ticket rules, and transport before finalizing the route.</p>
          </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{destination_text} Trip Guide</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      min-height: 100vh;
      padding: 20px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}

    .container {{
      max-width: 1000px;
      margin: 0 auto;
      overflow: hidden;
      border-radius: 16px;
      background: #ffffff;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.30);
    }}

    header {{
      padding: 42px 30px;
      color: #ffffff;
      text-align: center;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }}

    header h1 {{
      margin-bottom: 10px;
      font-size: 46px;
      font-weight: 750;
    }}

    header p {{
      font-size: 16px;
      opacity: 0.92;
    }}

    .content {{
      padding: 40px 30px;
    }}

    section {{
      margin-bottom: 50px;
    }}

    h2 {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 20px;
      color: #333333;
      font-size: 28px;
      font-weight: 650;
    }}

    h2 i {{
      color: #667eea;
      font-size: 30px;
    }}

    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
    }}

    .summary-card,
    .tip-card {{
      padding: 20px;
      border: 1px solid #e0e0ff;
      border-radius: 12px;
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.10) 0%, rgba(118, 75, 162, 0.10) 100%);
    }}

    .summary-card strong,
    .tip-card h3 {{
      display: block;
      margin-bottom: 8px;
      color: #333333;
      font-size: 15px;
    }}

    .summary-card p,
    .tip-card p {{
      color: #666666;
      font-size: 14px;
      line-height: 1.55;
    }}

    .day-selector {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 30px;
    }}

    .day-btn {{
      padding: 12px 20px;
      border: 2px solid #dddddd;
      border-radius: 8px;
      background: #f0f0f0;
      color: #333333;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      transition: all 0.25s ease;
    }}

    .day-btn:hover {{
      border-color: #667eea;
      background: #f8f8ff;
    }}

    .day-btn.active {{
      border-color: #667eea;
      color: #ffffff;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }}

    .day-content {{
      display: none;
    }}

    .day-content.active {{
      display: block;
      animation: fadeIn 0.3s ease-in;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(10px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .day-heading {{
      margin-bottom: 18px;
      color: #333333;
      font-size: 22px;
    }}

    .itinerary-card {{
      margin-bottom: 16px;
      padding: 24px;
      border-left: 4px solid #667eea;
      border-radius: 8px;
      background: #f9f9f9;
      transition: all 0.25s ease;
    }}

    .itinerary-card:hover {{
      background: #f0f0ff;
      box-shadow: 0 4px 16px rgba(102, 126, 234, 0.12);
    }}

    .itinerary-time {{
      margin-bottom: 8px;
      color: #667eea;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }}

    .itinerary-card h3 {{
      margin-bottom: 10px;
      color: #333333;
      font-size: 18px;
    }}

    .itinerary-card p {{
      color: #666666;
      font-size: 15px;
      line-height: 1.65;
    }}

    .place-grid,
    .tips-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
    }}

    .place-card {{
      display: block;
      padding: 24px;
      border: 2px solid #eeeeee;
      border-radius: 12px;
      color: inherit;
      text-align: center;
      text-decoration: none;
      background: #ffffff;
      transition: all 0.25s ease;
    }}

    .place-card:hover {{
      border-color: #667eea;
      box-shadow: 0 8px 24px rgba(102, 126, 234, 0.16);
      transform: translateY(-4px);
    }}

    .place-card i,
    .tip-card i {{
      display: block;
      margin-bottom: 14px;
      color: #667eea;
      font-size: 34px;
    }}

    .place-card h3 {{
      margin-bottom: 10px;
      color: #333333;
      font-size: 18px;
    }}

    .place-card p {{
      color: #666666;
      font-size: 14px;
      line-height: 1.5;
    }}

    footer {{
      padding: 30px;
      border-top: 1px solid #eeeeee;
      background: #f5f5f5;
      color: #666666;
      text-align: center;
      font-size: 14px;
    }}

    @media (max-width: 768px) {{
      body {{ padding: 10px; }}
      header h1 {{ font-size: 32px; }}
      .content {{ padding: 24px 20px; }}
      h2 {{ font-size: 22px; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>{destination_text}</h1>
      <p>Your {days}-day AI travel guide</p>
    </header>

    <div class="content">
      <section>
        <h2><i class="fas fa-suitcase"></i> Trip Summary</h2>
        <div class="summary">
          <div class="summary-card"><strong>Destination</strong><p>{destination_text}</p></div>
          <div class="summary-card"><strong>Length</strong><p>{days} days</p></div>
          <div class="summary-card"><strong>Budget</strong><p>{budget_text}</p></div>
          <div class="summary-card"><strong>Interests</strong><p>{interest_text}</p></div>
        </div>
        {notes_html}
      </section>

      <section>
        <h2><i class="fas fa-calendar"></i> Day-by-Day Itinerary</h2>
        <div class="day-selector">
          {day_buttons}
        </div>
        {"".join(day_sections)}
      </section>

      <section>
        <h2><i class="fas fa-map-marker-alt"></i> Recommended Places</h2>
        <div class="place-grid">
          {place_cards}
        </div>
      </section>

      <section>
        <h2><i class="fas fa-lightbulb"></i> Practical Tips</h2>
        <div class="tips-grid">
          <div class="tip-card"><i class="fas fa-wallet"></i><h3>Budget</h3><p>Plan paid attractions first, then fill gaps with free walks, markets, parks, and viewpoints.</p></div>
          <div class="tip-card"><i class="fas fa-train"></i><h3>Transport</h3><p>Group nearby stops together and check route times before leaving each morning.</p></div>
          <div class="tip-card"><i class="fas fa-clock"></i><h3>Timing</h3><p>Confirm opening hours, closed days, timed entry rules, and local holidays before booking.</p></div>
          <div class="tip-card"><i class="fas fa-cloud-sun"></i><h3>Weather</h3><p>Keep one indoor backup activity each day in case of heat, rain, or low energy.</p></div>
        </div>
      </section>
    </div>

    <footer>
      <p>Created with AI Travel Planner. Have a wonderful trip.</p>
    </footer>
  </div>

  <script>
    function switchDay(dayNumber, event) {{
      document.querySelectorAll(".day-content").forEach(content => content.classList.remove("active"));
      document.querySelectorAll(".day-btn").forEach(button => button.classList.remove("active"));
      document.getElementById("day" + dayNumber).classList.add("active");
      event.target.classList.add("active");
    }}
  </script>
</body>
</html>
"""


st.set_page_config(
    page_title="AI Travel Planner",
    page_icon=":airplane:",
    layout="centered",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #172033;
        --muted: #5f6f89;
        --sky: #e7f4ff;
        --coral: #ff7a66;
        --teal: #00a99d;
        --gold: #f7b731;
        --panel: rgba(255, 255, 255, 0.86);
        --line: rgba(23, 32, 51, 0.10);
    }

    html, body, [class*="css"] {
        font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .stApp {
        color: var(--ink);
        background:
            radial-gradient(circle at 12% 12%, rgba(255, 122, 102, 0.22), transparent 28%),
            radial-gradient(circle at 88% 8%, rgba(0, 169, 157, 0.20), transparent 30%),
            linear-gradient(135deg, #f8fbff 0%, #edf7ff 44%, #fff8ec 100%);
    }

    .block-container {
        max-width: 920px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 2.3rem 2.2rem;
        border: 1px solid rgba(255, 255, 255, 0.72);
        border-radius: 24px;
        background:
            linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(255, 255, 255, 0.70)),
            url("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1400&q=80");
        background-size: cover;
        background-position: center;
        box-shadow: 0 24px 70px rgba(37, 57, 90, 0.18);
    }

    .hero::after {
        content: "";
        position: absolute;
        inset: auto -15% -45% auto;
        width: 360px;
        height: 360px;
        background: rgba(255, 255, 255, 0.45);
        border-radius: 50%;
    }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        margin-bottom: 0.7rem;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        color: #0e766e;
        background: rgba(0, 169, 157, 0.13);
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .hero h1 {
        max-width: 650px;
        margin: 0;
        color: #10192c;
        font-size: clamp(2.25rem, 6vw, 4.4rem);
        line-height: 0.98;
        letter-spacing: 0;
    }

    .hero p {
        max-width: 570px;
        margin: 1rem 0 0;
        color: #3d4b62;
        font-size: 1.06rem;
        line-height: 1.65;
    }

    .trip-stats {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 1.35rem 0 0;
        max-width: 640px;
    }

    .trip-stat {
        padding: 0.85rem 0.95rem;
        border: 1px solid rgba(255, 255, 255, 0.76);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.70);
        box-shadow: 0 12px 34px rgba(23, 32, 51, 0.10);
    }

    .trip-stat strong {
        display: block;
        color: #111a2d;
        font-size: 1rem;
    }

    .trip-stat span {
        color: var(--muted);
        font-size: 0.78rem;
        font-weight: 600;
    }

    div[data-testid="stForm"] {
        margin-top: 1.35rem;
        padding: 1.35rem;
        border: 1px solid var(--line);
        border-radius: 20px;
        background: var(--panel);
        box-shadow: 0 18px 50px rgba(37, 57, 90, 0.12);
        backdrop-filter: blur(12px);
    }

    label, .stMultiSelect label, .stTextInput label, .stTextArea label {
        color: #1a2638 !important;
        font-weight: 700 !important;
    }

    .stTextInput,
    .stNumberInput,
    .stSelectbox,
    .stMultiSelect,
    .stTextArea {
        margin-bottom: 0.55rem;
    }

    div[data-baseweb="input"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="textarea"] {
        min-height: 2.85rem;
        border: 1px solid rgba(23, 32, 51, 0.15) !important;
        border-radius: 13px !important;
        background: rgba(255, 255, 255, 0.94) !important;
        box-shadow: 0 8px 18px rgba(23, 32, 51, 0.05) !important;
        transition: border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
    }

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within > div,
    div[data-baseweb="textarea"]:focus-within {
        border-color: rgba(0, 169, 157, 0.58) !important;
        box-shadow: 0 0 0 4px rgba(0, 169, 157, 0.12), 0 10px 22px rgba(23, 32, 51, 0.07) !important;
    }

    input,
    textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] input,
    div[data-baseweb="textarea"] textarea {
        color: #142033 !important;
        caret-color: var(--teal) !important;
        background: transparent !important;
        font-weight: 600 !important;
    }

    input::placeholder,
    textarea::placeholder {
        color: #8794a7 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }

    .stNumberInput > div {
        gap: 0 !important;
    }

    .stNumberInput div[data-baseweb="input"] {
        overflow: hidden;
        min-height: 2.85rem;
        padding-right: 0 !important;
        border-right: 0 !important;
        border-radius: 13px 0 0 13px !important;
        background: rgba(255, 255, 255, 0.94) !important;
    }

    .stNumberInput input {
        background: rgba(255, 255, 255, 0.94) !important;
    }

    div[data-testid="InputInstructions"],
    .stNumberInput div[data-testid="InputInstructions"] {
        display: none !important;
    }

    .stNumberInput button {
        height: 2.85rem !important;
        min-width: 2.45rem !important;
        border: 1px solid rgba(23, 32, 51, 0.15) !important;
        border-left: 0 !important;
        border-radius: 0 !important;
        color: #1f2b40 !important;
        background: rgba(248, 251, 255, 0.96) !important;
        box-shadow: 0 8px 18px rgba(23, 32, 51, 0.05) !important;
    }

    .stNumberInput button:hover {
        color: #0e766e !important;
        background: rgba(0, 169, 157, 0.10) !important;
    }

    .stNumberInput button:last-child {
        border-radius: 0 13px 13px 0 !important;
    }

    .stSelectbox svg,
    .stMultiSelect svg {
        color: #5f6f89 !important;
        fill: #5f6f89 !important;
    }

    .stMultiSelect [data-baseweb="tag"] {
        height: 1.9rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #ff6f61, #ff474f) !important;
        color: #ffffff !important;
        font-weight: 800;
        box-shadow: 0 6px 14px rgba(255, 71, 79, 0.20);
    }

    .stMultiSelect [data-baseweb="tag"] span {
        color: #ffffff !important;
    }

    textarea {
        min-height: 6rem !important;
        resize: vertical !important;
    }

    textarea:focus,
    input:focus {
        outline: none !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        width: 100%;
        min-height: 3rem;
        border: 0;
        border-radius: 14px;
        color: white;
        font-weight: 800;
        background: linear-gradient(135deg, var(--coral), var(--teal));
        box-shadow: 0 14px 28px rgba(0, 169, 157, 0.24);
        transition: transform 160ms ease, box-shadow 160ms ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 18px 34px rgba(255, 122, 102, 0.28);
    }

    .result-card {
        margin-top: 1.4rem;
        padding: 1.35rem;
        border: 1px solid rgba(0, 169, 157, 0.18);
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.90);
        box-shadow: 0 18px 50px rgba(37, 57, 90, 0.12);
    }

    .result-card h2 {
        margin: 0 0 0.25rem;
        color: #10192c;
        font-size: 1.55rem;
        letter-spacing: 0;
    }

    .model-pill {
        display: inline-flex;
        margin-top: 1rem;
        padding: 0.45rem 0.75rem;
        border-radius: 999px;
        background: rgba(247, 183, 49, 0.18);
        color: #7a5411;
        font-size: 0.82rem;
        font-weight: 700;
    }

    .section-title {
        margin: 1.3rem 0 0.45rem;
        color: #10192c;
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: 0;
    }

    .place-card {
        min-height: 9rem;
        padding: 1rem;
        border: 1px solid rgba(23, 32, 51, 0.10);
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.88);
        box-shadow: 0 12px 32px rgba(37, 57, 90, 0.09);
    }

    .place-card h3 {
        margin: 0 0 0.45rem;
        color: #111a2d;
        font-size: 1rem;
        letter-spacing: 0;
    }

    .place-card p {
        margin: 0;
        color: var(--muted);
        font-size: 0.88rem;
        line-height: 1.5;
    }

    .day-meta {
        color: var(--muted);
        font-size: 0.92rem;
        font-weight: 700;
    }

    div[data-testid="stAlert"] {
        border-radius: 16px;
    }

    /* Final widget reset: Streamlit/BaseWeb can keep dark inner layers from the active theme. */
    [data-testid="stTextInputRootElement"],
    [data-testid="stNumberInputContainer"],
    [data-testid="stTextAreaRootElement"],
    .stTextInput div[data-baseweb="input"],
    .stTextInput div[data-baseweb="base-input"],
    .stTextInput div[data-baseweb="input"] > div,
    .stNumberInput div[data-baseweb="input"],
    .stNumberInput div[data-baseweb="base-input"],
    .stNumberInput div[data-baseweb="input"] > div,
    .stTextArea div[data-baseweb="textarea"],
    .stTextArea div[data-baseweb="base-input"],
    .stTextArea div[data-baseweb="textarea"] > div,
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #172033 !important;
    }

    [data-testid="stTextInputRootElement"],
    [data-testid="stNumberInputContainer"],
    [data-testid="stTextAreaRootElement"],
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        border: 1px solid rgba(23, 32, 51, 0.16) !important;
        border-radius: 14px !important;
        box-shadow: 0 8px 18px rgba(23, 32, 51, 0.05) !important;
    }

    [data-testid="stTextInputRootElement"]:focus-within,
    [data-testid="stNumberInputContainer"]:focus-within,
    [data-testid="stTextAreaRootElement"]:focus-within,
    .stSelectbox div[data-baseweb="select"] > div:focus-within,
    .stMultiSelect div[data-baseweb="select"] > div:focus-within {
        border-color: rgba(0, 169, 157, 0.58) !important;
        box-shadow: 0 0 0 4px rgba(0, 169, 157, 0.12), 0 10px 22px rgba(23, 32, 51, 0.07) !important;
    }

    [data-testid="stTextInputRootElement"] input,
    [data-testid="stNumberInputContainer"] input,
    [data-testid="stTextAreaRootElement"] textarea,
    .stSelectbox div[data-baseweb="select"] input,
    .stMultiSelect div[data-baseweb="select"] input {
        color: #172033 !important;
        -webkit-text-fill-color: #172033 !important;
        background: transparent !important;
    }

    [data-testid="stTextInputRootElement"] input::placeholder,
    [data-testid="stTextAreaRootElement"] textarea::placeholder {
        color: #7b879a !important;
        -webkit-text-fill-color: #7b879a !important;
    }

    [data-testid="stNumberInputContainer"] {
        overflow: hidden;
    }

    [data-testid="stNumberInputContainer"] button {
        border-top: 0 !important;
        border-right: 0 !important;
        border-bottom: 0 !important;
        background: #f8fbff !important;
        box-shadow: none !important;
    }

    @media (max-width: 640px) {
        .block-container {
            padding-top: 1rem;
        }

        .hero {
            padding: 1.5rem;
            border-radius: 18px;
        }

        .trip-stats {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="hero">
        <div class="eyebrow">Smart itinerary studio</div>
        <h1>AI Travel Planner</h1>
        <p>
            Build a practical day-by-day trip plan with destination ideas,
            budget-aware pacing, and activities shaped around what you like.
        </p>
        <div class="trip-stats">
            <div class="trip-stat"><strong>1-21 days</strong><span>Flexible trip length</span></div>
            <div class="trip-stat"><strong>3 budgets</strong><span>Low, medium, or high</span></div>
            <div class="trip-stat"><strong>9 interests</strong><span>Food, culture, nature, and more</span></div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)


def render_travel_result(result):
    data = result["data"]
    destination_value = result["destination"]
    days_value = result["days"]
    budget_value = result["budget"]
    interests_value = result["interests"]
    notes_value = result["notes"]
    places = data.get("recommended_places", [])
    day_plans = data.get("day_plans", [])

    st.markdown(
        """
        <div class="result-card">
            <h2>Your AI Travel Plan</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if places:
        st.markdown(
            '<div class="section-title">Recommended places</div>',
            unsafe_allow_html=True,
        )
        for index in range(0, len(places), 2):
            columns = st.columns(2)
            for column, place in zip(columns, places[index : index + 2]):
                with column:
                    place_name = escape(place["name"])
                    place_description = escape(
                        place.get("description")
                        or "A useful stop to research before finalizing your route."
                    )
                    st.markdown(
                        f"""
                        <div class="place-card">
                            <h3>{place_name}</h3>
                            <p>{place_description}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.link_button("Open in Google Maps", place["maps_url"])

    if day_plans:
        st.markdown(
            '<div class="section-title">Day-by-day itinerary</div>',
            unsafe_allow_html=True,
        )
        for plan in day_plans:
            with st.expander(
                f"Day {plan['day']}: {plan['theme']}",
                expanded=plan["day"] == 1,
            ):
                st.markdown('<div class="day-meta">Morning</div>', unsafe_allow_html=True)
                st.write(plan["morning"])
                st.markdown('<div class="day-meta">Afternoon</div>', unsafe_allow_html=True)
                st.write(plan["afternoon"])
                st.markdown('<div class="day-meta">Evening</div>', unsafe_allow_html=True)
                st.write(plan["evening"])
                st.markdown('<div class="day-meta">Food</div>', unsafe_allow_html=True)
                st.write(plan["food"])
                st.markdown('<div class="day-meta">Transport</div>', unsafe_allow_html=True)
                st.write(plan["transport"])
    else:
        st.markdown(data["itinerary"])

    guide_file_name = (
        f"{destination_value.strip().replace(' ', '_').lower()}_trip_guide.html"
    )
    st.download_button(
        "Download HTML trip guide",
        build_itinerary_html(
            destination_value.strip(),
            int(days_value),
            budget_value,
            interests_value,
            notes_value.strip(),
            places,
            day_plans,
        ),
        file_name=guide_file_name,
        mime="text/html",
    )
    st.markdown(
        f'<div class="model-pill">Generated with: {data["model"]}</div>',
        unsafe_allow_html=True,
    )


with st.form("travel_form"):
    destination = st.text_input("Destination", placeholder="Example: Tokyo, Japan")

    col1, col2 = st.columns(2)
    with col1:
        days = st.number_input("Number of days", min_value=1, max_value=21, value=3)
    with col2:
        budget = st.selectbox("Budget", ["Low", "Medium", "High"])

    interests = st.multiselect(
        "Travel interests",
        [
            "Food",
            "Culture",
            "Nature",
            "Shopping",
            "Adventure",
            "Relaxation",
            "Museums",
            "Nightlife",
            "Family-friendly",
        ],
        default=["Food", "Culture"],
    )

    notes = st.text_area(
        "Extra notes",
        placeholder="Example: I prefer public transport and vegetarian food.",
    )

    submitted = st.form_submit_button("Generate travel plan")

if submitted:
    if not destination.strip():
        st.error("Please enter a destination.")
    else:
        payload = {
            "destination": destination.strip(),
            "days": int(days),
            "budget": budget,
            "interests": interests,
            "notes": notes.strip(),
        }

        with st.spinner("Planning your trip..."):
            try:
                response = requests.post(API_URL, json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()
                st.session_state["travel_result"] = {
                    "data": data,
                    "destination": destination.strip(),
                    "days": int(days),
                    "budget": budget,
                    "interests": interests,
                    "notes": notes.strip(),
                }
            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to the backend API. Start FastAPI first with "
                    "`uvicorn backend.main:app`."
                )
            except requests.exceptions.RequestException as exc:
                st.error(f"Request failed: {exc}")

if "travel_result" in st.session_state:
    render_travel_result(st.session_state["travel_result"])
