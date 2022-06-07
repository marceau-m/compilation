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

### typage dynamique

Concernant le typage, on est capable de faire de nombreuses opérations entre les int et les float

- opération float/int, si l'un des deux est float alors le résultat est un float
- cast permettant de transformer un int en float ou un float en int
- changement de type d'une variable, Z=1 puis Z=3.14 

Les problèmes que nous avons rencontré ont notamment été lorsqu'il y a un changement de type dans une boucle, si on ne passe pas dans la boucle alors le type ne change pas, cependant le compilateur ne peut pas savoir s'il va y avoir un passage dans la boucle ou non. 
La solution que nous avons apporté à été de créer un changement de type conditionnel au passage ou non dans la boucle, si on ne passe pas dans la boucle on execute un code avec les anciens types, si on passe dedans on execute la boucle puis un code avec les nouveaux types, le tout géré par des jump.


## Script bash pour simplifier les commandes

Il suffit de lancer la commande `./run.sh arg0 arg1 ...` après avoir entré l'exemple désiré à la fin du code python et l'exemple est compilé et run directement, le code assembleur est disponible dans le fichier hum.asm

## Exemples

Les exemples sont au format cmm pour C-- et illustrent des particularités de nos implémentations

L'exemple 1 doit printer 1 0 8 pour 2 et 3 en entrée

L'exemple 2 doit printer 9.0 2 pour 2 en entrée

L'exemple 3 doit printer pour 2 en entrée

L'exemple 4 doit printer pour 2 en entrée

L'exemple 5 doit printer 5.0 1 2 pour 2 en entrée

L'exemple 6 doit printer 2 3 2 0.8 2 pour 2 en entrée
