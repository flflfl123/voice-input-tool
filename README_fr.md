[中文](README_zh.md) | [English](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Русский](README_ru.md) | [Español](README_es.md) | [Français](README_fr.md) | [Deutsch](README_de.md) | [Português](README_pt.md)

# Saisie vocale — Mode d'emploi

## I. Présentation du logiciel

Il s'agit d'une méthode de saisie vocale pour la plateforme Windows qui s'appuie sur une API ASR (reconnaissance vocale) tierce. Appuyez sur le raccourci clavier pour commencer l'enregistrement, appuyez à nouveau pour l'arrêter : le texte reconnu est automatiquement inséré à la position actuelle du curseur.

## II. Fonctionnalités principales

- Reconnaissance vocale : déclenchez l'enregistrement via un raccourci clavier global, le résultat reconnu est automatiquement collé à l'emplacement du curseur
- Prise en charge multi-fournisseurs : prend en charge trois services ASR — format compatible OpenAI, modèle Doubao, Volcengine
- Fenêtre flottante : affiche l'état en temps réel pendant l'enregistrement (avec un fin liseré de la couleur du thème) ; le résultat est automatiquement copié dans le presse-papiers puis collé
- Historique : enregistre automatiquement chaque résultat de reconnaissance, prend en charge le format avec retrait de paragraphe
- Interface multilingue : 35 langues d'interface intégrées, associe automatiquement la police la plus appropriée
- Changement de thème : prend en charge les thèmes clair et sombre, toutes les couleurs des contrôles sont rafraîchies uniformément
- Réglage de la taille de police : ajustez le niveau de taille de police avec les flèches haut/bas (8 à 15, 10 par défaut), n'affecte que la police, pas les contrôles
- Personnalisation des raccourcis clavier : cliquez sur le bouton « Modifier » puis appuyez sur la combinaison de touches dans la fenêtre popup pour la capturer ; prend en charge les combinaisons de 1 à 3 touches
- Remplacement par mots chauds : inscrivez les mots rares dans la table des mots chauds, remplacement forcé par correspondance phonétique floue
- Remplacement par règles regex : remplacement précis du texte spécifié via des équations ou des règles regex
- Conversion numérique ITN : convertit automatiquement « 十五六个 » en « 15~16个 », prend en charge les plages, dates, pourcentages, fractions, etc. ; mots protégés intégrés pour éviter la conversion erronée de « 一会儿 » « 一样 »
- Suppression des tics de langage : supprime automatiquement les tics verbaux oraux tels que « 呃、啊、嗯 » (traitement local pur, sans LLM)
- Traitement par rôles LLM : lorsque le résultat de reconnaissance commence par un nom de rôle, il est confié au rôle LLM correspondant (raffinement, traduction, assistant, etc.) ; les fichiers de rôles sont analysés en toute sécurité via AST, seules les affectations littérales sont autorisées
- Commandes vocales : dites des commandes telles que « 撤销 » « 换行 » « 退格 » pour exécuter automatiquement l'action correspondante
- Archivage par journal : enregistre chaque saisie vocale et son résultat de reconnaissance par date
- Démarrage automatique : démarrage automatique au lancement du système (facultatif)
- Zone de notification système : réduction dans la zone de notification, clic gauche pour ouvrir la fenêtre principale, clic droit pour quitter

## III. Démarrage rapide

1. Après le lancement, le logiciel se réduit par défaut dans la zone de notification système
2. Clic gauche sur l'icône de la zone de notification pour ouvrir la fenêtre principale
3. Avant la première utilisation, rendez-vous sur la page « Configuration AI » pour remplir le fournisseur ASR et la clé API
4. Dans n'importe quelle fenêtre permettant la saisie de texte, placez le curseur à l'endroit où vous souhaitez saisir
5. Appuyez sur `Ctrl+Alt` pour commencer l'enregistrement (l'icône de la zone de notification devient rouge, la fenêtre flottante apparaît)
6. Parlez dans le microphone
7. Appuyez à nouveau sur `Ctrl+Alt` pour arrêter l'enregistrement
8. Le résultat de reconnaissance sera automatiquement collé à la position du curseur

> Astuce : si vous appuyez sur le raccourci d'enregistrement sans avoir configuré l'API, la fenêtre flottante affichera « AI 未配置 », veuillez d'abord terminer la configuration.

## IV. Description de l'interface

La fenêtre principale comporte une barre de navigation à gauche, avec les pages suivantes :

- Accueil : affiche l'état d'enregistrement et le dernier résultat de reconnaissance, avec un bouton de copie
- Journal : affiche en temps réel les logs d'exécution du programme, y compris les enregistrements, la reconnaissance et les informations de post-traitement
- Historique : parcourez les enregistrements de reconnaissance historiques, avec copie et affichage avec retrait de paragraphe
- Configuration AI : saisissez le fournisseur ASR, l'adresse API et la clé, le nom du modèle, etc. ; inclut les commutateurs « Activer le raffinement du texte » et « Activer les rôles LLM »
- Boîte à outils : regroupe les commutateurs des fonctions de post-traitement du texte (suppression de la ponctuation finale, ITN, suppression des tics de langage, mots chauds, règles regex, archivage par journal)
- Paramètres : paramètres généraux, y compris raccourcis clavier, thème, taille de police, langue d'interface, démarrage automatique, fenêtre flottante, etc.

## V. Détail des paramètres

### Paramètres ASR (page Configuration AI)

| Paramètre | Rôle |
| --- | --- |
| Fournisseur ASR | Sélectionnez le service de reconnaissance vocale : openai_compatible (compatible OpenAI), doubao (Doubao), volcengine (Volcengine) |
| base_url | Adresse de base de l'API compatible OpenAI |
| api_key | Clé de l'API compatible OpenAI |
| model | Nom du modèle, par exemple whisper-1 |
| app_key | Clé d'application Doubao / Volcengine |
| access_key | Clé d'accès Doubao / Volcengine |
| resource_id | ID de ressource Doubao |
| cluster | Nom du cluster Volcengine |
| asr_mode | Mode de reconnaissance ASR |
| Activer le raffinement du texte | Commutateur principal, désactivé n'appelle pas le LLM |
| Activer les rôles LLM | Uniquement disponible lorsque le raffinement du texte est activé, grisé sinon |

### Paramètres généraux (page Paramètres)

| Paramètre | Rôle |
| --- | --- |
| Raccourci clavier | Raccourci clavier global pour déclencher l'enregistrement, Ctrl+Alt par défaut ; cliquez sur « Modifier » pour capturer une nouvelle combinaison dans la fenêtre popup |
| Thème | Clair (light) ou sombre (dark), sombre par défaut |
| Taille de police | Niveau de taille de police 8 à 15, 10 par défaut ; ajustez avec les flèches haut/bas, n'affecte que la police pas les contrôles, prend effet après redémarrage |
| Langue d'interface | Change la langue d'affichage de l'interface, 35 langues disponibles |
| Démarrage automatique | Après activation, le programme démarre automatiquement au démarrage du système |
| Fenêtre flottante | Après activation, affiche la fenêtre flottante pendant l'enregistrement (avec un fin liseré de la couleur du thème) ; désactivée, le résultat ne s'affiche que dans la zone de texte de la fenêtre principale |

### Commutateurs de post-traitement du texte (page Boîte à outils)

| Paramètre | Rôle | Défaut |
| --- | --- | --- |
| Suppression de la ponctuation finale | Supprime automatiquement les virgules et points finals du résultat de reconnaissance | Activé |
| Conversion numérique ITN | Convertit « 十五六个 » en « 15~16个 » et d'autres formats numériques ; mots protégés intégrés pour éviter la conversion erronée de « 一会儿 » « 一样 » | Activé |
| Suppression des tics de langage | Supprime automatiquement les tics verbaux oraux tels que « 呃、啊、嗯 » (traitement local pur, sans LLM) | Activé |
| Remplacement par mots chauds | Remplacement forcé des mots rares par correspondance phonétique floue | Activé |
| Seuil de correspondance des mots chauds | Seuil de similarité des mots chauds, 0.0~1.0, plus élevé = plus strict | 0.85 |
| Remplacement par règles regex | Remplacement précis du texte via des équations ou des règles regex | Activé |
| Archivage par journal | Enregistre par date chaque saisie vocale et son résultat de reconnaissance | Activé |

> Les commutateurs liés au LLM (Activer le raffinement du texte, Activer les rôles LLM) se trouvent sur la page « Configuration AI », pas dans la Boîte à outils.

### Paramètres audio

| Paramètre | Rôle | Défaut |
| --- | --- | --- |
| sample_rate | Taux d'échantillonnage audio (Hz) | 16000 |
| chunk_size | Taille du bloc audio (octets) | 3200 |

## VI. Langues d'interface prises en charge

Le logiciel intègre les 35 langues d'interface suivantes, chacune étant automatiquement associée à la police la plus appropriée (chinois : Microsoft YaHei, japonais : Yu Gothic, coréen : Malgun Gothic, autres langues : Segoe UI) :

1. Chinois simplifié (zh_CN)
2. Chinois traditionnel (zh_TW)
3. Anglais (en)
4. Espagnol (es)
5. Arabe (ar)
6. Hindi (hi)
7. Indonésien (id)
8. Japonais (ja)
9. Français (fr)
10. Allemand (de)
11. Russe (ru)
12. Portugais (pt)
13. Italien (it)
14. Turc (tr)
15. Polonais (pl)
16. Néerlandais (nl)
17. Coréen (ko)
18. Vietnamien (vi)
19. Bengali (bn)
20. Ourdou (ur)
21. Philippin (fil)
22. Malais (ms)
23. Thaï (th)
24. Tchèque (cs)
25. Hongrois (hu)
26. Suédois (sv)
27. Finnois (fi)
28. Roumain (ro)
29. Ukrainien (uk)
30. Grec (el)
31. Danois (da)
32. Norvégien (no)
33. Hébreu (he)
34. Bulgare (bg)
35. Croate (hr)

Au premier lancement, la langue d'interface est automatiquement sélectionnée en fonction de la langue du système ; elle peut ensuite être changée manuellement sur la page « Paramètres ».

## VII. Questions fréquentes

### 1. Le raccourci clavier ne répond pas ?

- Vérifiez que le logiciel est en cours d'exécution dans la zone de notification système (l'icône grise signifie qu'il est prêt)
- Vérifiez que le raccourci n'est pas utilisé par un autre logiciel
- Allez sur la page « Paramètres », cliquez sur le bouton « Modifier » à côté du raccourci, puis appuyez à nouveau sur la combinaison de touches dans la fenêtre popup
- Vérifiez si la page Journal affiche des messages d'erreur

### 2. Que faire en cas d'échec de la reconnaissance ?

- Vérifiez que la clé API, l'adresse et le modèle remplis sur la page « Configuration AI » sont corrects
- Vérifiez que la connexion réseau est normale
- Ouvrez la page « Journal » pour voir les messages d'erreur détaillés
- Vérifiez que le microphone fonctionne correctement et que le volume de la voix est suffisant

### 3. Comment régler la taille de police ?

Allez sur la page « Paramètres », recherchez le paramètre « Taille de police », utilisez les flèches haut/bas à droite pour ajuster le niveau (8 à 15, 10 par défaut). Plus la valeur est élevée, plus la police est grande. Ce paramètre n'affecte que la police, pas la taille des contrôles tels que les boutons ; il faut redémarrer le programme pour qu'il prenne effet.

### 4. Comment personnaliser le raccourci clavier ?

Allez sur la page « Paramètres », recherchez le paramètre « Raccourci clavier », cliquez sur le bouton « Modifier » à droite, puis dans la fenêtre indépendante qui s'ouvre, appuyez sur la combinaison de touches souhaitée (prend en charge 1 à 3 touches, par exemple Ctrl+Shift+V). Une fois la capture terminée, cliquez sur « Confirmer » pour enregistrer ; le nouveau raccourci prendra effet après le redémarrage du programme.

### 5. Le résultat de reconnaissance n'est pas automatiquement collé ?

- Vérifiez que la fenêtre cible prend en charge l'opération de collage
- Vérifiez que le curseur est placé dans une zone de saisie
- Si la fenêtre flottante est désactivée, le résultat de reconnaissance ne s'affiche que dans la zone de texte de la fenêtre principale ; vous devez cliquer manuellement sur le bouton de copie

### 6. Comment ajouter des mots rares pour améliorer la reconnaissance ?

Éditez directement le fichier `config/hot.txt`, un mot chaud par ligne. Vous pouvez également utiliser `config/hot-rule.txt` pour effectuer un remplacement précis via des équations ou des règles regex.

### 7. Comment utiliser les rôles LLM ?

Créez un fichier `.py` dans le répertoire `config/roles/` et définissez les attributs du rôle par affectation de variables dans le fichier (name, trigger_words, system_prompt, output_mode, etc.). Les fichiers de rôles sont analysés en toute sécurité via AST, seules les affectations littérales sont autorisées, aucun appel de fonction ni code arbitraire n'est permis. Lorsque le résultat de reconnaissance commence par un nom de rôle, le rôle correspondant est automatiquement déclenché.
