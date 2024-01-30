"""
URL configuration for Kairos_API project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from API_views import views_generator, views_salles, views_professeurs, views_indisponibilite
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', views.home),
    path('api/generate_edt/', views_generator.generate_edt),
    # Salles
    path('api/salles/', views_salles.get_all),
    path('api/salle/<int:code>/', views_salles.by_id),
    path('api/salle/', views_salles.add),
    # Utilisateurs
    path('api/utilisateurs/', views_professeurs.get_all),
    path('api/utilisateur/<int:code>/', views_professeurs.by_id),
    path('api/utilisateur/', views_professeurs.add),
    # Indisponibilite
    path('api/indisponibilites/', views_indisponibilite.get_all),
    path('api/indisponibilite/<int:code>/', views_indisponibilite.by_id),
    path('api/indisponibilite/', views_indisponibilite.add),

]
