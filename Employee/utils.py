from num2words import num2words  
def convert_number_to_words(number):
    return num2words(number)
import re
import io
from pdfminer.high_level import extract_text as extract_pdf_text
import docx

def extract_text_from_file(uploaded_file):
    filename = uploaded_file.name.lower()
    text = ""
    
    try:
        # Reset file pointer to the beginning just in case
        uploaded_file.seek(0)
        
        if filename.endswith('.pdf'):
            # FIX: Convert Django's file object to a standard BytesIO stream
            file_stream = io.BytesIO(uploaded_file.read())
            text = extract_pdf_text(file_stream)
            
        elif filename.endswith('.docx'):
            # python-docx handles Django file objects better, but BytesIO is safer
            file_stream = io.BytesIO(uploaded_file.read())
            doc = docx.Document(file_stream)
            text = "\n".join([para.text for para in doc.paragraphs])
            
    except Exception as e:
        print(f"Error parsing file: {e}")
        return ""
    
    return text

def parse_resume_data(text):
    data = {}
    
    # 1. Extract Email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_match = re.search(email_pattern, text)
    if email_match:
        data['email'] = email_match.group(0)

    # 2. Extract Mobile Number
    # Regex for 10-digit numbers, optionally starting with +91 or 0
    phone_pattern = r'(?:\+91[\-\s]?)?(?:0)?\d{10}'
    phone_matches = re.findall(phone_pattern, text)
    
    if phone_matches:
        # Filter to find the most likely candidate (usually the first valid one)
        for number in phone_matches:
            # Clean non-digit chars
            clean_num = re.sub(r'\D', '', number)
            # If it's longer than 10 digits (like 919876543210), slice the last 10
            if len(clean_num) > 10:
                clean_num = clean_num[-10:]
            
            if len(clean_num) == 10:
                data['mobile'] = clean_num
                break

    # 3. Extract Name (Basic Heuristic)
    # Split by lines and look for the first non-empty line that isn't a header
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        for line in lines[:5]: # Check first 5 lines only
            lower_line = line.lower()
            if "resume" not in lower_line and "cv" not in lower_line and "curriculum" not in lower_line:
                # Assuming the name is reasonably short
                if len(line) < 50: 
                    data['name'] = line
                    break

    # 4. Extract Gender (Simple keyword search)
    text_lower = text.lower()
    if re.search(r'\b(female|mrs\.|ms\.)\b', text_lower):
        data['gender'] = 'Female'
    elif re.search(r'\b(male|mr\.)\b', text_lower):
        data['gender'] = 'Male'

    return data