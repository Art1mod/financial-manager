from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # Saves the new user into the SQLite DB
            login(request, user) # Automatically logs them in right after signing up
            return redirect('dashboard') # We will create the dashboard view later!
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
