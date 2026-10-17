import string
from collections import OrderedDict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.db.models.functions import Lower
from .models import Disease, Symptom  
from organisations.models import Organisation

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

    # Criação de uma lista real de inteiros para evitar validação incorreta de string no HTML
    symptom_ids_list = []
    if symptom_filter:
        if ',' in symptom_filter:
            symptom_ids = [int(x) for x in symptom_filter.split(',') if x.isdigit()]
            symptom_ids_list = symptom_ids
            for s_id in symptom_ids:
                disease_queryset = disease_queryset.filter(symptoms__id=s_id)
        else:
            if symptom_filter.isdigit():
                s_id = int(symptom_filter)
                symptom_ids_list = [s_id]
                disease_queryset = disease_queryset.filter(symptoms__id=s_id)
            
        disease_queryset = disease_queryset.distinct()

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
            "symptom_list": symptom_ids_list,  # Enviado como lista de números inteiros [14]
            "orderby": orderby_filter,
        }
    }

    return render(request, "diseases.html", context)
    
def disease_detail(request, pk):
    disease = get_object_or_404(Disease, pk=pk)
    
    symptoms = disease.symptoms.all().order_by(Lower('description'))
    
    org_list = Organisation.objects.filter(diseases=disease, approved=True).order_by('name')
    
    paginator = Paginator(org_list, 4)
    page = request.GET.get('page') 

    try:
        organisations = paginator.page(page)
    except PageNotAnInteger:
        organisations = paginator.page(1)
    except EmptyPage:
        organisations = paginator.page(paginator.num_pages)

    context = {
        "disease": disease,
        "symptoms": symptoms,
        "organisations": organisations,
    }

    return render(request, "disease.html", context)
    
def symptom_search(request):
    search_query = request.GET.get('q_symptom', '').strip()
    letter_filter = request.GET.get('letter', '').upper()
    selected_ids_str = request.GET.get('symptom', '') or request.GET.get('selected_symptoms', '')
    
    selected_ids = [int(x) for x in selected_ids_str.split(',') if x.isdigit()]
    
    symptom_queryset = Symptom.objects.all().order_by(Lower('description'))
    selected_symptoms = Symptom.objects.filter(id__in=selected_ids).order_by(Lower('description'))
    
    if search_query:
        symptom_queryset = symptom_queryset.filter(description__icontains=search_query)
    ITEMS_PER_PAGE = 15
    alphabet_map = OrderedDict()
    
    all_filtered_symptoms = list(symptom_queryset)
    for index, sym in enumerate(all_filtered_symptoms):
        first_letter = sym.description[0].upper() if sym.description else ''
        if first_letter and first_letter not in alphabet_map:
            page_number = (index // ITEMS_PER_PAGE) + 1
            alphabet_map[first_letter] = page_number


    if letter_filter and letter_filter in string.ascii_uppercase:
        symptom_queryset = symptom_queryset.filter(description__istartswith=letter_filter)
        
    paginator = Paginator(symptom_queryset, ITEMS_PER_PAGE) 
    page = request.GET.get('page')
    try:
        symptoms_page = paginator.page(page)
    except PageNotAnInteger:
        symptoms_page = paginator.page(1)
    except EmptyPage:
        symptoms_page = paginator.page(paginator.num_pages)

    alphabet = list(string.ascii_uppercase)

    context = {
        "symptoms_page": symptoms_page,
        "selected_symptoms": selected_symptoms,
        "alphabet_map": alphabet_map,  
        "alphabet": alphabet,          
        "filters": {
            "q_symptom": search_query,
            "letter": letter_filter,
            "selected_symptoms": selected_ids_str,
        }
    }
    return render(request, "symptoms.html", context)