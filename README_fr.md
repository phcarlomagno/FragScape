
Nouveautés FragScape 2.0 :
 - mode Raster
 - algorithme pour comparer 2 couches résultat

# Aperçu

*FragScape* est un plugin QGIS 3.

Cet outil permet de calculer les indicateurs de fragmentation du paysage définis par Jaeger (Jaeger 2000). Parmi ces indicateurs, la taille effective de maille est très largement utilisée pour quantifier la fragmentation du paysage.

*FragScape* définit une procédure en 4 étapes depuis les données brutes jusqu’au calcul des indicateurs et permet de sauvegarder la configuration de l’outil afin de pouvoir reproduire les résultats.

*FragScape* a été développé par *Mathieu Chailloux* au sein d'[*INRAE*](http://www.inrae.fr), pour le [*centre de ressources Trame Verte et Bleue*](http://www.trameverteetbleue.fr/) 
(piloté par le [*Ministère de la Transition Écologique et Solidaire*](https://www.ecologique-solidaire.gouv.fr/)).

# Installation

Pour installer *FragScape*, QGIS 3.4 ou plus est nécessaire.
Aller dans le menu *Extension*, *Installer/Gérer les extensions*, activer les options expérimentales (onglet Paramètres) et *FragScape* doit être disponible. Une fois installé, une icône en forme de grille doît appraître dans la barre d'outils QGIS. Sinon, le plugin est disponible dans le menu *Extension*.

# Documentation

Documentation disponible:
 - [Notice d'utilisation de FragScape](https://github.com/MathieuChailloux/FragScape/blob/master/docs/FragScape_UserGuide_fr.pdf)
 - Tutoriels vidéo en cours de production

# Exemple

Des données d'exemple sont fournies avec le plugin ([lien](https://github.com/MathieuChailloux/FragScape/tree/qgis-lib-mc/sample_data/EPCI_Clermontais_2012))

Résultats avec la méthode CUT :

<img src="https://github.com/MathieuChailloux/FragScape/blob/master/docs/gifs/CUT.gif?raw=True" width="500"/>

Résultats avec la méthode CBC :

<img src="https://github.com/MathieuChailloux/FragScape/blob/master/docs/gifs/CBC.gif?raw=True" width="500"/>

Pour reproduire les résultats, cf section "Exemple" de la notice d'utilisation.
 
# Étapes

*FragScape* définit une procédure en 4 étapes :
 1. Définition des paramètres généraux
 2. Sélection des éléments d'occupation du sol
 3. Sélection des données complémentaires
 4. Calcul des indicateurs
    
Chaque étape est détaillé dans le panneau d'aide du plugin.

# Contact

Mathieu Chailloux (INRAE/UMR TETIS)- *mathieu.chailloux@inrae.fr*

Jennifer Amsallem(INRAE/UMR TETIS) - *jennifer.amsallem@inrae.fr*

Jean-Pierre Chéry (AgroParisTech/UMR TETIS) - *jean-pierre.chery@teledection.fr*

# Citation

> Chailloux, M. & Chéry, J.P. & Amsallem, J. (2019) FragScape : a QGIS plugin to quantify landscape fragmentation
    
# Liens
 - [Répertoire git de FragScape](https://github.com/MathieuChailloux/FragScape)
 - [INRAE](http://www.inrae.fr)
 - [AgroParisTech](http://www2.agroparistech.fr/)
 - [UMR TETIS](https://www.umr-tetis.fr)
 - [Centre de ressources Trame Verte et Bleue](http://www.trameverteetbleue.fr/)
 - [Ministère de la Transition Écologique et Solidaire](https://www.ecologique-solidaire.gouv.fr/)
