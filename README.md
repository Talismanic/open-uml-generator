# 🧠 Open UML Generator

A full-stack AI-powered system that generates UML diagrams from plain-language software requirements using AutoGen and PlantUML.

---

## 📁 Project Structure

```
open-uml-generator/
├── backend/               # FastAPI backend with AutoGen agents
│   ├── autogen_logic.py
│   ├── main.py
│   ├── tools.py
│   ├── uml_agent_runner.py
│   ├── utils.py
│   └── diagrams/          # Generated UML diagram images
├── frontend/              # React frontend
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
├── .gitignore
├── README.md
└── .env.example           # Sample environment variables
```

---

## ⚙️ Backend Setup (Python 3.10+ recommended)

### ✅ 1. Create and activate virtual environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

### ✅ 2. Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, install manually:

```bash
pip install fastapi uvicorn python-dotenv plantuml autogen typing_extensions
```

### ✅ 3. Create `.env` file

Create a `.env` file in `backend/`:

```bash
cp ../.env.example .env
```

---

### ✅ 4. Run the backend server

```bash
uvicorn main:app --reload
```

Backend will run at [http://localhost:8000](http://localhost:8000)

---

## 💻 Frontend Setup (React)

### ✅ 1. Install dependencies

```bash
cd frontend
npm install
```

### ✅ 2. Run the frontend

```bash
npm start
```

Frontend will open at [http://localhost:3000](http://localhost:3000)

> 💡 To change port, add `.env` file in `frontend/`:
>
> ```
> PORT=3500
> ```

---

## ✨ Usage Instructions

1. Go to `http://localhost:3000`
2. Enter a software requirement (e.g., "A hospital management system")
3. Click **Generate Diagram**
4. A modal will appear showing the generated UML class diagram

---

## 📄 Sample `.env.example`

```env
# backend/.env or project root
# OpenAI model name
MODEL_NAME=gpt-4o-mini

# (Optional) OpenAI API key if needed
# OPENAI_API_KEY=your-api-key-here
```

---

## 🚧 Troubleshooting & Git Tips

### 🔄 Git thinks frontend is a submodule?

```bash
git rm --cached frontend
rm -rf frontend/.git
git add frontend/
git commit -m "Fix frontend as regular folder"
git push origin main
```

### 📂 Add backend & frontend only

```bash
git add backend frontend
git commit -m "Add backend and frontend"
```

---

## 🚀 Future Improvements

- [ ] Add SVG rendering support
- [ ] User download & share buttons for diagrams
- [ ] Save diagram history with titles
- [ ] Dockerize full stack for production

---

## 📄 License

MIT License – free for personal and commercial use.
