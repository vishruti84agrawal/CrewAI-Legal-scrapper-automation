#!/usr/bin/env python3
"""
Dedicated CAPTCHA solver for Elite Posting website
Supports multiple solving methods:
1. Vision LLM (GPT-4o/Claude 3.5 Sonnet) - Highest accuracy
2. CapSolver/2Captcha API - Most reliable for production
3. Enhanced OpenCV + OCR - Local processing with noise removal
"""
import os
import base64
import time
import requests
from pathlib import Path

# ==============================================================================
# METHOD 1: Vision LLM Approach (Highest Intelligence)
# ==============================================================================

def solve_with_vision_llm(image_path, model="gpt-4o", api_key=None):
    """
    Solve CAPTCHA using Vision-capable LLM (GPT-4o or Claude 3.5 Sonnet)
    
    Args:
        image_path: Path to CAPTCHA image
        model: "gpt-4o" or "claude-3-5-sonnet"
        api_key: OpenAI or Anthropic API key (reads from env if not provided)
    
    Returns:
        Solved CAPTCHA text or None
    """
    print(f"\n🤖 Using Vision LLM ({model}) to solve CAPTCHA...")
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return None
    
    # Encode image to base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    try:
        if model.startswith("gpt"):
            return _solve_with_openai(base64_image, model, api_key)
        elif model.startswith("claude"):
            return _solve_with_anthropic(base64_image, model, api_key)
        else:
            print(f"❌ Unsupported model: {model}")
            return None
    except Exception as e:
        print(f"❌ Vision LLM failed: {e}")
        return None

def _solve_with_openai(base64_image, model="gpt-4o", api_key=None):
    """Solve CAPTCHA using OpenAI GPT-4o Vision"""
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return None
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract ONLY the alphanumeric characters from this CAPTCHA image. Return ONLY the code with no explanation, no spaces, no punctuation. Just the characters you see."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        captcha_text = result['choices'][0]['message']['content'].strip()
        # Clean the result
        captcha_text = ''.join(c for c in captcha_text if c.isalnum())
        print(f"✅ GPT-4o result: {captcha_text}")
        return captcha_text
    else:
        print(f"❌ OpenAI API error: {response.status_code} - {response.text}")
        return None

def _solve_with_anthropic(base64_image, model="claude-3-5-sonnet-20241022", api_key=None):
    """Solve CAPTCHA using Anthropic Claude 3.5 Sonnet Vision"""
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return None
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": model,
        "max_tokens": 50,
        "temperature": 0.1,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": "Extract ONLY the alphanumeric characters from this CAPTCHA image. Return ONLY the code with no explanation, no spaces, no punctuation. Just the characters you see."
                    }
                ]
            }
        ]
    }
    
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        captcha_text = result['content'][0]['text'].strip()
        # Clean the result
        captcha_text = ''.join(c for c in captcha_text if c.isalnum())
        print(f"✅ Claude 3.5 Sonnet result: {captcha_text}")
        return captcha_text
    else:
        print(f"❌ Anthropic API error: {response.status_code} - {response.text}")
        return None

# ==============================================================================
# METHOD 2: CapSolver/2Captcha API Approach (Most Reliable)
# ==============================================================================

def solve_with_capsolver(image_path, api_key=None):
    """
    Solve CAPTCHA using CapSolver API
    Sign up at: https://www.capsolver.com/
    Cost: ~$0.001 per solve, 99%+ accuracy
    
    Args:
        image_path: Path to CAPTCHA image
        api_key: CapSolver API key (reads from CAPSOLVER_API_KEY env if not provided)
    
    Returns:
        Solved CAPTCHA text or None
    """
    print(f"\n🔑 Using CapSolver API to solve CAPTCHA...")
    
    api_key = api_key or os.getenv("CAPSOLVER_API_KEY")
    if not api_key:
        print("❌ CAPSOLVER_API_KEY not found in environment")
        return None
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return None
    
    # Encode image to base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    try:
        # Create task
        payload = {
            "clientKey": api_key,
            "task": {
                "type": "ImageToTextTask",
                "body": base64_image,
                "module": "common",  # or "queueit" for specific types
                "score": 0.8,
                "case": True
            }
        }
        
        response = requests.post(
            "https://api.capsolver.com/createTask",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ CapSolver API error: {response.status_code}")
            return None
        
        result = response.json()
        if result.get("errorId") != 0:
            print(f"❌ CapSolver error: {result.get('errorDescription')}")
            return None
        
        task_id = result.get("taskId")
        print(f"⏳ Task created: {task_id}")
        
        # Poll for result
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(2)
            
            check_payload = {
                "clientKey": api_key,
                "taskId": task_id
            }
            
            check_response = requests.post(
                "https://api.capsolver.com/getTaskResult",
                json=check_payload,
                timeout=30
            )
            
            if check_response.status_code == 200:
                check_result = check_response.json()
                
                if check_result.get("status") == "ready":
                    captcha_text = check_result.get("solution", {}).get("text", "")
                    print(f"✅ CapSolver result: {captcha_text}")
                    return captcha_text
                elif check_result.get("status") == "failed":
                    print(f"❌ CapSolver task failed")
                    return None
            
            print(f"⏳ Waiting for result... ({attempt + 1}/{max_attempts})")
        
        print("❌ CapSolver timeout")
        return None
        
    except Exception as e:
        print(f"❌ CapSolver failed: {e}")
        return None

def solve_with_2captcha(image_path, api_key=None):
    """
    Solve CAPTCHA using 2Captcha API
    Sign up at: https://2captcha.com/
    Cost: ~$0.001 per solve, 99%+ accuracy
    
    Args:
        image_path: Path to CAPTCHA image
        api_key: 2Captcha API key (reads from TWOCAPTCHA_API_KEY env if not provided)
    
    Returns:
        Solved CAPTCHA text or None
    """
    print(f"\n🔑 Using 2Captcha API to solve CAPTCHA...")
    
    api_key = api_key or os.getenv("TWOCAPTCHA_API_KEY")
    if not api_key:
        print("❌ TWOCAPTCHA_API_KEY not found in environment")
        return None
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return None
    
    # Encode image to base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    try:
        # Submit CAPTCHA
        submit_url = "http://2captcha.com/in.php"
        params = {
            "key": api_key,
            "method": "base64",
            "body": base64_image,
            "json": 1
        }
        
        response = requests.post(submit_url, data=params, timeout=30)
        result = response.json()
        
        if result.get("status") != 1:
            print(f"❌ 2Captcha error: {result.get('request')}")
            return None
        
        captcha_id = result.get("request")
        print(f"⏳ Task created: {captcha_id}")
        
        # Poll for result
        result_url = "http://2captcha.com/res.php"
        max_attempts = 30
        
        for attempt in range(max_attempts):
            time.sleep(3)
            
            params = {
                "key": api_key,
                "action": "get",
                "id": captcha_id,
                "json": 1
            }
            
            response = requests.get(result_url, params=params, timeout=30)
            result = response.json()
            
            if result.get("status") == 1:
                captcha_text = result.get("request")
                print(f"✅ 2Captcha result: {captcha_text}")
                return captcha_text
            elif result.get("request") != "CAPCHA_NOT_READY":
                print(f"❌ 2Captcha error: {result.get('request')}")
                return None
            
            print(f"⏳ Waiting for result... ({attempt + 1}/{max_attempts})")
        
        print("❌ 2Captcha timeout")
        return None
        
    except Exception as e:
        print(f"❌ 2Captcha failed: {e}")
        return None

# ==============================================================================
# METHOD 3: Enhanced OpenCV + OCR Approach (Local Processing)
# ==============================================================================

def clean_image_for_ocr(image_path):
    """
    Advanced image preprocessing using OpenCV to remove CAPTCHA noise
    This significantly improves OCR accuracy on distorted images
    
    Args:
        image_path: Path to original CAPTCHA image
    
    Returns:
        Path to cleaned image
    """
    try:
        import cv2
        import numpy as np
        
        # Load image in grayscale
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            print(f"❌ Failed to load image with OpenCV: {image_path}")
            return image_path
        
        # 1. Increase contrast and rescale (Otsu's Binarization)
        _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 2. Remove Noise (Morphological Operations)
        kernel = np.ones((2, 2), np.uint8)
        # Erode to thin the noise lines, then dilate to restore character thickness
        processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # 3. Additional noise removal with median blur
        processed = cv2.medianBlur(processed, 3)
        
        # 4. Sharpen the image
        kernel_sharpen = np.array([[-1,-1,-1],
                                   [-1, 9,-1],
                                   [-1,-1,-1]])
        processed = cv2.filter2D(processed, -1, kernel_sharpen)
        
        # 5. Save cleaned image
        cleaned_path = image_path.replace('.png', '_cleaned.png').replace('.jpg', '_cleaned.jpg')
        cv2.imwrite(cleaned_path, processed)
        
        print(f"✅ Image cleaned and saved to: {cleaned_path}")
        return cleaned_path
        
    except ImportError:
        print("⚠️ OpenCV not installed. Install with: pip install opencv-python")
        return image_path
    except Exception as e:
        print(f"⚠️ Image cleaning failed: {e}")
        return image_path

def solve_captcha_direct(image_path, use_opencv_cleaning=True):
    """Direct CAPTCHA solving using pre-installed packages with OpenCV preprocessing"""
    print(f"\n🔍 Solving CAPTCHA with local OCR: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return None
    
    # Apply OpenCV cleaning first
    working_image = image_path
    if use_opencv_cleaning:
        print("🧹 Applying OpenCV noise removal...")
        working_image = clean_image_for_ocr(image_path)
    
    results = []
    
    # Method 1: EasyOCR with multiple configurations
    try:
        import easyocr
        
        print("🤖 Using EasyOCR on cleaned image...")
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        
        # Try multiple EasyOCR configurations
        configs = [
            {'width_ths': 0.7, 'height_ths': 0.7},
            {'width_ths': 0.5, 'height_ths': 0.5},
            {'width_ths': 0.9, 'height_ths': 0.9},
            {'paragraph': False},
            {'paragraph': True}
        ]
        
        for i, config in enumerate(configs):
            try:
                ocr_results = reader.readtext(working_image, detail=0, **config)
                if ocr_results:
                    text = ''.join(ocr_results).strip().replace(' ', '').replace('\n', '')
                    clean_text = ''.join(c for c in text if c.isalnum())
                    if len(clean_text) >= 3:
                        results.append(f"EasyOCR-{i+1}: {clean_text}")
                        print(f"✅ EasyOCR config {i+1}: {clean_text}")
            except Exception as e:
                print(f"⚠️ EasyOCR config {i+1} failed: {e}")
                
    except Exception as e:
        print(f"❌ EasyOCR failed: {e}")
    
    # Method 2: Enhanced Pytesseract with image preprocessing
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps
        import numpy as np
        
        print("🔤 Using Enhanced Pytesseract on cleaned image...")
        
        # Load and preprocess image (use cleaned version)
        img = Image.open(working_image)
        
        # Try different preprocessing approaches
        preprocessing_methods = [
            "original",
            "grayscale_contrast", 
            "binary_threshold",
            "noise_removal",
            "sharpening",
            "invert_colors"
        ]
        
        for method in preprocessing_methods:
            try:
                processed_img = img.copy()
                
                if method == "grayscale_contrast":
                    processed_img = processed_img.convert('L')
                    enhancer = ImageEnhance.Contrast(processed_img)
                    processed_img = enhancer.enhance(2.5)
                    
                elif method == "binary_threshold":
                    processed_img = processed_img.convert('L')
                    # Convert to numpy array for thresholding
                    img_array = np.array(processed_img)
                    threshold = 128
                    binary_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
                    processed_img = Image.fromarray(binary_array)
                    
                elif method == "noise_removal":
                    processed_img = processed_img.convert('L')
                    processed_img = processed_img.filter(ImageFilter.MedianFilter(3))
                    enhancer = ImageEnhance.Contrast(processed_img)
                    processed_img = enhancer.enhance(2.0)
                    
                elif method == "sharpening":
                    processed_img = processed_img.convert('L')
                    processed_img = processed_img.filter(ImageFilter.SHARPEN)
                    enhancer = ImageEnhance.Sharpness(processed_img)
                    processed_img = enhancer.enhance(2.0)
                    
                elif method == "invert_colors":
                    processed_img = processed_img.convert('L')
                    processed_img = ImageOps.invert(processed_img)
                
                # Try different PSM modes
                psm_modes = [6, 7, 8, 13]
                for psm in psm_modes:
                    config = f'--psm {psm} -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                    text = pytesseract.image_to_string(processed_img, config=config).strip()
                    clean_text = ''.join(c for c in text if c.isalnum())
                    
                    if len(clean_text) >= 3:
                        result_name = f"Tesseract-{method}-PSM{psm}: {clean_text}"
                        results.append(result_name)
                        print(f"✅ {result_name}")
                        
            except Exception as e:
                print(f"⚠️ Tesseract {method} failed: {e}")
                
    except Exception as e:
        print(f"❌ Pytesseract failed: {e}")
    
    # Analyze results and pick the best one
    if results:
        print(f"\n📊 All OCR Results:")
        for result in results:
            print(f"  {result}")
        
        # Extract just the text results
        text_results = [r.split(': ')[1] for r in results]
        
        # Apply manual corrections for common OCR errors
        corrected_results = []
        corrected_texts = []
        for text in text_results:
            corrected = apply_captcha_corrections(text)
            if corrected != text:
                corrected_results.append(f"Corrected: {corrected}")
                corrected_texts.append(corrected)
                print(f"🔧 Applied correction: {text} → {corrected}")
            else:
                corrected_texts.append(text)
        
        # Pick the best result (prefer corrected ones, then by length)
        all_candidates = corrected_texts  # Use corrected texts instead of originals
        best_candidates = [c for c in all_candidates if len(c) in [4, 5, 6]]
        
        if best_candidates:
            best_result = best_candidates[0]
            print(f"\n🏆 Best result: {best_result}")
            return best_result
        elif all_candidates:
            best_result = all_candidates[0]
            print(f"\n🔄 Using first result: {best_result}")
            return best_result
    
    print("❌ All OCR methods failed")
    return None

def apply_captcha_corrections(text):
    """Apply intelligent CAPTCHA OCR corrections using universal pattern analysis"""
    import re
    from itertools import product
    
    corrected = text
    original = text
    
    # Universal OCR character confusions - these can happen with ANY character
    char_confusions = {
        # Single character confusions
        'y': ['r', 'v', 'n', 'g'],        # y often confused with these
        'u': ['a', 'o', 'n', 'ii'],       # u often confused with these
        'z': ['s', 'a', 't', '2'],        # z often confused with these
        't': ['a', 'l', 'i', '+'],        # t often confused with these
        'l': ['i', 't', '1', 'j'],        # l often confused with these
        'i': ['l', 'j', '1', 't'],        # i often confused with these
        'o': ['a', '0', 'e', 'c'],        # o often confused with these
        'n': ['r', 'm', 'h', 'ii'],       # n often confused with these
        'r': ['n', 'y', 'v'],            # r often confused with these
        'a': ['o', 'e', 'u'],            # a often confused with these
        's': ['z', '5', 'g'],            # s often confused with these
        'g': ['q', 'y', '9'],            # g often confused with these
        'q': ['g', 'o', '9'],            # q often confused with these
        'w': ['v', 'vv', 'ii'],          # w often confused with these
        'v': ['y', 'r'],                 # v often confused with these
        'e': ['c', 'o'],                 # e often confused with these
        'c': ['e', 'o'],                 # c often confused with these
        'm': ['n', 'ii', 'rn'],          # m often confused with these
        'h': ['n', 'ii'],                # h often confused with these
        'j': ['i', 'l'],                 # j often confused with these
        'f': ['t', 'r'],                 # f often confused with these
        'p': ['q', 'g'],                 # p often confused with these
        'b': ['g', '6'],                 # b often confused with these
        'd': ['a', 'cl'],                # d often confused with these
        'k': ['h', 'ii'],                # k often confused with these
    }
    
    # Universal 2-character pattern confusions - these can occur anywhere
    two_char_patterns = {
        'rn': ['m', 'n'],               # rn often misread as m
        'cl': ['d', 'a'],               # cl often misread as d  
        'ml': ['mon', 'mi'],            # ml often misread as mon
        'ii': ['n', 'u', 'w'],          # ii often misread as n, u, w
        'vv': ['w'],                    # vv often misread as w
        'qu': ['q', 'g'],               # qu sometimes compressed
        'ij': ['j', 'y'],               # ij often misread as j
    }
    
    # Universal 3+ character pattern analysis
    # Look for common error patterns that can happen anywhere
    def generate_dynamic_patterns(text):
        patterns = []
        
        # Look for potential 2-char combinations that might be wrong
        for i in range(len(text) - 1):
            two_char = text[i:i+2]
            if two_char in two_char_patterns:
                for replacement in two_char_patterns[two_char]:
                    new_text = text[:i] + replacement + text[i+2:]
                    patterns.append((f"{two_char} -> {replacement}", new_text))
        
        # Look for characters that might need replacement
        for i, char in enumerate(text):
            if char.lower() in char_confusions:
                for replacement in char_confusions[char.lower()][:3]:  # Top 3 alternatives
                    new_text = text[:i] + replacement + text[i+1:]
                    patterns.append((f"{char} -> {replacement}", new_text))
        
        return patterns
    
    print(f"\nAnalyzing OCR result: '{original}'")
    
    # Generate all possible corrections dynamically
    correction_candidates = [original]
    pattern_explanations = []
    
    # Apply dynamic pattern generation
    patterns = generate_dynamic_patterns(original.lower())
    
    for explanation, candidate in patterns:
        if candidate != original.lower() and candidate not in correction_candidates:
            correction_candidates.append(candidate)
            pattern_explanations.append(f"{explanation} = {candidate}")
    
    # Show some pattern fixes being tried
    if pattern_explanations:
        print("Dynamic pattern fixes:")
        for explanation in pattern_explanations[:8]:  # Show first 8
            print(f"  {explanation}")
    
    # Score candidates by CAPTCHA likelihood (no hardcoded word knowledge)
    def score_candidate(candidate):
        score = 0
        
        # Length preference (CAPTCHAs are usually 4-8 chars)
        if 4 <= len(candidate) <= 8:
            score += 2
        elif len(candidate) < 4:
            score -= 3
        
        # Common letter combinations
        if 'qu' in candidate: score += 1.5
        if 'wr' in candidate: score += 1
        if 'th' in candidate: score += 1
        if 'ch' in candidate: score += 1
        if 'sh' in candidate: score += 1
        
        # Avoid too many repeated characters
        unique_chars = len(set(candidate))
        if unique_chars < len(candidate) * 0.5:
            score -= 1
        
        # Prefer alternating consonants/vowels
        vowels = 'aeiou'
        consonants = 'bcdfghjklmnpqrstvwxyz'
        vowel_count = sum(1 for c in candidate if c in vowels)
        consonant_count = sum(1 for c in candidate if c in consonants)
        if 0.2 <= vowel_count / len(candidate) <= 0.6:
            score += 1
            
        return score
    
    # Remove duplicates and score
    unique_candidates = list(set(correction_candidates))
    scored_candidates = [(score_candidate(c), c) for c in unique_candidates if c != original.lower()]
    scored_candidates.sort(reverse=True, key=lambda x: x[0])
    
    if scored_candidates:
        print(f"Top correction candidates:")
        for i, (score, candidate) in enumerate(scored_candidates[:5], 1):
            print(f"  {i}. {candidate} (score: {score:.1f})")
        
        # Return the highest scored candidate
        best_candidate = scored_candidates[0][1]
        if best_candidate != original.lower():
            print(f"Selected best correction: {original} -> {best_candidate}")
            return best_candidate
    
    print(f"No good corrections found, keeping original: {original}")
    return original

# ==============================================================================
# UNIFIED SOLVER with Intelligent Fallback
# ==============================================================================

def solve_captcha(image_path, methods=None):
    """
    Unified CAPTCHA solver that tries multiple methods with intelligent fallback
    
    Args:
        image_path: Path to CAPTCHA image
        methods: List of methods to try in order. Options:
                 - "vision_llm_gpt" (GPT-4o)
                 - "vision_llm_claude" (Claude 3.5 Sonnet)
                 - "capsolver"
                 - "2captcha"
                 - "local_ocr"
                 If None, tries all available methods in optimal order
    
    Returns:
        Solved CAPTCHA text or None
    """
    print(f"\n{'='*70}")
    print(f"🎯 CAPTCHA Solver - Multi-Method Approach")
    print(f"{'='*70}")
    print(f"Image: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return None
    
    # Default method order (best to worst)
    if methods is None:
        methods = [
            "vision_llm_gpt",      # Highest intelligence
            "vision_llm_claude",   # Alternative vision model
            "capsolver",           # Most reliable API
            "2captcha",            # Backup API
            "local_ocr"            # Fallback to local processing
        ]
    
    results = {}
    
    for method in methods:
        try:
            if method == "vision_llm_gpt":
                if os.getenv("OPENAI_API_KEY"):
                    result = solve_with_vision_llm(image_path, model="gpt-4o")
                    if result:
                        results[method] = result
                        print(f"\n✅ SUCCESS with {method}: {result}")
                        return result
                else:
                    print(f"⚠️ Skipping {method}: OPENAI_API_KEY not set")
            
            elif method == "vision_llm_claude":
                if os.getenv("ANTHROPIC_API_KEY"):
                    result = solve_with_vision_llm(image_path, model="claude-3-5-sonnet-20241022")
                    if result:
                        results[method] = result
                        print(f"\n✅ SUCCESS with {method}: {result}")
                        return result
                else:
                    print(f"⚠️ Skipping {method}: ANTHROPIC_API_KEY not set")
            
            elif method == "capsolver":
                if os.getenv("CAPSOLVER_API_KEY"):
                    result = solve_with_capsolver(image_path)
                    if result:
                        results[method] = result
                        print(f"\n✅ SUCCESS with {method}: {result}")
                        return result
                else:
                    print(f"⚠️ Skipping {method}: CAPSOLVER_API_KEY not set")
            
            elif method == "2captcha":
                if os.getenv("TWOCAPTCHA_API_KEY"):
                    result = solve_with_2captcha(image_path)
                    if result:
                        results[method] = result
                        print(f"\n✅ SUCCESS with {method}: {result}")
                        return result
                else:
                    print(f"⚠️ Skipping {method}: TWOCAPTCHA_API_KEY not set")
            
            elif method == "local_ocr":
                result = solve_captcha_direct(image_path, use_opencv_cleaning=True)
                if result:
                    results[method] = result
                    print(f"\n✅ SUCCESS with {method}: {result}")
                    return result
            
            else:
                print(f"⚠️ Unknown method: {method}")
        
        except Exception as e:
            print(f"❌ Method {method} failed with exception: {e}")
    
    print(f"\n{'='*70}")
    print(f"❌ All methods failed to solve CAPTCHA")
    if results:
        print(f"Partial results: {results}")
    print(f"{'='*70}")
    return None

if __name__ == "__main__":
    print("🔍 CAPTCHA Solver Test Suite")
    print("\nSupported methods:")
    print("  1. Vision LLM (GPT-4o) - Requires OPENAI_API_KEY")
    print("  2. Vision LLM (Claude 3.5) - Requires ANTHROPIC_API_KEY")
    print("  3. CapSolver API - Requires CAPSOLVER_API_KEY")
    print("  4. 2Captcha API - Requires TWOCAPTCHA_API_KEY")
    print("  5. Local OCR (OpenCV + Tesseract/EasyOCR) - No API key needed")
    print("\n" + "="*70)
    
    # Look for CAPTCHA image
    captcha_files = ['captcha_image.png', 'captcha.png', 'captcha.jpg']
    
    for captcha_file in captcha_files:
        if os.path.exists(captcha_file):
            # Use unified solver with all methods
            result = solve_captcha(captcha_file)
            if result:
                print(f"\n{'='*70}")
                print(f"🎉 FINAL RESULT: {result}")
                print(f"{'='*70}")
                break
            else:
                print(f"\n❌ Failed to solve: {captcha_file}")
    else:
        print("\n❌ No CAPTCHA images found")
        print("Looking for: captcha_image.png, captcha.png, or captcha.jpg")
        print("\nAvailable image files:")
        image_files = [f for f in os.listdir('.') if f.endswith(('.png', '.jpg', '.jpeg'))]
        if image_files:
            for f in image_files:
                print(f"  - {f}")
        else:
            print("  (none)")