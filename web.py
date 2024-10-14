import fitz  # PyMuPDF
import openai
import os
from flask import Flask, request, render_template, redirect, url_for, flash, send_file
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

# Function to ensure the summary ends with a full stop
def ensure_full_stop(text):
    text = text.strip()
    if not text.endswith(('.', '!', '?')):
        text += '.'
    return text

# Function to summarize text using OpenAI GPT model
def summarize_text(api_key, text):
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use "gpt-4" if you have access
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Summarize the following text:\n\n{text}"}
        ],
        max_tokens=500,
        temperature=0.5
    )
    summary = response.choices[0].message['content'].strip()
    return ensure_full_stop(summary)

# Function to predict the main topic of the text
def predict_topic(api_key, text):
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use "gpt-4" if you have access
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"What is the main topic of the following text?\n\n{text}"}
        ],
        max_tokens=500,
        temperature=0.5
    )
    topic = response.choices[0].message['content'].strip()
    return topic

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        api_key = request.form['api_key']
        file = request.files['pdf_file']
        
        if file and file.filename.endswith('.pdf'):
            pdf_path = os.path.join('uploads', file.filename)
            file.save(pdf_path)

            # Extract text from PDF
            text = extract_text_from_pdf(pdf_path)
            if len(text) > 1000:
                # Summarize the text
                summary = summarize_text(api_key, text)
                
                # Predict the main topic
                topic = predict_topic(api_key, text)

                # Display the results
                return render_template('results.html', summary=summary, topic=topic, original_file_name=file.filename)
            else:
                flash("The document is too short for meaningful analysis.")
                return redirect(url_for('index'))
        else:
            flash("Please upload a valid PDF file.")
            return redirect(url_for('index'))
    
    return render_template('index.html')

from fpdf import FPDF

@app.route('/save_summary', methods=['POST'])
def save_summary():
    summary = request.form['summary']
    topic = request.form['topic']
    original_file_name = request.form['original_file_name']

    # Create a PDF filename based on the original PDF name
    base_name = os.path.splitext(original_file_name)[0]  # Remove the .pdf extension
    pdf_file_name = f"{base_name} summary.pdf"  # Create the new filename

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Summary", ln=True, align='C')
    pdf.multi_cell(0, 10, txt=summary)

    pdf.cell(200, 10, txt="Predicted Main Topic", ln=True, align='C')
    pdf.multi_cell(0, 10, txt=topic)

    # Save the PDF to a file
    pdf_file_path = os.path.join('saved_summaries', pdf_file_name)
    pdf.output(pdf_file_path)

    return send_file(pdf_file_path, as_attachment=True)

# Run the application
if __name__ == "__main__":
    app.run(debug=True)
