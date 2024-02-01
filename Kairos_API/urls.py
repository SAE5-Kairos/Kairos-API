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
from API_views import views_generator, views_salles, views_utilisateurs, views_indisponibilite, views_ressource, \
    views_cours, views_groupe, views_EDT, views_banque, views_type_cours, views_couleur
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
    path('api/utilisateurs/', views_utilisateurs.get_all),
    path('api/utilisateurs/professeur/', views_utilisateurs.get_all_professors),
    path('api/utilisateurs/etudiant/', views_utilisateurs.get_all_students),
    path('api/utilisateur/<int:code>/', views_utilisateurs.by_id),
    path('api/utilisateur/', views_utilisateurs.add),

    # Indisponibilite
    path('api/indisponibilites/', views_indisponibilite.get_all),
    path('api/indisponibilite/<int:code>/', views_indisponibilite.by_id),
    path('api/indisponibilite/', views_indisponibilite.add),

    # Ressource
    path('api/ressources/', views_ressource.get_all),
    path('api/ressource/<int:code>/', views_ressource.by_id),
    path('api/ressource/', views_ressource.add),

    # Cours
    path('api/cours/', views_cours.get_all),
    path('api/cour/<int:code>/', views_cours.by_id),
    path('api/cour/', views_cours.add),

    # Groupe
    path('api/groupes/', views_groupe.get_all),
    path('api/groupe/<int:code>/', views_groupe.by_id),
    path('api/groupe/', views_groupe.add),
    
    # EDT
    path('api/emploidutemps/', views_EDT.get_all),
    path('api/emploidutemp/<int:code>/', views_EDT.by_id),
    path('api/emploidutemp/', views_EDT.add),

    # Banque
    path('api/banques/', views_banque.GetAll),
    path('api/banque/<int:code>/', views_banque.by_id),
    path('api/banque/', views_banque.add),

    # TypeCours
    path('api/typecours/', views_type_cours.get_all),
    path('api/typecour/<int:code>/', views_type_cours.by_id),
    path('api/typecour/', views_type_cours.add),

    # Couleurs
    path('api/couleurs/', views_couleur.get_all),
    path('api/couleur/<int:code>/', views_couleur.by_id),
    path('api/couleur/', views_couleur.add),

]
