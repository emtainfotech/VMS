from django.shortcuts import render,redirect
from django.shortcuts import render, get_object_or_404
from .models import *

# Create your views here.

# View to display resumes
def resume(request):
    resumes = ResumeData.objects.all()
    unique_sectors = resumes.values_list('sector', flat=True).distinct()
    coverletters = CoverData.objects.all()
    
    context = {
        'resumes': resumes,
        'coverletters' : coverletters,
        'unique_sectors': unique_sectors
    } 
    return render(request, 'resume/resume.html', context)

# View to upload a resume
def upload_resume(request):
    if request.method == 'POST':  # Correct case
        name = request.POST.get('name')
        description = request.POST.get('description')  # Typo corrected: `discription` to `description`
        category = request.POST.get('category')
        sector = request.POST.get('sector')
        resume_image = request.FILES.get('resume_image')  # Use `FILES` to get uploaded files
        resume_file = request.FILES.get('resume_file')
        edit_link = request.POST.get('edit_link')

        # Create a new instance of ResumeData
        resume_data = ResumeData(
            name=name,
            description=description,
            category=category,
            sector=sector,
            resume_image=resume_image,
            resume_file=resume_file,
            edit_link=edit_link,
        )
        # Save the instance to the database
        resume_data.save()
        return redirect(upload_resume)  # Redirect to the listing page

    return render(request, 'resume/upload-resume.html')

# View to upload a resume
def upload_cover(request):
    if request.method == 'POST':  # Correct case
        name = request.POST.get('name')
        description = request.POST.get('description')  # Typo corrected: `discription` to `description`
        category = request.POST.get('category')
        sector = request.POST.get('sector')
        cover_image = request.FILES.get('cover_image')  # Use `FILES` to get uploaded files
        cover_file = request.FILES.get('cover_file')
        edit_link = request.POST.get('edit_link')

        # Create a new instance of ResumeData
        cover_data = CoverData(
            name=name,
            description=description,
            category=category,
            sector=sector,
            cover_image=cover_image,
            cover_file=cover_file,
            edit_link=edit_link,
        )
        # Save the instance to the database
        cover_data.save()
        return redirect('resume')  # Redirect to the listing page

    return render(request, 'resume/upload-cover.html')

def resume_list(request) :
    resumes = ResumeData.objects.all()
    unique_sectors = resumes.values_list('sector', flat=True).distinct()
    context = {
        'resumes': resumes,
        'unique_sectors': unique_sectors
    }
    return render(request,'resume/resume-list.html',context)

def cover_list(request) :
    coverletters = CoverData.objects.all()
    unique_sectors = coverletters.values_list('sector', flat=True).distinct()
    context = {
        'coverletters': coverletters,
        'unique_sectors': unique_sectors
    }
    return render(request,'resume/cover-list.html',context)


def product_details(request, id):
    resume = get_object_or_404(ResumeData, id=id)
    resumes = ResumeData.objects.all()
    context = {
        'resume': resume,
        'resumes' : resumes
    }
    return render(request, 'resume/product-resume.html', context)

def cover_details(request, id):
    coverletter = get_object_or_404(CoverData, id=id)
    coverletters = CoverData.objects.all()
    context = {
        'coverletter': coverletter,
        'coverletters' : coverletters
    }
    return render(request, 'resume/product-cover.html', context)

