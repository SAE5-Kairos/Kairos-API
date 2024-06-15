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
from API_views import view_EDT, view_authentification, view_banque, view_couleur, view_cours, view_enseigne, view_generator, view_groupe, view_indisponibilite_prof, view_ressource, view_salles, view_type_cours, view_utilisateurs, view_indisponibilite_salle
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', views.home),

    # Authentification
    path('api/login/', view_authentification.Login),
    path('api/register/', view_authentification.Register),
    path('api/reset_password/', view_authentification.ResetPassword),

    # Génerateur
    path('api/generate_edt/<int:id_groupe>/<int:semaine>/<int:annee>/<int:id_admin>/', view_generator.generate_edt),
    path('api/get_prof_dispo/<int:semaine>/<int:annee>/', view_generator.get_prof_dispo_all),
    path('api/get_prof_dispo/<int:id_prof>/<int:semaine>/<int:annee>/', view_generator.get_prof_dispo),

    # Indisponibilités des salles
    path('api/get_salle_dispo_all/<int:semaine>/<int:annee>/', view_generator.get_salle_dispo_all),

    # Enseigne
    path('api/add-enseignes/', view_enseigne.add_enseigne),

    # Salles
    path('api/salles/', view_salles.get_all),
    path('api/salle/<int:code>/', view_salles.by_id),
    path('api/salle/', view_salles.add),

    # Utilisateurs
    path('api/utilisateurs/', view_utilisateurs.get_all),
    path('api/utilisateurs/professeur/', view_utilisateurs.get_all_professors),
    path('api/utilisateurs/professeur/<int:code>/ressource/', view_utilisateurs.get_ressourcesByUser),
    path('api/utilisateurs/professeurs/ressources/', view_utilisateurs.get_ressourcesAllUsers),
    path('api/utilisateurs/etudiant/', view_utilisateurs.get_all_students),
    path('api/utilisateur/<int:code>/', view_utilisateurs.by_id),
    path('api/utilisateur/', view_utilisateurs.add),

    # IndisponibiliteProf
    path('api/indisponibilites/', view_indisponibilite_prof.get_all),
    path('api/indisponibilite/<int:code>/', view_indisponibilite_prof.by_id),
    path('api/indisponibilite/', view_indisponibilite_prof.add),
    path('api/indisponibilite/professeur/<int:code>', view_indisponibilite_prof.get_indiponibility_by_user_id),

    # IndisponibiliteSalle
    path('api/indisponibilitesalle/', view_indisponibilite_salle.get_all),
    path('api/indisponibilitesalle/<int:code>/', view_indisponibilite_salle.by_id),
    path('api/indisponibilitesalle/', view_indisponibilite_salle.add),
    path('api/indisponibilitesalle/salle/<int:code>', view_indisponibilite_salle.get_indiponibility_by_salle_id),

    # Ressource
    path('api/ressources/', view_ressource.get_all),
    path('api/ressource/<int:code>/', view_ressource.by_id),
    path('api/ressource/', view_ressource.add),

    # Cours
    path('api/cours/', view_cours.get_all),
    path('api/cour/<int:code>/', view_cours.by_id),
    path('api/cour/', view_cours.add),

    # Groupe
    path('api/groupes/', view_groupe.get_all),
    path('api/groupes/etudiants/', view_groupe.get_all_etudiants),
    path('api/groupe/<int:code>/', view_groupe.by_id),
    path('api/groupe/', view_groupe.add),
    
    # EDT
    path('api/emploidutemps/<int:code>/', view_EDT.by_id),
    path('api/emploidutemps/<int:semaine>/<int:annee>/', view_EDT.get_all_by_semaine),
    path('api/emploidutemps/liste/<int:semaine>/<int:annee>/', view_EDT.by_list_groupe),
    path('api/emploidutemps/<int:semaine>/<int:annee>/<int:idGroupe>/', view_EDT.by_groupe),
    path('api/emploidutemps/professeur/<int:semaine>/<int:annee>/<int:idProf>/', view_EDT.by_enseignant),
    path('api/emploidutemps/', view_EDT.add),
    path('api/emploidutemps/save/<int:groupe>/<int:semaine>/<int:annee>/', view_EDT.save_edt),
    path('api/emploidutemps/save_all/<int:semaine>/<int:annee>/', view_EDT.save_all_edt),


    # Banque
    path('api/banques/', view_banque.GetAll),
    path('api/banque/<int:code>/', view_banque.by_id),
    path('api/banque/', view_banque.add),

    # TypeCours
    path('api/typecours/', view_type_cours.get_all),
    path('api/typecour/<int:code>/', view_type_cours.by_id),
    path('api/typecour/', view_type_cours.add),

    # Couleurs
    path('api/couleurs/', view_couleur.get_all),
    path('api/couleur/<int:code>/', view_couleur.by_id),
    path('api/couleur/', view_couleur.add),

]
