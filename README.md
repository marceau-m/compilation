# Advanced Compilation: compilation d'un code en C--

### Contributeurs

- Erwan Lebailly
- Nicolas Jaboulay
- Marceau Mathieu

### Fonctionnalitées ajoutées

- float
- pointeurs
- typage dynamique à la python


## Nos résultats

### float

Les float sont fonctionnels, il est possible de déclarer des variables à virgules, d'effectuer des opérations, de les utiliser dans des boucles while ou if, (Z>1.0)

Pour cela nous avons défini chaque nombre à virgule apparaissant dans le code comme une variable en elle même sous la forme _floati pour la réutiliser le moment venu

La plupart du code est proche des int avec l'utilisation des registres xmm0 ou xmm1 et des fonctions addsd au lieu de add

### pointeurs

Les pointeurs simples et doubles sont pris en charge, les adresses. Pour en définir un il faut lui fournir l'adresse d'une variable vers laquelle pointer ou le définir grâce à un malloc
Il n'y a pas d'arithmétique des pointeurs, ni de pointage vers un float
Un point d'amélioration est d'améliorer la grammaire afin de prendre en charge les pointeurs multiples et de la rendre "plus belle" que de définir chaque pointeur à la main


### typage dynamique

Concernant le typage, on est capable de faire de nombreuses opérations entre les int et les float

- opération float/int, si l'un des deux est float alors le résultat est un float
- cast permettant de transformer un int en float ou un float en int
- changement de type d'une variable, Z=1 puis Z=3.14 

Les problèmes que nous avons rencontré ont notamment été lorsqu'il y a un changement de type dans une boucle, si on ne passe pas dans la boucle alors le type ne change pas, cependant le compilateur ne peut pas savoir s'il va y avoir un passage dans la boucle ou non. 
Nous n'avons pas trouvé de solution permettant de résoudre complétement ce problème, ainsi lorsqu'il y a un changement de type dans une boucle il faut y passer au moins une fois dedans. L'exemple 4 témoigne de ce problème ou le 1er et 2ème print renvoient 0.0 car le type de Y a changé puis celui de Z


## Script bash pour simplifier les commandes

Il suffit de lancer la commande `./run.sh arg0 arg1 ...` après avoir entré l'exemple désiré à la fin du code python et l'exemple est compilé et run directement

## Exemples

Les exemples sont au format cmm pour C-- et illustrent des particularités de nos implémentations

L'exemple 1 doit printer 1 0 3.14 8 pour 2 et 3 en entrée

L'exemple 2 doit printer 9.0 2 pour 2 en entrée

L'exemple 3 doit printer 3 5.0 2 pour 2 en entrée

L'exemple 4 doit printer 0.0 0.0 2 pour 2 en entrée (problème de typage mentionné plus haut)

L'exemple 5 doit printer 5.0 1 2 pour 2 en entrée

L'exemple 6 doit printer 2 3 2 0.8 2 pour 2 en entrée

L'exemple 7 doit printer addr1 3 addr2 addr3 4 addr3 4 pour 2 en entrée (adresses memoire, malloc)

L'exemple 8 doit printer 6 addr1 4 addr1 7 addr1 pour 2 en entrée (pointeurs)

L'exemple 9 doit printer addr1 3 addr1 addr2 pour 2 en entrée (doubles pointeurs)
