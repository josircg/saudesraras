from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.db.models.functions import Lower
from .models import Disease, Symptom  
from organisations.models import Organisation  # Importante: puxando o model de organizações

def disease_list(request):
    disease_queryset = Disease.objects.all().prefetch_related('symptoms')
    
    query = request.GET.get('q', '')
    symptom_filter = request.GET.get('symptom', '')
    orderby_filter = request.GET.get('orderby', 'name') 

    if query:
        disease_queryset = disease_queryset.filter(
            Q(name__icontains=query) | 
            Q(ICD__icontains=query) | 
            Q(description__icontains=query)
        ).distinct()

    if symptom_filter:
        disease_queryset = disease_queryset.filter(symptoms__id=symptom_filter).distinct()

    if orderby_filter == '-name':
        disease_queryset = disease_queryset.order_by(Lower('name').desc())  
    else:
        disease_queryset = disease_queryset.order_by(Lower('name')) 

    paginator = Paginator(disease_queryset, 12)
    page = request.GET.get('page')

    try:
        diseases = paginator.page(page)
    except PageNotAnInteger:
        diseases = paginator.page(1)
    except EmptyPage:
        diseases = paginator.page(paginator.num_pages)

    all_symptoms = Symptom.objects.all().order_by(Lower('description'))

    context = {
        "diseases": diseases,
        "all_symptoms": all_symptoms,
        "filters": {
            "q": query,
            "symptom": symptom_filter,
            "orderby": orderby_filter,
        }
    }

    return render(request, "diseases.html", context)


def disease_detail(request, pk):
    disease = get_object_or_404(Disease, pk=pk)
    
    symptoms = disease.symptoms.all().order_by(Lower('description'))
    
    org_list = Organisation.objects.filter(diseases=disease, approved=True).order_by('name')
    
    paginator = Paginator(org_list, 4)
    page = request.GET.get('page')  # Pega o parâmetro ?page= da URL

    try:
        organisations = paginator.page(page)
    except PageNotAnInteger:
        organisations = paginator.page(1)
    except EmptyPage:
        organisations = paginator.page(paginator.num_pages)

    # 5. Monta o contexto para renderizar no disease.html
    context = {
        "disease": disease,
        "symptoms": symptoms,
        "organisations": organisations,
    }

    return render(request, "disease.html", context)