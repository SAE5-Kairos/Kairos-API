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
    views_cours, views_groupe, views_EDT, views_banque, views_type_cours, views_couleur, views_authentification, \
    views_enseigne
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', views.home),

    # Authentification
    path('api/login/', views_authentification.Login),
    path('api/register/', views_authentification.Register),
    path('api/reset_password/', views_authentification.ResetPassword),

    # Génerateur
    path('api/generate_edt/', views_generator.generate_edt),
    path('api/get_prof_dispo/<int:semaine>/<int:annee>/', views_generator.get_prof_dispo_all),
    path('api/get_prof_dispo/<int:id_prof>/<int:semaine>/<int:annee>/', views_generator.get_prof_dispo),

    # Enseigne
    path('api/add-enseignes/', views_enseigne.add_enseigne),

    # Salles
    path('api/salles/', views_salles.get_all),
    path('api/salle/<int:code>/', views_salles.by_id),
    path('api/salle/', views_salles.add),

    # Utilisateurs
    path('api/utilisateurs/', views_utilisateurs.get_all),
    path('api/utilisateurs/professeur/', views_utilisateurs.get_all_professors),
    path('api/utilisateurs/professeur/<int:code>/ressource/', views_utilisateurs.get_ressourcesByUser),
    path('api/utilisateurs/professeurs/ressources/', views_utilisateurs.get_ressourcesAllUsers),
    path('api/utilisateurs/etudiant/', views_utilisateurs.get_all_students),
    path('api/utilisateur/<int:code>/', views_utilisateurs.by_id),
    path('api/utilisateur/', views_utilisateurs.add),

    # Indisponibilite
    path('api/indisponibilites/', views_indisponibilite.get_all),
    path('api/indisponibilite/<int:code>/', views_indisponibilite.by_id),
    path('api/indisponibilite/', views_indisponibilite.add),
    path('api/indisponibilite/professeur/<int:code>', views_indisponibilite.get_indiponibility_by_user_id),

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
    path('api/emploidutemps/<int:code>/', views_EDT.by_id),
    path('api/emploidutemps/<int:semaine>/<int:annee>/', views_EDT.get_all_by_semaine),
    path('api/emploidutemps/<int:semaine>/<int:annee>/<int:idGroupe>/', views_EDT.by_groupe),
    path('api/emploidutemps/', views_EDT.add),

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
