from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from proposals.models import ThesisProposal
from profiles.models import SupervisorProfile
from .models import PaperEmbedding
from .services import analyze_query


@login_required
def search_novelty_view(request):
    query = request.GET.get('q', '').strip() or request.POST.get('query', '').strip()
    analysis = analyze_query(query)
    return render(request, 'core_ai/match_result.html', analysis)

# ১. প্রপোজাল এবং সুপারভাইজার ম্যাচিং স্কোর চেক করার ভিউ
@login_required
def match_proposal_view(request, proposal_id):
    proposal = get_object_or_404(ThesisProposal, id=proposal_id)
    supervisors = SupervisorProfile.objects.all()

    # ডেমো AI ম্যাচিং লজিক (ভবিষ্যতে এখানে আসল NLP/TF-IDF/BERT মডেল বসবে)
    matches = []
    for sup in supervisors:
        # প্রপোজালের ডোমেইন এবং সুপারভাইজারের ডোমেইন মিলে গেলে স্কোর বেশি হবে
        score = 85.0 if proposal.domain.lower() in sup.research_domains.lower() else 45.0
        matches.append({
            'supervisor': sup.user.username,
            'department': sup.department,
            'match_score': score
        })

    # স্কোর অনুযায়ী সাজানো (Descending order)
    matches = sorted(matches, key=lambda x: x['match_score'], reverse=True)

    return render(request, 'core_ai/match_result.html', {
        'proposal': proposal,
        'matches': matches
    })


# ২. API End Point (AJAX বা ফ্রন্টএন্ড থেকে AI স্কোর কল করার জন্য)
@login_required
def match_score_api(request, proposal_id):
    proposal = get_object_or_404(ThesisProposal, id=proposal_id)
    
    # ডেমো রেসপন্স
    data = {
        'proposal_id': proposal.id,
        'title': proposal.proposed_title,
        'status': 'success',
        'recommended_supervisor_count': 3
    }
    return JsonResponse(data)