# 🩺 MatCare — Real-Time IoT Maternal Health Monitoring System

MatCare is a real-time health monitoring platform designed for maternal and newborn care, combining IoT, backend systems, machine learning, and blockchain for secure and intelligent healthcare tracking.

---

## 🚀 Features

- 📡 Real-time monitoring of vital parameters using IoT (ESP32)
- 📊 Dual-channel tracking for both mother and newborn
- 🧠 Machine learning-based health state prediction
- 📄 Medical report parsing (PDF/DOCX)
- 🔗 Blockchain-based patient identity registration

---

## 🧠 Core Idea

MatCare integrates multiple technologies to provide:

> Continuous monitoring + intelligent prediction + secure data handling

It aims to assist in early detection of potential health risks during pregnancy and postnatal care.

---

## 🏗️ System Architecture


ESP32 Sensors → Blynk API → Backend (Flask) → ML Model → Database → Blockchain


---

## 🔧 Components

### 📡 IoT Layer
- ESP32 sensors collect real-time vitals (heart rate, temperature, etc.)
- Data transmitted via Blynk APIs

### 🧠 Backend & Processing
- Flask backend handles data ingestion and processing
- Stores structured health data in PostgreSQL

### 🤖 Machine Learning
- Random Forest classifier predicts health conditions
- Uses real-time + historical data

### 📄 Report Parsing
- Extracts clinical data (e.g., amniotic fluid levels, gestational info)
- Supports PDF/DOCX inputs

### 🔗 Blockchain Integration
- Patient identity stored on Ethereum (Sepolia)
- Ensures tamper-resistant records

---

## 🛠️ Tech Stack

- **Backend:** Flask (Python)  
- **IoT:** ESP32, Blynk API  
- **ML:** Scikit-learn (Random Forest)  
- **Database:** PostgreSQL  
- **Blockchain:** Ethereum (Sepolia), Web3.py, Solidity  
- **Parsing:** pdfplumber  

---

## ▶️ Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/matcare.git
cd matcare
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Run backend
```bash
python app.py
```

💡 Use Cases
Remote maternal health monitoring
Early risk detection during pregnancy
Secure medical data handling
IoT-based healthcare systems

🔮 Future Improvements
Real-time alert system for critical conditions
Mobile application integration
Advanced ML models for better prediction accuracy
Multi-patient dashboard for hospitals

🧑‍💻 Author

Rishikesh R
Cybersecurity • Backend Systems • IoT & ML

🔗 https://linkedin.com/in/rishikesh-r-196b5a290
🌐 https://rishikesh-r.vercel.app
