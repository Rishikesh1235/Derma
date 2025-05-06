from flask import Flask, request, render_template, jsonify
import os
import csv
import pandas as pd
from datetime import datetime


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_data_to_csv(data_dict):
    csv_file_path = os.path.join(UPLOAD_FOLDER, 'data.csv')
    file_exists = os.path.isfile(csv_file_path)
    
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data_dict.keys())
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(data_dict)

def save_prediction_to_csv(prediction_data):
    predictions_file = os.path.join(UPLOAD_FOLDER, 'predictions.csv')
    file_exists = os.path.isfile(predictions_file)
    
    # Add timestamp and patient info to predictions
    prediction_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(predictions_file, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            'timestamp', 'patient_id', 'age', 'gender',
            'acne_probability', 'rashes_probability', 'hyperpigmentation_probability',
            'predicted_condition', 'confidence_score'
        ])
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(prediction_data)

def save_feedback_to_csv(feedback_data):
    feedback_file = os.path.join(UPLOAD_FOLDER, 'feedback.csv')
    file_exists = os.path.isfile(feedback_file)
    
    with open(feedback_file, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            'timestamp', 'patient_id', 'disease', 'original_probability',
            'feedback_status', 'correction_text'
        ])
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(feedback_data)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_data():
    # Get data from form with correct field names
    age = request.form['age']
    gender = request.form['gender']
    city = request.form['city']
    country = request.form['country']
    description = request.form['description']
    skin_history = request.form['skin_history']
    lifestyle = request.form['lifestyle']
    genetic_history = request.form['genetic_history']
    
    # Handle multiple images
    image1 = request.files['image1']
    image2 = request.files['image2']
    image3 = request.files['image3']
    lab_report = request.files['lab_report']

    # Save images
    for image in [image1, image2, image3]:
        if image:
            image_path = os.path.join(UPLOAD_FOLDER, image.filename)
            image.save(image_path)

    # Save lab report
    if lab_report:
        report_path = os.path.join(UPLOAD_FOLDER, lab_report.filename)
        lab_report.save(report_path)

    # Save data to CSV
    save_data_to_csv({
        'age': age,
        'gender': gender,
        'city': city,
        'country': country,
        'description': description,
        'skin_history': skin_history,
        'lifestyle': lifestyle,
        'genetic_history': genetic_history,
        'image1': image1.filename if image1 else '',
        'image2': image2.filename if image2 else '',
        'image3': image3.filename if image3 else '',
        'lab_report': lab_report.filename if lab_report else ''
    })

    return "Data successfully saved!"

@app.route('/view-data')
def view_data():
    csv_file_path = os.path.join(UPLOAD_FOLDER, 'data.csv')
    if os.path.exists(csv_file_path):
        data = pd.read_csv(csv_file_path)
        return data.to_html()  # Display data as an HTML table
    else:
        return "No data available."

@app.route('/output', methods = ['POST'])
def output():
    return render_template('output.html')

@app.route('/predict', methods=['POST'])
def predict():
    # Example data (replace with actual predictions from your AI model)
    predictions = {
        "Acne": 35,
        "Rashes": 20,
        "Hyperpigmentation": 45
    }
    
    # Get the highest probability prediction
    predicted_condition = max(predictions.items(), key=lambda x: x[1])[0]
    confidence_score = max(predictions.values())
    
    # Generate patient ID
    patient_id = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create prediction data dictionary
    prediction_data = {
        'patient_id': patient_id,
        'age': request.form.get('age', 'N/A'),
        'gender': request.form.get('gender', 'N/A'),
        'acne_probability': predictions['Acne'],
        'rashes_probability': predictions['Rashes'],
        'hyperpigmentation_probability': predictions['Hyperpigmentation'],
        'predicted_condition': predicted_condition,
        'confidence_score': confidence_score
    }
    
    # Save prediction to CSV
    save_prediction_to_csv(prediction_data)
    
    # Include patient_id in response
    response_data = {
        'predictions': predictions,
        'patient_id': patient_id
    }
    
    return jsonify(response_data)

@app.route('/view-predictions', methods =['GET','POST'])
def view_predictions():
    predictions_file = os.path.join(UPLOAD_FOLDER, 'predictions.csv')
    if os.path.exists(predictions_file):
        data = pd.read_csv(predictions_file)
        return render_template('predictions.html', predictions=data.to_dict('records'))
    else:
        return "No predictions available."

@app.route('/feedback/<patient_id>')
def feedback(patient_id):
    # Get the predictions for this patient
    predictions_file = os.path.join(UPLOAD_FOLDER, 'predictions.csv')
    if os.path.exists(predictions_file):
        df = pd.read_csv(predictions_file)
        patient_data = df[df['patient_id'] == patient_id].iloc[0]
        
        predictions = {
            'Acne': {
                'probability': patient_data['acne_probability'],
                'reasoning': 'Based on the presence of inflammatory papules and pustules, ' +
                           'combined with the patient\'s age and skin history.'
            },
            'Rashes': {
                'probability': patient_data['rashes_probability'],
                'reasoning': 'Analysis of skin texture patterns and distribution of affected areas ' +
                           'suggests possible inflammatory response.'
            },
            'Hyperpigmentation': {
                'probability': patient_data['hyperpigmentation_probability'],
                'reasoning': 'Evaluation of skin color variations and patient\'s reported ' +
                           'sun exposure history indicates possible melanin irregularities.'
            }
        }
        
        return render_template('feedback.html', predictions=predictions, patient_id=patient_id)
    
    return "Patient data not found", 404

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    patient_id = request.form['patient_id']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Process feedback for each disease
    for disease in ['Acne', 'Rashes', 'Hyperpigmentation']:
        feedback_status = request.form.get(f'feedback_{disease}')
        if feedback_status:
            feedback_data = {
                'timestamp': timestamp,
                'patient_id': patient_id,
                'disease': disease,
                'original_probability': request.form.get(f'probability_{disease}', ''),
                'feedback_status': feedback_status,
                'correction_text': request.form.get(f'correction_{disease}', '')
            }
            save_feedback_to_csv(feedback_data)
    
    return "Feedback submitted successfully!"

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    # Get form data
    name = request.form['name']
    email = request.form['email']
    subject = request.form['subject']
    message = request.form['message']
    
    # Save contact form submission to CSV
    contact_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'name': name,
        'email': email,
        'subject': subject,
        'message': message
    }
    
    contact_file = os.path.join(UPLOAD_FOLDER, 'contact_submissions.csv')
    file_exists = os.path.isfile(contact_file)
    
    with open(contact_file, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=contact_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(contact_data)
    
    return "Message sent successfully!"

if __name__ == '__main__':
    app.run(debug=True)

