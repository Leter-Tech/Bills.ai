from flask import Flask, render_template, request, jsonify, redirect, url_for
import google.generativeai as genai
import os
import re
import json
import traceback
import logging
import requests
import ast
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    api_key = "REMOVED"

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

@app.route('/')
def home():
    return render_template('bills_ai.html')

@app.route('/authentication')
def authentication():
    return render_template('authentication.html')
    
@app.route('/api/generate_bills', methods=['POST'])
def generate_bills():
    try:
        data = request.json
        bills_text = data.get('bills')

        if not bills_text:
            return jsonify({"error": "bills text is required"}), 400

        prompt = f"""
        The following bill info has been extracted from an image, you need to give the bill a title, total amount and additional notes.
        -To give the title, give a basic title for the bill type, for example if it's a restaurant bill then add restaurant's name, if it's a product bill then add product's name.
        -To know the bill type, try to know the bill type from the text information shared, it can be from the following bill types:
            1. Housing
            2. Insurance
            3. Transportation
            4. Credit and Loans
            5. Subscriptions
            6. Dining and Entertainment
            7. Medical
            8. Education Expenses
            9. Household Supplies
            10. Product Purchase

        -To Give amount, look for texts like total or sub total and the value in front of them, the  for example:
        
        Total: $100.21
        Sub Total: $1200.36
        Sub-Total: $1300.87
            
        -DO NOT calculate total bill amount yourself
        -DO NOT use apostrophe sign in Bill Title, for example: 
        
        Don't Give: McDonald's Restaurant
        Give: McDonald Restaurant
        
        -DO NOT give commas in Bill Amount, for example:

        Don't Give: 3,231
        Give: 3231

        -DO NOT give currency in bill amount
        
        For example:
        Title: Amount: Type:

        Bill Info:
        {bills_text}

        Format the response as a single JSON object with the following structure:
        {{
            "title": "Bill Title"
            "amount": "Total Bill Amount"
            "type": "Bill Type"
        }}

        """

        response = model.generate_content(prompt)
        logging.debug(f"Model response: {response.text}")

        cleaned_response = re.sub(r'```json\n|```', '', response.text).strip()
        print(cleaned_response)
        try:
            bill = json.loads(cleaned_response)

            if not isinstance(bill, dict) or 'title' not in bill or 'amount' not in bill or 'type' not in bill:
                raise ValueError("Bill must contain 'title', 'amount', and 'type' keys")

            return jsonify({"bill": bill})
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Failed to parse model response: {cleaned_response}")
            logging.error(f"Error: {str(e)}")
            return jsonify({"error": "Failed to parse model response"}), 500

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True)
