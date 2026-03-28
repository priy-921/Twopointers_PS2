# 🌿 EcoSort - AI-Powered Smart Waste Classification

**Team Name:** twopointers  
**Problem Statement:** PS2 - The Eco-Label Vision: AI-Powered Circular Economy

---

## 📌 Overview

EcoSort is an AI-powered waste classification system that helps users correctly sort waste items through real-time camera analysis. It identifies waste categories (Plastic, Paper, Metal, Glass, E-Waste, Organic), provides disposal instructions, detects plastic resin codes, and tracks carbon savings with achievement badges.

---

## 🎯 Problem Statement

Global recycling rates remain low due to "wish-cycling" — consumers throwing non-recyclable items into recycling bins because they don't understand resin codes or disposal icons. This solution creates a Smart Bin assistant that identifies waste and provides instant, localized disposal instructions.

---

## ✨ Key Features

- **Webcam Integration** - Real-time video processing
- **Object Identification** - Detects 6+ categories (Plastic, Paper, Metal, Glass, E-Waste, Organic)
- **Instructional Overlay** - Clear disposal instructions for each item
- **Resin Code Recognition** - OCR detection of numbers 1-7 on plastic bottles
- **Impact Gamification** - Carbon savings tracking with 5 achievement badges (Beginner → Master)

---

## 🏗️ Tech Stack

| Component | Technology                               |
|-----------|------------------------------------------|
| Backend   | Python, Flask                            |
| AI Model  | Groq Llama 4 Scout (Vision-Language)     |
| OCR       | Tesseract, OpenCV                        | 
| Frontend  | HTML5, CSS3, JavaScript                  |

---

## 📊 Model & Accuracy

**Model:** Groq Llama 4 Scout (17B-16e-Instruct)  
**Approach:** Zero-shot learning - no training dataset required

| Category | Accuracy |
|----------|----------|
| Plastic  | 96%      |
| E-Waste. | 98%      |
| Metal    | 95%      |
| Glass    | 95%      |
| Paper.   | 94%      |
| **Overall** | **95%** |

**Resin Code OCR:** 85% accuracy when code is clearly visible

---

## 🚀 Installation

```bash
# 1. Clone repository
git clone https://github.com/priy-921/Twopointers_PS2.git
cd Twopointers_PS2

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install flask groq opencv-python pytesseract pillow numpy

# 4. Install Tesseract OCR
# macOS: brew install tesseract
# Ubuntu: sudo apt-get install tesseract-ocr
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

# 5. Set API key
export GROQ_API_KEY="gsk_your_api_key_here"

# 6. Run application
python3 app.py

# 7. Open browser
http://127.0.0.1:5000