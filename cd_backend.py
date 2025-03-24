from flask import Flask, request, redirect, session, render_template_string, jsonify
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import stripe

app = Flask(__name__)
CORS(app)
app.secret_key = 'iemj-fgeh-qbbz-jljf-lljf'  # Change this in production!

# --- STRIPE SETUP ---
stripe.api_key = 'iemj-fgeh-qbbz-jljf-lljf'  # Replace with your actual secret key

# --- DB Setup ---
DB_FILE = "cd_consulting.db"
if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        type TEXT,
        timeline TEXT,
        goals TEXT,
        submitted_at TEXT
    )''')
    conn.commit()
    conn.close()

# --- Admin Credentials (simple for demo) ---
ADMIN_USERNAME = 'cjdarbouz'
ADMIN_PASSWORD = 'Moviestar13!'  # Replace this in production!

# --- Public Submission Route ---
@app.route('/submit', methods=['POST'])
def submit_request():
    data = request.form
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO requests (name, email, type, timeline, goals, submitted_at) VALUES (?, ?, ?, ?, ?, ?)",
              (
                data.get('name'),
                data.get('email'),
                data.get('type'),
                data.get('timeline'),
                data.get('goals'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
              ))
    conn.commit()
    conn.close()
    return jsonify({"message": "Request submitted successfully."}), 200

# --- Admin Login ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect('/admin/dashboard')
        else:
            error = "Invalid credentials"
    return render_template_string(open('admin_login.html').read(), error=error)

# --- Admin Dashboard ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return open('admin_dashboard.html').read()

# --- Logout ---
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')

# --- Admin: Get All Requests (API) ---
@app.route('/admin/requests')
def admin_requests():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, email, type, timeline, goals, submitted_at FROM requests ORDER BY submitted_at DESC")
    data = [
        {
            "name": row[0],
            "email": row[1],
            "type": row[2],
            "timeline": row[3],
            "goals": row[4],
            "submitted_at": row[5]
        } for row in c.fetchall()
    ]
    conn.close()
    return jsonify(data)

# --- Stripe Payment Endpoint ---
@app.route('/admin/create-payment', methods=['POST'])
def create_payment():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')

    data = request.get_json()
    try:
        checkout = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': data['label']
                    },
                    'unit_amount': int(float(data['amount']) * 100)
                },
                'quantity': 1
            }],
            mode='payment',
            success_url='https://yourdomain.com/thank-you',
            cancel_url='https://yourdomain.com/cancelled'
        )
        return jsonify({'checkout_url': checkout.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
