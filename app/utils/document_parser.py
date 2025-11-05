"""
Document parser for extracting measure data from PDF and PowerPoint files
"""
import re
from datetime import datetime
from typing import Dict, List, Optional
from PyPDF2 import PdfReader
from pptx import Presentation


def parse_measure_document(file_path: str, file_type: str) -> Dict:
    """
    Parse a PDF or PowerPoint file and extract measure information
    
    Args:
        file_path: Path to the uploaded file
        file_type: 'pdf' or 'pptx'
    
    Returns:
        Dictionary with extracted measure data
    """
    if file_type == 'pdf':
        return parse_pdf(file_path)
    elif file_type in ['pptx', 'ppt']:
        return parse_powerpoint(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def parse_pdf(file_path: str) -> Dict:
    """Extract measure data from PDF"""
    reader = PdfReader(file_path)
    text = ""
    
    # Extract text from all pages
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    return extract_measure_data(text)


def parse_powerpoint(file_path: str) -> Dict:
    """Extract measure data from PowerPoint"""
    prs = Presentation(file_path)
    text = ""
    
    # Extract text from all slides
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
    
    return extract_measure_data(text)


def extract_measure_data(text: str) -> Dict:
    """
    Extract structured measure data from text using pattern matching
    
    Expected patterns based on the image:
    - Measure name/title at the top
    - Focus area: Process/Technology/etc
    - Description: [text]
    - Responsible: [name]
    - Participants: [names]
    - Time/Date: [date]
    - Target: [text]
    - Steps: Step 1, Step 2, etc.
    """
    data = {
        'name': '',
        'measure_detail': '',
        'target': '',
        'departments': '',
        'responsible': '',
        'participants': '',
        'start_date': None,
        'end_date': None,
        'steps': []
    }
    
    # Extract measure name (usually first line or after "Measure")
    measure_match = re.search(r'Measure\s+\d+\s*[:\-]?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if measure_match:
        data['name'] = measure_match.group(1).strip()
    else:
        # Try to get first non-empty line
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            data['name'] = lines[0]
    
    # Extract focus area / departments
    focus_match = re.search(r'Focus\s+area\s*:?\s*(.+?)(?:\n|Description)', text, re.IGNORECASE)
    if focus_match:
        data['departments'] = focus_match.group(1).strip()
    
    # Extract description
    desc_match = re.search(r'Description\s*:?\s*(.+?)(?:\n(?:Responsible|Participants|Time|Target|Step)|$)', text, re.IGNORECASE | re.DOTALL)
    if desc_match:
        data['measure_detail'] = desc_match.group(1).strip()
    
    # Extract responsible person
    resp_match = re.search(r'Responsible\s*:?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if resp_match:
        data['responsible'] = resp_match.group(1).strip()
    
    # Extract participants
    part_match = re.search(r'Participants\s*:?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if part_match:
        data['participants'] = part_match.group(1).strip()
    
    # Extract target
    target_match = re.search(r'Target\s*:?\s*(.+?)(?:\n|Step)', text, re.IGNORECASE | re.DOTALL)
    if target_match:
        data['target'] = target_match.group(1).strip()
    
    # Extract date/time
    time_match = re.search(r'Time\s*:?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if time_match:
        date_str = time_match.group(1).strip()
        # Try to parse date
        parsed_date = parse_date(date_str)
        if parsed_date:
            data['end_date'] = parsed_date
    
    # Extract steps
    steps = extract_steps(text)
    data['steps'] = steps
    
    return data


def extract_steps(text: str) -> List[str]:
    """Extract step titles from text"""
    steps = []
    
    # Pattern: Step 1, Step 2, etc.
    step_pattern = r'Step\s+\d+\s*:?\s*(.+?)(?=\nStep\s+\d+|\n\n|$)'
    matches = re.finditer(step_pattern, text, re.IGNORECASE | re.DOTALL)
    
    for match in matches:
        step_text = match.group(1).strip()
        # Clean up step text (remove extra whitespace, newlines)
        step_text = ' '.join(step_text.split())
        if step_text:
            steps.append(step_text)
    
    return steps


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Try to parse a date string in various formats
    
    Examples:
    - October 30, 2025
    - 2025-10-30
    - 30/10/2025
    """
    date_formats = [
        '%B %d, %Y',      # October 30, 2025
        '%b %d, %Y',      # Oct 30, 2025
        '%Y-%m-%d',       # 2025-10-30
        '%d/%m/%Y',       # 30/10/2025
        '%m/%d/%Y',       # 10/30/2025
        '%d-%m-%Y',       # 30-10-2025
        '%Y/%m/%d',       # 2025/10/30
    ]
    
    # Extract just the date part if there's extra text
    date_match = re.search(r'([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})', date_str)
    if date_match:
        date_str = date_match.group(1)
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    
    return None
