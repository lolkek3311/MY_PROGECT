import re

def parse_constitution(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Разбиваем по "СТАТЬЯ N."
    pattern = re.compile(r'(СТАТЬЯ\s+\d+\.)', re.IGNORECASE)
    parts = pattern.split(text)
    docs = []
    
    if parts[0].strip():
        docs.append({"article": 0, "text": parts[0].strip()})

    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        body = parts[i+1].strip()
        # Ищем номер
        num_match = re.search(r'\d+', header)
        num = int(num_match.group()) if num_match else 0
        
        docs.append({"article": num, "text": f"{header}\n{body}"})
        
    return docs

def chunk_text(docs, size=1000, overlap=200):
    chunks = []
    for d in docs:
        words = d['text'].split()
        if len(words) <= size:
            chunks.append(d)
        else:
            start = 0
            while start < len(words):
                end = start + size
                sub_text = " ".join(words[start:end])
                chunks.append({"article": d['article'], "text": sub_text})
                start += (size - overlap)
    return chunks