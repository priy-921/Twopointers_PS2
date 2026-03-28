from flask import Flask, render_template, request, jsonify
import base64
import json
import re
from groq import Groq
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io

app = Flask(__name__)

GROQ_API_KEY = "WRITE_YOUR_API_KEY_HERE"  # Replace with your actual Groq API key

client = Groq(api_key=GROQ_API_KEY)

def extract_resin_code(image_data):
    """Extract resin code from image with strict validation"""
    try:
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))
        
        # Crop to center area
        width, height = img.size
        center_x, center_y = width // 2, height // 2
        crop_size = min(width, height) // 3
        
        cropped = img.crop((
            max(0, center_x - crop_size),
            max(0, center_y - crop_size),
            min(width, center_x + crop_size),
            min(height, center_y + crop_size)
        ))
        
        # Enhance image
        cropped = cropped.convert('L')
        cropped = ImageEnhance.Contrast(cropped).enhance(4.0)
        cropped = cropped.filter(ImageFilter.SHARPEN)
        
        threshold = 100
        cropped = cropped.point(lambda x: 0 if x < threshold else 255, '1')
        
        # OCR with strict settings
        custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=1234567 -c textord_min_linesize=2.5'
        text = pytesseract.image_to_string(cropped, config=custom_config)
        
        print("OCR TEXT FROM CENTER:", text.strip())
        
        # ONLY look for numbers 1-7 (strict range)
        resin_pattern = r'\b([1-7])\b'
        matches = re.findall(resin_pattern, text)
        
        valid_resin = None
        for match in matches:
            # Check if number appears alone on a line
            lines = text.split('\n')
            for line in lines:
                if match in line and len(line.strip()) <= 3:
                    valid_resin = match
                    break
            if valid_resin:
                break
        
        if valid_resin:
            resin_code = valid_resin
            resin_types = {
                '1': 'PET',
                '2': 'HDPE',
                '3': 'PVC',
                '4': 'LDPE',
                '5': 'PP',
                '6': 'PS',
                '7': 'Other'
            }
            print(f"✓ VALID RESIN CODE FOUND: {resin_code} ({resin_types.get(resin_code, 'Unknown')})")
            return resin_code, resin_types.get(resin_code, 'Unknown')
        
        return None, None
        
    except Exception as e:
        print(f"OCR Error: {e}")
        return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        image_data = data['image']
        
        resin_code, resin_type = extract_resin_code(image_data)
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        resin_info = ""
        if resin_code:
            resin_info = f"""
✓ VERIFIED RESIN CODE DETECTED: {resin_code} ({resin_type})
This code was physically scanned from the item. ONLY apply to PLASTIC items.
"""
        
        prompt = f"""Analyze the image and identify the waste item. Return ONLY valid JSON.

{resin_info}

DYNAMIC CONFIDENCE SCORING - Base on actual image quality:
- 98-100%: Crystal clear, perfect lighting, entire item visible
- 95-97%: Clear view, good lighting, easily identifiable  
- 90-94%: Slightly blurry or moderate lighting, but identifiable
- 85-89%: Partially visible or poor lighting
- 80-84%: Very blurry or obstructed, but can guess
- Below 80%: Extremely poor quality

CLASSIFICATION RULES:
- Plastic bottle, container, packaging → Plastic → Blue Bin
- Sunscreen bottle, lotion bottle, glue bottle → Plastic → Blue Bin
- Glass bottle, jar → Glass → Blue Bin
- Metal can, water bottle, container → Metal → Blue Bin
- Paper, cardboard, notebook → Paper → Blue Bin
- Mobile phone, charger, cable, battery → E-Waste → Red Bin
- Person with no waste → Human → No bin

CRITICAL RULES:
- Resin codes ONLY apply to PLASTIC items
- If resin code detected on metal, glass, or paper → IGNORE it
- Confidence must vary based on image quality (not always 95)

Return JSON:
{{
    "category": "Plastic/Glass/Metal/Paper/Organic/E-Waste/Human",
    "itemName": "Brief description",
    "resinCode": {f'"{resin_code}"' if resin_code else 'null'},
    "resinType": {f'"{resin_type}"' if resin_type else 'null'},
    "recyclable": true/false,
    "bin": "Blue Bin/Green Bin/Red Bin/Black Bin/None",
    "binColor": "blue/green/red/black/none",
    "instruction": "Short disposal steps",
    "specialNote": null,
    "carbonSaved": 50,
    "confidence": 95.0
}}

Return ONLY JSON."""

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            max_tokens=300,
            temperature=0.2
        )

        raw = response.choices[0].message.content.strip()
        print("RAW RESPONSE:", raw)

        raw = re.sub(r'```json\s*', '', raw)
        raw = re.sub(r'```\s*', '', raw)
        raw = raw.strip()
        
        json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        
        if json_match:
            result = json.loads(json_match.group())
            
            # Human category handling
            if result.get('category') == 'Human':
                result = {
                    "category": "Human",
                    "itemName": "No waste detected",
                    "resinCode": None,
                    "resinType": None,
                    "recyclable": False,
                    "bin": "None",
                    "binColor": "none",
                    "instruction": "No waste item detected. Position waste in frame.",
                    "specialNote": None,
                    "carbonSaved": 0,
                    "confidence": min(result.get('confidence', 99.0), 99.0)
                }
            else:
                # CRITICAL: Resin code ONLY applies to PLASTIC
                if resin_code and result.get('category') == 'Plastic':
                    result['resinCode'] = resin_code
                    result['resinType'] = resin_type
                    
                    # Apply resin code rules
                    if resin_code in ['1', '2', '5']:
                        result['recyclable'] = True
                        result['bin'] = "Blue Bin"
                        result['binColor'] = "blue"
                        result['carbonSaved'] = 120 if 'bottle' in result.get('itemName', '').lower() else 80
                        result['instruction'] = f"Resin code {resin_code} ({resin_type}) detected. Clean and place in Blue Bin."
                        # Boost confidence for clear resin code detection
                        if result.get('confidence', 0) < 95:
                            result['confidence'] = min(result.get('confidence', 0) + 5, 98)
                    elif resin_code == '6':
                        result['recyclable'] = False
                        result['bin'] = "Black Bin"
                        result['binColor'] = "black"
                        result['carbonSaved'] = 0
                        result['instruction'] = "Styrofoam/PS is not recyclable. Dispose in Black Bin."
                    elif resin_code in ['3', '4', '7']:
                        result['recyclable'] = False
                        result['bin'] = "Check Local Facilities"
                        result['binColor'] = "black"
                        result['carbonSaved'] = 0
                        result['instruction'] = f"Resin code {resin_code} has limited recyclability. Check local facilities."
                elif resin_code and result.get('category') != 'Plastic':
                    # Resin code detected on non-plastic - IGNORE it
                    print(f"⚠ IGNORING resin code {resin_code} on {result.get('category')} item")
                    result['resinCode'] = None
                    result['resinType'] = None
                
                # Fix carbonSaved
                if 'carbonSaved' in result and result['carbonSaved'] is not None:
                    if isinstance(result['carbonSaved'], str):
                        numbers = re.findall(r'\d+', result['carbonSaved'])
                        result['carbonSaved'] = int(numbers[0]) if numbers else 50
                    else:
                        result['carbonSaved'] = int(result['carbonSaved'])
                else:
                    result['carbonSaved'] = 50
                
                # Fix recyclable
                if 'recyclable' in result and result['recyclable'] is not None:
                    result['recyclable'] = bool(result['recyclable'])
                else:
                    result['recyclable'] = True if result.get('category') in ['Plastic', 'Glass', 'Metal', 'Paper'] else False
                
                # Fix confidence - keep dynamic value
                if 'confidence' in result and result['confidence'] is not None:
                    if isinstance(result['confidence'], str):
                        numbers = re.findall(r'\d+\.?\d*', result['confidence'])
                        result['confidence'] = float(numbers[0]) if numbers else 90.0
                    else:
                        result['confidence'] = float(result['confidence'])
                else:
                    result['confidence'] = 90.0
                
                # Cap confidence at 99
                if result['confidence'] > 99:
                    result['confidence'] = 99.0
                
                # Fix binColor
                if 'binColor' not in result or result['binColor'] is None:
                    bin_map = {'Blue Bin': 'blue', 'Green Bin': 'green', 'Red Bin': 'red', 'Black Bin': 'black', 'Check Local Facilities': 'black', 'None': 'none'}
                    result['binColor'] = bin_map.get(result.get('bin', ''), 'none')
                
                # Fix instruction
                if 'instruction' not in result or result['instruction'] is None:
                    if result.get('category') == 'Plastic':
                        result['instruction'] = "1. Remove cap 2. Rinse 3. Place in Blue Bin"
                    elif result.get('category') == 'Glass':
                        result['instruction'] = "1. Rinse 2. Remove cap 3. Place in Blue Bin"
                    elif result.get('category') == 'Metal':
                        result['instruction'] = "1. Clean 2. Crush 3. Place in Blue Bin"
                    elif result.get('category') == 'Paper':
                        result['instruction'] = "1. Flatten 2. Remove non-paper 3. Place in Blue Bin"
                    elif result.get('category') == 'E-Waste':
                        result['instruction'] = "Take to designated e-waste collection center"
                        result['carbonSaved'] = 150
                    else:
                        result['instruction'] = "Place in appropriate bin"
                
                # Ensure e-waste has correct values
                if result.get('category') == 'E-Waste':
                    result['bin'] = "Red Bin"
                    result['binColor'] = "red"
                    result['recyclable'] = True
                    if result.get('carbonSaved', 0) < 100:
                        result['carbonSaved'] = 150
                    # E-waste confidence is usually high
                    if result.get('confidence', 0) < 95:
                        result['confidence'] = 97.0
        else:
            result = {
                "category": "Unknown",
                "itemName": "Unable to identify",
                "resinCode": None,
                "resinType": None,
                "recyclable": False,
                "bin": "Unknown",
                "binColor": "none",
                "instruction": "Scan again with better lighting",
                "specialNote": None,
                "carbonSaved": 0,
                "confidence": 0.0
            }

        return jsonify(result)

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "category": "Error",
            "itemName": "Error occurred",
            "resinCode": None,
            "resinType": None,
            "recyclable": False,
            "bin": "Error",
            "binColor": "none",
            "instruction": "Please try again",
            "specialNote": str(e),
            "carbonSaved": 0,
            "confidence": 0.0
        })

if __name__ == '__main__':
    app.run(debug=True)
