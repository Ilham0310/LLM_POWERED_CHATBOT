# LLM Powered Chatbot for Hospital Database

A Python project that combines a Streamlit-based hospital database chatbot with LLM-enhanced retrieval and database query support.

## Project Overview

- `final11.py`: Main application file. A Streamlit app that connects to a MySQL hospital database and provides patient, appointment, and medical record views.
- `requirements.txt`: Python package dependencies.
- `static/`: Frontend web UI assets for a chat interface.
- `templates/index.html`: HTML chat page for a separate Flask-based chatbot frontend.
- `directory.txt`: Project structure reference.

> Note: The repository contains both a Streamlit app (`final11.py`) and static frontend assets that appear to target a Flask backend. The current main entry point is `final11.py`.

## Setup Instructions

1. Install Python 3.12+.
2. Create and activate a virtual environment:
   ```bash
   python -m venv env
   .\env\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
4. Update API keys in `final11.py`:
   - `GROQ_API_KEY`
   - `GOOGLE_API_KEY`
5. Update MySQL database connection settings in `final11.py`:
   - `host`
   - `user`
   - `password`
   - `database`
6. Run the Streamlit app:
   ```bash
   streamlit run final11.py
   ```

## Usage

- Log in using valid credentials from the `Users` table.
- View patient details, appointments, and medical records through the Streamlit UI.
- If you want to use the static chat frontend, build a Flask backend endpoint at `/chat` on `http://127.0.0.1:5000`.

## Important Notes

- The project currently includes `final11.py` as the main backend app.
- `static/` and `templates/` are static frontend assets that may require a separate Flask service.
- `requirements.txt` includes the required Python libraries used by this project.

## Included Files

- `final11.py`
- `requirements.txt`
- `static/style.css`
- `static/script.js`
- `templates/index.html`
- `.gitignore`
- `README.md`

## License

This repository does not include a license file. Add one if you want to share the project publicly under a specific license.
