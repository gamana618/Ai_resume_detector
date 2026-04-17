from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import re, math
from collections import Counter
from PyPDF2 import PdfReader

app = Flask(__name__)
CORS(app)

AI_BUZZWORDS = [
    "proven track record","results-driven","dynamic professional",
    "leveraged","spearheaded","orchestrated","synergized","utilized",
    "passionate about","highly motivated","team player","go-getter",
    "strong work ethic","detail-oriented","self-starter","innovative",
    "cutting-edge","best practices","actionable insights","cross-functional",
    "stakeholder","deliverables","scalable","robust","seamlessly",
    "collaborated with","contributed to","responsible for","managed",
    "developed and maintained","ensured","facilitated","streamlined",
    "optimized","implemented","executed","achieved","demonstrated"
]

HUMAN_MARKERS = [
    "i ","i've","i'd","i'll","my ","me ","we ","our ",
    "honestly","basically","kind of","a bit","you know",
    "really","quite","pretty much","got to","ended up",
    "decided to","tried to","learned that","realized"
]

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\'\"]', ' ', text)
    return text.strip()

def split_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 20]

def split_chunks(text, chunk_size=100):
    words = text.split()
    return [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def compute_perplexity_proxy(text):
    words = text.lower().split()
    if len(words) < 5:
        return 0.5
    freq = Counter(words)
    total = len(words)
    entropy = -sum((c/total)*math.log2(c/total) for c in freq.values())
    max_entropy = math.log2(len(freq)) if len(freq)>1 else 1
    return 1 - entropy/max_entropy

def compute_burstiness(sentences):
    if len(sentences)<2:
        return 0.5
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths)/len(lengths)
    std = math.sqrt(sum((l-mean)**2 for l in lengths)/len(lengths))
    return max(0,min(1,1-(std/mean)/0.8))

def compute_buzzword_density(text):
    t=text.lower()
    return min(1,sum(1 for bw in AI_BUZZWORDS if bw in t)/6)

def compute_human_markers(text):
    t=text.lower()
    return 1-min(1,sum(1 for hm in HUMAN_MARKERS if hm in t)/5)

def compute_avg_sentence_length(sentences):
    if not sentences:
        return 0.5
    avg=sum(len(s.split()) for s in sentences)/len(sentences)
    if 14<=avg<=26:
        return 0.7
    elif avg<8 or avg>35:
        return 0.25
    return 0.5

def compute_punctuation_variety(text):
    total=len(re.findall(r'[.,!?;:\-()]',text))
    varied=len(re.findall(r'[!?;:\-()]',text))
    return 0.5 if total==0 else 1-min(1,(varied/total)/0.3)

def compute_repetition(text):
    words=text.lower().split()
    if len(words)<20:
        return 0.5
    trigrams=[' '.join(words[i:i+3]) for i in range(len(words)-2)]
    freq=Counter(trigrams)
    return min(1,sum(1 for c in freq.values() if c>1)/5)

def compute_formality_score(text):
    informal=len(re.findall(r"\b(gonna|wanna|gotta|cool|stuff)\b",text.lower()))
    contractions=len(re.findall(r"\b\w+'[a-z]{1,2}\b",text.lower()))
    return max(0,1-(informal+contractions*0.5)/5)

def score_chunk(chunk):
    sentences=split_sentences(chunk) or [chunk]
    feats={
        'perplexity':compute_perplexity_proxy(chunk),
        'burstiness':compute_burstiness(sentences),
        'buzzwords':compute_buzzword_density(chunk),
        'human_markers':compute_human_markers(chunk),
        'sent_length':compute_avg_sentence_length(sentences),
        'punctuation':compute_punctuation_variety(chunk),
        'repetition':compute_repetition(chunk),
        'formality':compute_formality_score(chunk),
    }
    weights={'perplexity':0.1,'burstiness':0.15,'buzzwords':0.2,
             'human_markers':0.15,'sent_length':0.1,'punctuation':0.1,
             'repetition':0.1,'formality':0.1}
    ai_prob=sum(feats[k]*weights[k] for k in feats)
    return min(0.98,max(0.02,ai_prob)),feats

def analyze_resume(text):
    text=clean_text(text)
    chunks=split_chunks(text)
    results=[]
    weights=[len(c.split()) for c in chunks]

    for i,chunk in enumerate(chunks):
        prob,feats=score_chunk(chunk)
        results.append({
            'chunk_id':i+1,
            'text_preview':chunk[:120],
            'ai_probability':prob,
            'human_probability':1-prob,
            'label':'AI-generated' if prob>=0.5 else 'Human-written',
            'confidence':abs(prob-0.5)*200,
            'features':feats
        })

    avg_ai=sum(results[i]['ai_probability']*weights[i] for i in range(len(chunks)))/sum(weights)
    ai_pct=round(avg_ai*100,1)
    human_pct=round(100-ai_pct,1)

    return {
        'ai_percentage':ai_pct,
        'human_percentage':human_pct,
        'verdict':'Mostly AI-generated' if ai_pct>60 else 'Mostly human-written',
        'severity':'high' if ai_pct>60 else 'low',
        'overall_confidence':round(abs(avg_ai-0.5)*200,1),
        'total_chunks':len(chunks),
        'word_count':len(text.split()),
        'chunk_analysis':results
    }

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data=request.get_json()
    text=data.get('text','')
    if len(text)<50:
        return jsonify({'error':'Text too short'})
    return jsonify(analyze_resume(text))

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'})
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        if len(text.strip()) < 50:
            return jsonify({'error': 'PDF text too short or unreadable'})
        return jsonify(analyze_resume(text))
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)