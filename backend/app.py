from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import pandas as pd
import os
import tempfile
from flask_cors import CORS
import io
import re
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_account_details(text):
    details = {}
    patterns = {
        'account_no': r'Account No\s*:\s*(\d+)',
        'account_name': r'A/C Name\s*:\s*(.*?)\n',
        'address': r'Address\s*:\s*(.*?)\nCity',
        'open_date': r'Open Date\s*:\s*(\d{2}-\d{2}-\d{4})',
        'sanction_limit': r'Sanction Limit\s*:\s*(.*?)\n',
        'interest_rate': r'Interest Rate\s*:\s*(.*?)\n'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            details[key] = match.group(1).strip()
    
    return details

def extract_transactions(text):
    transactions = []
    # Match date, description, debit, credit, balance
    pattern = r'(\d{2}-[A-Za-z]{3}-\d{4})\s+(.*?)\s+([\d,]+\.\d{2}(?:Dr|Cr)?)?\s+([\d,]+\.\d{2})?\s+([\d,]+\.\d{2}(?:Dr|Cr))'
    
    for match in re.finditer(pattern, text):
        date = match.group(1)
        description = match.group(2).strip()
        debit = match.group(3) if match.group(3) else ''
        credit = match.group(4) if match.group(4) else ''
        balance = match.group(5)
        
        transactions.append({
            'Date': date,
            'Description': description,
            'Debit': debit.replace('Dr', '').replace(',', '') if debit else '',
            'Credit': credit.replace(',', '') if credit else '',
            'Balance': balance.replace('Dr', '').replace('Cr', '').replace(',', '')
        })
    
    return transactions

def process_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    
    for page in doc:
        text += page.get_text()
    
    doc.close()
    
    # Extract account details
    account_details = extract_account_details(text)
    
    # Extract transactions
    transactions = extract_transactions(text)
    
    return {
        'account_details': account_details,
        'transactions': transactions
    }

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(filepath)
        data = process_pdf(filepath)
        
        if not data['transactions']:
            return jsonify({"error": "No transactions found in the PDF"}), 400
        
        # Create Excel file in memory
        excel_output = io.BytesIO()
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            # Account Details sheet
            account_df = pd.DataFrame.from_dict(data['account_details'], orient='index', columns=['Value'])
            account_df.to_excel(writer, sheet_name='Account Details')
            
            # Transactions sheet
            transactions_df = pd.DataFrame(data['transactions'])
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
        
        # Prepare the response
        excel_output.seek(0)
        response = send_file(
            excel_output,
            as_attachment=True,
            download_name=f"{filename.replace('.pdf', '')}_statement.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        return response
        
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        # Clean up the PDF file
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)