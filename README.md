# AI Travel Planner

## Project Objective

AI Travel Planner is a local web application that creates a day-by-day travel itinerary from a user's destination, trip length, budget, interests, and extra notes.

The goal of the project is to show how a Streamlit frontend can send user input to a FastAPI backend, use an AI text-generation model to build a personalized travel plan, enrich the results with destination research from Wikipedia, and display recommended places with Google Maps links.

## Tools Used

- Python: main programming language
- Streamlit: frontend web interface
- FastAPI: backend API service
- Uvicorn: local ASGI server for FastAPI
- Requests: HTTP requests between the frontend, backend, and Wikipedia API
- Hugging Face Transformers: loads and runs the AI model
- PyTorch: model runtime used by Transformers
- Wikipedia API: destination research and place suggestions
- Google Maps search links: map links for recommended places

## AI Model Used

The project uses the Hugging Face model:

```text
google/flan-t5-small
```

The backend loads this model with `AutoTokenizer` and `AutoModelForSeq2SeqLM` from the `transformers` library. The model name can also be changed with the `TRAVEL_MODEL` environment variable.

## Project Structure

```text
.
|-- backend/
|   `-- main.py
|-- frontend/
|   `-- app.py
|-- requirements.txt
`-- README.md
```

## Running Instructions

Run these commands from the project root folder.

### 1. Create a virtual environment

```powershell
python -m venv .venv
```

### 2. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Start the backend API

```powershell
uvicorn backend.main:app
```

The backend will run at:

```text
http://127.0.0.1:8000
```

You can test it in a browser by opening:

```text
http://127.0.0.1:8000
```

### 5. Start the frontend app

Open a second PowerShell terminal in the project root, activate the virtual environment again, then run:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Streamlit will open the AI Travel Planner in your browser.

## How the App Works

1. The user enters a destination, number of days, budget, travel interests, and notes in the Streamlit app.
2. Streamlit sends the input to the FastAPI `/plan` endpoint.
3. The backend searches Wikipedia for relevant destination places.
4. The `google/flan-t5-small` model generates a travel itinerary.
5. The backend returns the itinerary, recommended places, Google Maps links, and structured day plans.
6. Streamlit displays the travel plan and lets the user download an HTML trip guide.

## Main API Endpoint

```text
POST /plan
```

Example request:

```json
{
  "destination": "Tokyo, Japan",
  "days": 4,
  "budget": "Medium",
  "interests": ["Food", "Culture", "Shopping"],
  "notes": "I prefer public transport."
}
```

## Notes

- The first AI request may take longer because the Hugging Face model must be downloaded.
- Keep the backend running while using the Streamlit frontend.
- Internet access is needed for the first model download and Wikipedia destination research.
