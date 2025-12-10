import requests
import psycopg2
from chank import parse_constitution, chunk_text
from embending import get_embedding

# --- НАСТРОЙКИ БД ---
DB_CONFIG = {
    "dbname": "rag_db",
    "user": "postgres",
    "password": "cntgf",  # ВАШ ПАРОЛЬ
    "host": "localhost",
    "port": "5432"
}

# --- НАСТРОЙКИ LLM ---
# Ваш ключ OpenRouter
OPENROUTER_API_KEY = "YOUR_API_KEY_FOR_OPENROUTER"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class RAGSystem:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.init_db()

    # ... (начало файла такое же)

    def init_db(self):
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # --- ВАЖНО: Удаляем старую таблицу, если размер не 1536 ---
            cur.execute("""
                SELECT atttypmod FROM pg_attribute
                WHERE attrelid = 'chunks'::regclass AND attname = 'embedding';
            """)
            result = cur.fetchone()
            
            # Если размерность не 1536, удаляем
            if result and result[0] != 1536:
                print("⚠️ Меняем размерность базы под OpenAI (1536)...")
                cur.execute("DROP TABLE chunks CASCADE;")
                cur.execute("DROP TABLE documents CASCADE;")
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id bigserial PRIMARY KEY,
                    filename text,
                    created_at timestamp DEFAULT now()
                );
            """)
            
            # ИЗМЕНЕНО НА 1536
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id bigserial PRIMARY KEY,
                    doc_id bigint REFERENCES documents(id),
                    article int,
                    text text,
                    embedding vector(1536)
                );
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS chunk_idx ON chunks 
                USING hnsw (embedding vector_l2_ops);
            """)
        self.conn.commit()

# ... (остальной код такой же)

    def load_data(self, filepath):
        """Парсинг, векторизация и сохранение."""
        docs = parse_constitution(filepath)
        chunks = chunk_text(docs)
        
        with self.conn.cursor() as cur:
            # Очистка перед новой загрузкой
            cur.execute("TRUNCATE chunks, documents RESTART IDENTITY CASCADE;")
            
            cur.execute("INSERT INTO documents (filename) VALUES (%s) RETURNING id", (filepath,))
            doc_id = cur.fetchone()[0]
            
            for ch in chunks:
                vec = get_embedding(ch['text'])
                if vec:
                    cur.execute("""
                        INSERT INTO chunks (doc_id, article, text, embedding)
                        VALUES (%s, %s, %s, %s)
                    """, (doc_id, ch['article'], ch['text'], vec))
        
        self.conn.commit()
        return len(chunks)

    def ask(self, question):
        """Поиск + LLM."""
        # 1. Локальная векторизация вопроса
        q_vec = get_embedding(question)
        if not q_vec:
            return "Ошибка генерации вектора (проверьте embending.py).", []

        # 2. Поиск в БД
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT article, text, embedding <-> %s::vector as dist
                FROM chunks
                ORDER BY dist ASC
                LIMIT 5
            """, (q_vec,))
            rows = cur.fetchall()

        if not rows:
            return "База данных пуста. Сначала загрузите файл Конституции.", []

        # 3. Сборка контекста
        context_parts = []
        sources = set()
        for r in rows:
            art_num = r[0]
            txt = r[1]
            context_parts.append(f"--- Статья {art_num} ---\n{txt}")
            sources.add(f"Статья {art_num}")
            
        full_context = "\n\n".join(context_parts)

        # 4. Запрос к OpenRouter
        system_prompt = (
            "Ты — официальный помощник по Конституции Республики Беларусь. "
            "Отвечай ТОЛЬКО используя предоставленный контекст. "
            "Всегда указывай номера статей, на которые ссылаешься. "
            "Если ответа нет в контексте, напиши: 'В Конституции нет прямой информации об этом'."
        )

        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"КОНТЕКСТ:\n{full_context}\n\nВОПРОС:\n{question}"}
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "ConstitutionApp"
        }

        try:
            resp = requests.post(OPENROUTER_URL, headers=headers, json=payload)
            if resp.status_code != 200:
                return f"Ошибка API ({resp.status_code}): {resp.text}", []
            
            ans = resp.json()['choices'][0]['message']['content']
            return ans, list(sources)
            
        except Exception as e:
            return f"Сбой соединения с нейросетью: {e}", []