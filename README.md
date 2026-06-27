# TravelMind – AI Travel Planning Agent

TravelMind is an AI-powered travel planning application that helps users plan trips based on their destination, travel dates, budget, and number of travelers.

Using **LangGraph**, the AI agent coordinates multiple tools to search for flights and hotels, generate personalized travel packages, and create a Google Calendar event after the user approves a package.

---

## Live Demo

**Website:** https://travelmind.software

---

## Features

* AI-powered travel planning
* Multi-step AI workflow using LangGraph
* Flight search integration
* Hotel search integration
* Budget-aware travel package recommendations
* Multiple travel package options
* Google Calendar event creation
* Conversation memory
* Destination image cards
* Automatic deployment with GitHub Actions
* Production deployment on Microsoft Azure

---

## Tech Stack

### Frontend

* Streamlit

### Backend

* Python

### AI Framework

* LangGraph
* LangChain

### APIs

* Flight API
* Hotel API
* Google Calendar API

### Deployment & DevOps

* Microsoft Azure Ubuntu VM
* Nginx Reverse Proxy
* GitHub Actions (CI/CD)
* Let's Encrypt SSL
* Custom Domain (travelmind.software)

---

## Project Architecture

```text
User
   │
   ▼
Streamlit Frontend
   │
   ▼
LangGraph AI Agent
   │
   ├── Flight Tool
   ├── Hotel Tool
   └── Google Calendar Tool
   │
   ▼
Travel Package Recommendations
   │
   ▼
Package Approval
   │
   ▼
Google Calendar Event
```

---

## Local Installation

Clone the repository

```bash
git clone https://github.com/zainameen335/travelmind.git
cd travelmind
```

Create a virtual environment

```bash
python -m venv ai_env
```

Activate the environment

### Windows

```bash
ai_env\Scripts\activate
```

### Linux

```bash
source ai_env/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file and configure your API keys.

Run the application

```bash
streamlit run frontend.py
```

---

## Production Deployment

TravelMind is deployed using a production-style deployment pipeline.

### Infrastructure

* Microsoft Azure Ubuntu Virtual Machine
* Nginx Reverse Proxy
* HTTPS using Let's Encrypt
* Custom Domain (travelmind.software)

### CI/CD

GitHub Actions automatically deploys the latest version to the Azure VM whenever changes are pushed to the `main` branch.

---

## Project Structure

```text
travelmind/
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── assets/
│
├── tools/
│   ├── flight_tool.py
│   ├── hotel_tool.py
│   └── calendar_tool.py
│
├── agent.py
├── backend.py
├── frontend.py
├── requirements.txt
└── README.md
```

---

## Environment Variables

The following files are intentionally excluded from version control:

* `.env`
* `credentials.json`
* `token.json`
* `*.pem`

---

## Future Improvements

* Flight booking integration
* Hotel booking integration
* Currency conversion
* User authentication
* Trip history
* Email itinerary sharing

---

## Author

**Zain Ameen**

GitHub: https://github.com/zainameen335

LinkedIn: https://www.linkedin.com/in/zainameen335/

---

