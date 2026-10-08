from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import ThesisPaperForm
from .models import ThesisPaper


def paper_list_view(request):
    query = request.GET.get('q', '').strip()
    selected_domain = request.GET.get('domain', '').strip()
    selected_year = request.GET.get('year', '').strip()

    papers = ThesisPaper.objects.all().order_by('-publication_year', '-uploaded_at')
    if query:
        papers = papers.filter(
            Q(title__icontains=query) | Q(authors__icontains=query)
        )
    if selected_domain:
        papers = papers.filter(domain=selected_domain)
    if selected_year.isdigit():
        papers = papers.filter(publication_year=int(selected_year))

    domains = ThesisPaper.objects.values_list('domain', flat=True).distinct().order_by('domain')
    years = ThesisPaper.objects.values_list('publication_year', flat=True).distinct().order_by('-publication_year')

    return render(request, 'research_library/paper_list.html', {
        'papers': papers,
        'query': query,
        'selected_domain': selected_domain,
        'selected_year': selected_year,
        'domains': domains,
        'years': years,
        'upload_form': ThesisPaperForm(),
    })


def paper_detail_view(request, paper_id):
    paper = get_object_or_404(ThesisPaper, id=paper_id)
    return render(request, 'research_library/paper_detail.html', {'paper': paper})


@login_required
def upload_paper_view(request):
    form = ThesisPaperForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Research paper uploaded successfully.')
        return redirect('paper_list')

    return render(request, 'research_library/upload_paper.html', {'form': form})