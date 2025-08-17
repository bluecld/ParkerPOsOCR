#!/usr/bin/env python3
"""
Minimal test version to debug the secure app issues
"""

from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)
app.secret_key = 'test-key'

@app.route('/')
def index():
    return "<h1>Test App Working!</h1>"

@app.route('/test')
def test():
    return "<h1>Test Route Working!</h1>"

@app.route('/dashboard')
def dashboard():
    try:
        return render_template('dashboard.html')
    except Exception as e:
        return f"Template error: {e}", 500

if __name__ == '__main__':
    print("🔧 Starting test app...")
    print(f"🔗 Access at: http://192.168.0.62:5002")
    app.run(host='0.0.0.0', port=5002, debug=True)
