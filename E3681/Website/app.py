import os
import json
import bcrypt
import psycopg2
import psycopg2.pool
import pandas as pd
import joblib
from datetime import datetime
from dateutil import relativedelta
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from web3 import Web3
from psycopg2.errors import UniqueViolation
from utils.report_utils import extract_text_from_pdf, extract_text_from_docx, classify_report_text
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-in-production")

# --- PostgreSQL connection pool ---
db_pool = psycopg2.pool.SimpleConnectionPool(
    1, 10,
    os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/matcare")
)

def get_db():
    conn = db_pool.getconn()
    conn.autocommit = False
    return conn

def release_db(conn):
    db_pool.putconn(conn)

# --- Web3 & Contract Setup ---
INFURA_URL    = os.getenv("INFURA_URL")
WALLET_ADDR   = os.getenv("WALLET_ADDRESS")
PRIVATE_KEY   = os.getenv("PRIVATE_KEY")
CONTRACT_ADDR = os.getenv("CONTRACT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(INFURA_URL))
contract_address = Web3.to_checksum_address(CONTRACT_ADDR)

with open("utils/abi.json") as f:
    contract_abi = json.load(f)
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# --- ML Model Setup ---
rf_model      = joblib.load('rf_model.pkl')
scaler        = joblib.load('scaler.pkl')
label_encoder = joblib.load('label_encoder.pkl')

# --- Blynk Sensor URLs ---
BLYNK           = os.getenv("BLYNK_TOKEN", "")
Pulse_URL       = f"https://blynk.cloud/external/api/get?token={BLYNK}&V0"
Glucose_URL     = f"https://blynk.cloud/external/api/get?token={BLYNK}&V1"
BP_Systolic_URL = f"https://blynk.cloud/external/api/get?token={BLYNK}&V2"
SPO2_URL        = f"https://blynk.cloud/external/api/get?token={BLYNK}&V3"
Temperature_URL = f"https://blynk.cloud/external/api/get?token={BLYNK}&V4"
Switch_URL      = f"https://blynk.cloud/external/api/get?token={BLYNK}&V9"

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_sensor_value(url):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return float(r.text.strip())
    except Exception:
        return None

def condition(Pulse, Glucose, BP_Systolic, SPO2, Temperature, Switch):
    df = pd.DataFrame([{
        'Pulse': Pulse, 'Glucose': Glucose,
        'BP_Systolic': BP_Systolic, 'SPO2': SPO2,
        'Temperature': Temperature, 'Switch': Switch,
    }])
    scaled = scaler.transform(df)
    pred = rf_model.predict(scaled)
    return label_encoder.inverse_transform(pred)[0]

def humanize_delta(past_dt):
    if past_dt.tzinfo is not None:
        past_dt = past_dt.replace(tzinfo=None)
    diff = relativedelta.relativedelta(datetime.utcnow(), past_dt)
    if diff.hours:
        return f"{diff.hours}h {diff.minutes}m ago"
    if diff.minutes:
        return f"{diff.minutes}m {diff.seconds}s ago"
    return f"{diff.seconds}s ago"

def send_blockchain_tx(fn):
    """Helper to build, sign, send and wait for a contract transaction."""
    nonce = w3.eth.get_transaction_count(WALLET_ADDR)
    tx = fn.build_transaction({
        'from': WALLET_ADDR,
        'nonce': nonce,
        'gas': 2_000_000,
        'gasPrice': w3.to_wei('10', 'gwei'),
    })
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    txhash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(txhash)
    return txhash

# --- DASHBOARD / HOME ---
@app.route('/')
def home():
    if 'mother_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
          SELECT pulse, spo2, bp, temp, glucose, timestamp
          FROM mother_readings WHERE mother_id = %s
          ORDER BY timestamp DESC LIMIT 1
        """, (session['mother_id'],))
        row = cursor.fetchone()
        mother_data = {}
        if row:
            p, s, b, t, g, ts = row
            mother_data = {'pulse': p, 'spo2': s, 'bp': b, 'temp': t, 'glucose': g,
                           'time_ago': humanize_delta(ts)}

        cursor.execute("""
          SELECT pulse, spo2, bp, temp, glucose, timestamp
          FROM mother_readings WHERE mother_id = %s
          ORDER BY timestamp DESC LIMIT 5
        """, (session['mother_id'],))
        mother_history = cursor.fetchall()

        cursor.execute("SELECT baby_id, baby_name FROM babies WHERE mother_id = %s", (session['mother_id'],))
        baby_row = cursor.fetchone()
        baby_data, baby_history, baby_name = {}, [], None

        if baby_row:
            baby_id, baby_name = baby_row
            cursor.execute("""
              SELECT pulse, spo2, bp, temp, glucose, timestamp
              FROM baby_readings WHERE baby_id = %s
              ORDER BY timestamp DESC LIMIT 1
            """, (baby_id,))
            brow = cursor.fetchone()
            if brow:
                p, s, b, t, g, ts = brow
                baby_data = {'pulse': p, 'spo2': s, 'bp': b, 'temp': t, 'glucose': g,
                             'time_ago': humanize_delta(ts)}
            cursor.execute("""
              SELECT pulse, spo2, bp, temp, glucose, timestamp
              FROM baby_readings WHERE baby_id = %s
              ORDER BY timestamp DESC LIMIT 5
            """, (baby_id,))
            baby_history = cursor.fetchall()

    finally:
        cursor.close()
        release_db(conn)

    # Serialize timestamps to string for JSON
    def serialize_history(rows):
        result = []
        for row in rows:
            result.append([row[0], row[1], row[2], row[3], row[4],
                           row[5].strftime('%Y-%m-%d %H:%M') if row[5] else ''])
        return result

    return render_template('dashboard.html',
                           mother_data=mother_data, baby_data=baby_data,
                           mother_history=serialize_history(mother_history),
                           baby_history=serialize_history(baby_history),
                           baby_name=baby_name,
                           username=session.get('username', ''))

# --- LOGIN / LOGOUT ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pw   = request.form.get('password', '')
        if not user or not pw:
            flash("Username & password required", "error")
            return redirect(url_for('login'))

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, wallet_addr, mother_id, password, username FROM mothers WHERE username=%s", (user,))
            row = cursor.fetchone()
            if row and bcrypt.checkpw(pw.encode(), row[3].encode()):
                session['user_id']   = row[0]
                session['wallet']    = row[1]
                session['mother_id'] = row[2]
                session['username']  = row[4]
                return redirect(url_for('home'))
        finally:
            cursor.close()
            release_db(conn)

        flash("Invalid credentials", "error")
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- REGISTER MOTHER ---
@app.route('/register', methods=['POST'])
def register():
    user   = request.form.get('username', '').strip()
    wallet = request.form.get('wallet', '').strip()
    pw     = request.form.get('password', '')

    if not user or not wallet or not pw:
        flash("All fields required", "error")
        return redirect(url_for('login'))

    if not w3.is_address(wallet):
        flash("Invalid wallet address format", "error")
        return redirect(url_for('login'))

    if len(pw) < 6:
        flash("Password must be at least 6 characters", "error")
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM mothers WHERE wallet_addr=%s", (wallet,))
        if cursor.fetchone():
            flash("Wallet already registered", "error")
            return redirect(url_for('login'))

        pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        wallet_cs = Web3.to_checksum_address(wallet)

        send_blockchain_tx(contract.functions.registerMother(wallet_cs))
        mother_id = contract.functions.getMotherID(wallet_cs).call()

        cursor.execute("""
          INSERT INTO mothers(wallet_addr, mother_id, username, password)
          VALUES(%s, %s, %s, %s)
        """, (wallet_cs, mother_id, user, pw_hash))
        conn.commit()
        flash("Registered successfully! Please log in.", "success")

    except UniqueViolation:
        conn.rollback()
        flash("Username or wallet already exists", "error")
    except Exception as e:
        conn.rollback()
        print("REGISTER ERROR:", e)
        flash(f"Registration failed: {str(e)}", "error")
    finally:
        cursor.close()
        release_db(conn)

    return redirect(url_for('login'))

# --- REGISTER BABY ---
@app.route('/register-baby', methods=['GET', 'POST'])
def register_baby():
    if 'mother_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name   = request.form.get('baby_name', '').strip()
        dob    = request.form.get('baby_dob', '')
        gender = request.form.get('baby_gender', '')
        wallet = session.get('wallet')

        if not name or not dob or not gender:
            flash("All fields are required", "error")
            return redirect(url_for('register_baby'))

        conn = get_db()
        cursor = conn.cursor()
        try:
            wallet_cs = Web3.to_checksum_address(wallet)
            send_blockchain_tx(contract.functions.registerBaby(wallet_cs))
            baby_id = contract.functions.getBabyID(wallet_cs).call()

            cursor.execute("""
              INSERT INTO babies(mother_id, baby_id, baby_name, baby_dob, baby_gender)
              VALUES(%s, %s, %s, %s, %s)
            """, (session['mother_id'], baby_id, name, dob, gender))
            conn.commit()
            flash(f"Baby '{name}' registered successfully!", "success")
            return redirect(url_for('home'))

        except Exception as e:
            conn.rollback()
            print("REGISTER BABY ERROR:", e)
            flash(f"Baby registration failed: {str(e)}", "error")
        finally:
            cursor.close()
            release_db(conn)

    return render_template('register_baby.html')

# --- PREDICT ---
@app.route('/predict')
def predict():
    if 'mother_id' not in session:
        return redirect(url_for('login'))

    vals = [get_sensor_value(u) for u in (
        Pulse_URL, Glucose_URL, BP_Systolic_URL, SPO2_URL, Temperature_URL, Switch_URL
    )]
    if None in vals:
        return render_template('result.html', prediction="Failed to fetch sensor data.",
                               error=True)

    prediction = condition(*vals)
    Pulse, Glucose, BP_Systolic, SPO2, Temperature, Switch = vals

    conn = get_db()
    cursor = conn.cursor()
    try:
        if int(Switch) == 1:
            cursor.execute("""
              INSERT INTO mother_readings(mother_id, pulse, spo2, bp, temp, glucose, prediction)
              VALUES(%s,%s,%s,%s,%s,%s,%s)
            """, (session['mother_id'], Pulse, SPO2, BP_Systolic, Temperature, Glucose, prediction))
        else:
            cursor.execute("SELECT baby_id FROM babies WHERE mother_id=%s", (session['mother_id'],))
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                  INSERT INTO baby_readings(baby_id, pulse, spo2, bp, temp, glucose, prediction)
                  VALUES(%s,%s,%s,%s,%s,%s,%s)
                """, (row[0], Pulse, SPO2, BP_Systolic, Temperature, Glucose, prediction))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("PREDICT STORE ERROR:", e)
    finally:
        cursor.close()
        release_db(conn)

    return render_template('result.html',
                           prediction=prediction,
                           Pulse=Pulse, Glucose=Glucose,
                           BP_Systolic=BP_Systolic, SPO2=SPO2,
                           Temperature=Temperature, Switch=int(Switch))

# --- UPLOAD & PARSE REPORT ---
@app.route('/report_upload', methods=['GET', 'POST'])
def report_upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        f = request.files.get('report')
        if not f or not allowed_file(f.filename):
            flash("Only PDF or DOCX files are accepted", "error")
            return redirect(url_for('report_upload'))

        os.makedirs('reports', exist_ok=True)
        safe_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{f.filename}"
        path = os.path.join('reports', safe_name)
        f.save(path)

        ext = f.filename.rsplit('.', 1)[-1].lower()
        try:
            text = (extract_text_from_pdf(path) if ext == 'pdf'
                    else extract_text_from_docx(path))
        except Exception as e:
            flash(f"Could not read file: {str(e)}", "error")
            return redirect(url_for('report_upload'))

        structured = classify_report_text(text)
        afi = structured.get("amniotic_fluid")
        alert = ""
        if afi is not None:
            if afi < 5:
                alert = "⚠️ Low Amniotic Fluid – Oligohydramnios risk detected"
            elif afi > 24:
                alert = "⚠️ High Amniotic Fluid – Polyhydramnios risk detected"
            else:
                alert = "✅ Amniotic Fluid is within normal range"

        return render_template('report_result.html', structured=structured, alert=alert)

    return render_template('report_upload.html')

# --- VERIFY WALLET ---
@app.route('/verify', methods=['GET', 'POST'])
def verify_wallet():
    result = None
    if request.method == 'POST':
        wallet_input = request.form.get('wallet', '').strip()
        if w3.is_address(wallet_input):
            try:
                wcs = Web3.to_checksum_address(wallet_input)
                mid = contract.functions.getMotherID(wcs).call()
                bid = contract.functions.getBabyID(wcs).call()
                result = {
                    'wallet': wcs,
                    'mother_id': mid if mid > 0 else None,
                    'baby_id':   bid if bid > 0 else None
                }
            except Exception as e:
                result = {'error': f"Blockchain error: {e}"}
        else:
            result = {'error': 'Invalid wallet address format'}
    return render_template('verify.html', result=result)

# --- HYBRID TRACKER PLACEHOLDER ---
@app.route('/hybridaction/zybTrackerStatisticsAction')
def dummy_stat_handler():
    return '', 204

if __name__ == '__main__':
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")