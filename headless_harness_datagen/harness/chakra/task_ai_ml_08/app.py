import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

from slipsift import extract

app = Flask(__name__)

# In-memory store
SUBMISSIONS = []  # list of dicts

# Simple HTML templates (inline)
INDEX_HTML = """
<!doctype html>
<title>SlipSift Demo</title>
<h1>SlipSift – Receipt Extractor</h1>
<form method=post enctype=multipart/form-data action="/submit">
  <label>Upload receipt image (PNG/JPG): </label><input type=file name=file><br><br>
  <label>Or paste receipt text:</label><br>
  <textarea name=text rows=6 cols=60></textarea><br><br>
  <label>Preset:</label>
  <select name=preset>
    <option value="us_corner_store">US Corner Store</option>
    <option value="eu_bistro">EU Bistro</option>
    <option value="strict_audit">Strict Audit</option>
  </select><br><br>
  <input type=submit value="Extract">
</form>
<hr>
<a href="/dashboard">Dashboard (confirmed receipts)</a> | <a href="/review">Review Queue</a>
"""

RESULT_HTML = """
<!doctype html>
<title>Extraction Result</title>
<h2>Extraction Result (ID: {{rec.id}})</h2>
<form method=post action="/confirm/{{rec.id}}">
  <label>Merchant:</label> <input name=merchant value="{{rec.result.merchant}}"><br>
  <label>Date (ISO):</label> <input name=date value="{{rec.result.date}}"><br>
  <label>Total:</label> <input name=total value="{{rec.result.total}}"><br>
  <label>Currency:</label> <input name=currency value="{{rec.result.currency}}"><br>
  <label>Preset:</label> <input name=preset value="{{rec.result.preset}}" readonly><br>
  <label>Issues:</label> <textarea readonly rows=3 cols=60>{{rec.result.issues|join('\n')}}</textarea><br>
  <input type=submit value="Confirm & Save">
</form>
<a href="/">Back to start</a>
"""

DASHBOARD_HTML = """
<!doctype html>
<title>SlipSift Dashboard</title>
<h2>Confirmed Receipts</h2>
<table border=1 cellpadding=5>
  <tr><th>ID</th><th>Merchant</th><th>Date</th><th>Total</th><th>Currency</th><th>Preset</th></tr>
  {% for rec in records %}
    <tr>
      <td>{{rec.id}}</td>
      <td>{{rec.result.merchant}}</td>
      <td>{{rec.result.date}}</td>
      <td>{{rec.result.total}}</td>
      <td>{{rec.result.currency}}</td>
      <td>{{rec.result.preset}}</td>
    </tr>
  {% endfor %}
</table>
<a href="/">Home</a>
"""

REVIEW_HTML = """
<!doctype html>
<title>Review Queue</title>
<h2>Pending Review</h2>
{% if pending %}
<ul>
  {% for rec in pending %}
    <li><a href="/result/{{rec.id}}">{{rec.id}} – {{rec.result.merchant or 'unknown merchant'}}</a></li>
  {% endfor %}
</ul>
{% else %}
<p>No pending submissions.</p>
{% endif %}
<a href="/">Home</a>
"""

@app.route('/')
def index():
    return INDEX_HTML

@app.route('/submit', methods=['POST'])
def submit():
    preset = request.form.get('preset', 'us_corner_store')
    raw_text = ''
    source = ''
    # handle file upload (stub OCR)
    if 'file' in request.files and request.files['file'].filename:
        f = request.files['file']
        source = f.filename
        raw_bytes = f.read()
        # stub OCR: deterministic mapping
        from slipsift import _stub_ocr
        raw_text = _stub_ocr(raw_bytes)
    else:
        raw_text = request.form.get('text', '').strip()
        source = 'paste'
    if not raw_text:
        return 'No input provided', 400
    # run extraction
    result = extract(raw_text, preset=preset)
    rec_id = str(uuid.uuid4())
    record = {
        'id': rec_id,
        'source': source,
        'raw_text': raw_text,
        'preset': preset,
        'result': result,
        'status': 'pending',
        'submitted_at': datetime.utcnow().isoformat()
    }
    SUBMISSIONS.append(record)
    return redirect(url_for('result', rec_id=rec_id))

@app.route('/result/<rec_id>')
def result(rec_id):
    rec = next((r for r in SUBMISSIONS if r['id'] == rec_id), None)
    if not rec:
        return 'Not found', 404
    return render_template_string(RESULT_HTML, rec=rec)

@app.route('/confirm/<rec_id>', methods=['POST'])
def confirm(rec_id):
    rec = next((r for r in SUBMISSIONS if r['id'] == rec_id), None)
    if not rec:
        return 'Not found', 404
    # update fields from form
    rec['result']['merchant'] = request.form.get('merchant') or rec['result']['merchant']
    rec['result']['date'] = request.form.get('date') or rec['result']['date']
    total_val = request.form.get('total')
    try:
        rec['result']['total'] = float(total_val) if total_val else rec['result']['total']
    except ValueError:
        pass
    rec['result']['currency'] = request.form.get('currency') or rec['result']['currency']
    rec['status'] = 'confirmed'
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    confirmed = [r for r in SUBMISSIONS if r['status'] == 'confirmed']
    return render_template_string(DASHBOARD_HTML, records=confirmed)

@app.route('/review')
def review():
    pending = [r for r in SUBMISSIONS if r['status'] == 'pending']
    return render_template_string(REVIEW_HTML, pending=pending)

@app.route('/healthz')
def healthz():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Ensure the app runs on a free port (8080 default)
    port = int(os.getenv('PORT', '8080'))
    app.run(host='127.0.0.1', port=port)
""