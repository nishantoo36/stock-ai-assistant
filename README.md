# 📈 AI Investment Assistant

A beginner-friendly AI-powered stock investment assistant built with Python and Streamlit.

This tool helps users:

- Search stocks and ETFs easily
- Get BUY / HOLD / SELL recommendations
- Understand investment suggestions in simple language
- View stock price trends
- Learn why the AI made a recommendation

The application is designed for personal use on your laptop.

---

# 🚀 Features

✅ Search by company name

✅ Supports:
- US stocks
- Indian stocks
- ETFs

✅ Beginner-friendly recommendations

✅ BUY / HOLD / SELL suggestions

✅ Confidence score

✅ Risk analysis

✅ Price trend chart

✅ Detailed investment insights

---

# 🖥️ System Requirements

Recommended environment:

| Requirement | Recommended |
|---|---|
| Operating System | macOS / Windows / Linux |
| Python Version | Python 3.10+ |
| RAM | 8 GB minimum |
| Internet | Required for live stock data |

---

# 🐍 Install Python

Download Python:

https://www.python.org/downloads/

IMPORTANT:

During installation enable:

```text
Add Python to PATH
```

Verify installation:

```bash
python3 --version
```

---

# 📦 Clone Repository

```bash
git clone https://github.com/nishantoo36/stock-ai-assistant.git
```

Go into project:

```bash
cd stock-ai-assistant
```

---

# 📁 Create Virtual Environment (Recommended)

## macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## Windows

```bash
python -m venv venv
venv\Scripts\activate
```

---

# 📥 Install Dependencies

## Main Installation

```bash
pip install -r requirements.txt
```

---

# ⚠️ pandas-ta Installation Issue (Mac M-Series)

If pandas-ta installation fails:

```bash
pip install git+https://github.com/twopirllc/pandas-ta.git
```

---

# ▶️ Run Application

```bash
streamlit run app.py
```

Application opens automatically in browser.

If not:

Open manually:

```text
http://localhost:8501
```

---

# 🔍 Example Searches

You can search:

- Nvidia
- Apple
- Tesla
- Tata Gold
- Reliance
- Infosys
- TCS
- Bitcoin

---

# 📊 How Recommendations Work

The AI analyzes:

- Historical stock prices
- Market momentum
- Trend direction
- Technical indicators

Then it provides:

- BUY
- HOLD
- SELL

recommendations with confidence and risk analysis.

---

# 🧠 Beginner Friendly Design

This tool avoids complicated trading jargon.

Instead of showing confusing technical analysis,
it explains recommendations in simple language.

---

# ⚠️ Important Disclaimer

This project is for educational and personal investment research purposes only.

No AI system can predict stock markets perfectly.

Always do your own research before investing.

---

# 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Streamlit | Frontend UI |
| yfinance | Stock market data |
| pandas-ta | Technical indicators |
| YahooQuery | Smart stock search |
| Python | Backend logic |

---

# 📌 Future Improvements

Planned features:

- AI news sentiment analysis
- Portfolio tracking
- Watchlist management
- Telegram alerts
- Long-term investment scoring
- Market sentiment analysis

---

# 👨‍💻 Author

Created by Nishant Patel