from functools import lru_cache

from proposals.models import ResearchTopic
from research_library.models import ThesisPaper

# সেফলি এআই লাইব্রেরিগুলো ইমপোর্ট করার ব্যবস্থা, যাতে রেন্ডার সার্ভারে ক্র্যাশ না করে
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    AI_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    SentenceTransformer = None
    cosine_similarity = None
    AI_AVAILABLE = False


MODEL_NAME = 'all-MiniLM-L6-v2'


@lru_cache(maxsize=1)
def get_embedding_model():
    if not AI_AVAILABLE or SentenceTransformer is None:
        return None
    return SentenceTransformer(MODEL_NAME)


def _document_text(title, description=''):
    return f'{title}\n{description}'.strip()


def _score(value):
    return round(max(0.0, min(1.0, float(value))) * 100, 1)


def _novelty_status(similarity):
    if similarity >= 75:
        return {
            'label': 'High Similarity',
            'description': 'Potential duplicate detected. Refine the scope or research question.',
            'tone': 'danger',
        }
    if similarity >= 45:
        return {
            'label': 'Moderate Overlap',
            'description': 'Related work exists. A sharper gap or new method may improve novelty.',
            'tone': 'warning',
        }
    return {
        'label': 'High Novelty',
        'description': 'The idea has limited overlap with the indexed research records.',
        'tone': 'success',
    }


def analyze_query(query):
    query = query.strip()
    if not query:
        return {
            'query': '',
            'similarity_percentage': 0,
            'novelty_percentage': 100,
            'status': _novelty_status(0),
            'matches': [],
            'recommendations': [],
            'chart_data': {'novelty': 100, 'similarity': 0, 'labels': [], 'scores': []},
        }

    papers = list(ThesisPaper.objects.all().only(
        'id', 'title', 'abstract', 'authors', 'domain', 'publication_year'
    ))
    topics = list(ResearchTopic.objects.all().only(
        'id', 'title', 'description', 'domain', 'status'
    ))

    records = []
    for paper in papers:
        records.append({
            'kind': 'paper',
            'id': paper.id,
            'title': paper.title,
            'description': paper.abstract,
            'domain': paper.domain,
            'meta': f'{paper.authors} | {paper.publication_year}',
        })
    for topic in topics:
        records.append({
            'kind': 'topic',
            'id': topic.id,
            'title': topic.title,
            'description': topic.description,
            'domain': topic.domain,
            'meta': f'{topic.domain} | {topic.status}',
        })

    # সার্ভারে এআই উপলব্ধ থাকলে এআই দিয়ে কাজ করবে, না থাকলে ফলব্যাক মোডে চলবে
    if AI_AVAILABLE and records:
        model = get_embedding_model()
        if model is not None and cosine_similarity is not None:
            try:
                query_vector = model.encode([query], convert_to_numpy=True)
                record_vectors = model.encode(
                    [_document_text(item['title'], item['description']) for item in records],
                    convert_to_numpy=True,
                    show_progress_bar=False,
                )
                scores = cosine_similarity(query_vector, record_vectors)[0]
                for record, score in zip(records, scores):
                    record['similarity'] = _score(score)
            except Exception:
                for record in records:
                    record['similarity'] = 0.0
        else:
            for record in records:
                record['similarity'] = 0.0
    else:
        for record in records:
            record['similarity'] = 0.0

    matches = sorted(records, key=lambda item: item.get('similarity', 0), reverse=True)[:5]
    highest_similarity = max((item.get('similarity', 0) for item in records), default=0)
    status = _novelty_status(highest_similarity)

    domain_counts = {}
    for record in records:
        domain = record.get('domain') or 'General research'
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    recommendations = []
    for topic in sorted(topics, key=lambda item: (
        domain_counts.get(item.domain or 'General research', 0),
        next((record['similarity'] for record in records if record['kind'] == 'topic' and record['id'] == item.id), 0),
    ))[:3]:
        recommendations.append({
            'title': topic.title,
            'domain': topic.domain,
            'description': topic.description,
            'reason': 'Low-density direction in the indexed topic set.',
        })

    return {
        'query': query,
        'similarity_percentage': highest_similarity,
        'novelty_percentage': round(100 - highest_similarity, 1),
        'status': status,
        'matches': matches,
        'recommendations': recommendations,
        'chart_data': {
            'novelty': round(100 - highest_similarity, 1),
            'similarity': highest_similarity,
            'labels': [item['title'] for item in matches],
            'scores': [item['similarity'] for item in matches],
        },
    }