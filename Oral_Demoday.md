# SCRIPT ORAL - DEMODAY 2026

**Duree** : ~20 minutes
**Focus** : Storytelling, parcours, produit, demonstration
**Audience** : Jury non-technique
**Fichier presentation** : `Presentation_demoday.html`

---

## SLIDE 1 : Titre Accrocheur (30 secondes)

### CE QUE VOUS DITES

> "Bonjour a tous ! Je m'appelle Samuel Verschueren et je vais vous presenter Mila-Assist.
>
> Imaginez un chatbot qui ne se contente pas de chercher des mots-cles, mais qui **comprend vraiment** ce que vous lui demandez. C'est exactement ce que j'ai construit."

---

## SLIDE 2 : Le Probleme (1 minute 30)

### CE QUE VOUS DITES

> "Laissez-moi vous raconter le probleme de depart.
>
> AI_licia est une plateforme innovante pour les streamers. Super produit, mais un probleme majeur : le support technique etait completement deborde.
>
> Avant Mila-Assist, c'etait du support 100% humain. Temps de reponse ? Des heures. Les memes questions revenaient en boucle. Et la nuit ? Personne pour repondre.
>
> Avec Mila-Assist, tout change. Reponse instantanee, 24 heures sur 24, 7 jours sur 7. Le systeme comprend les questions, meme formulees differemment. Il couvre 1366 sujets. Et le support humain peut enfin se concentrer sur les cas complexes.
>
> C'est le passage d'un support reactif a un support intelligent."

---

## SLIDE 3 : AI_licia - Le Contexte (1 minute 30)

### CE QUE VOUS DITES

> "Un mot sur AI_licia pour ceux qui ne connaissent pas.
>
> C'est une plateforme qui permet aux streamers de creer leur propre intelligence artificielle. Ils peuvent personnaliser la voix, l'apparence, le comportement. Cette IA interagit ensuite automatiquement avec les viewers pendant les streams.
>
> Mila-Assist est le support technique de cette plateforme. Quand un utilisateur se demande comment installer AI_licia, comment configurer la voix, ou pourquoi ca rame, c'est Mila qui repond.
>
> Quelques chiffres : 1366 questions couvertes dans la base de connaissances, disponibilite 24/7, et temps de reponse inferieur a 2 secondes."

---

## SLIDE 4 : Mon Parcours (2 minutes)

### CE QUE VOUS DITES

> "Laissez-moi vous raconter comment j'en suis arrive la.
>
> Les deux premiers mois, c'etait l'exploration. J'ai regarde les solutions existantes : ChatGPT, Claude, et d'autres. Le probleme ? Le cout des API peut exploser. Les donnees des utilisateurs partent sur des serveurs americains, donc probleme RGPD. Et surtout, ces modeles peuvent inventer des reponses, ce qu'on appelle les hallucinations.
>
> J'ai donc decide de tout construire en local avec une architecture RAG. RAG, ca veut dire que l'IA ne peut repondre qu'avec les informations de ma base de donnees. Pas d'invention possible.
>
> Les mois 3 et 4, c'etait le developpement intensif. Architecture avec 4 containers Docker, integration des technologies d'intelligence artificielle, et surtout beaucoup d'iterations sur le prompt engineering pour obtenir des reponses coherentes.
>
> Le dernier mois, optimisation et tests. Ma premiere version avait 72% de reussite. Aujourd'hui ? 90%. Chaque iteration a apporte son lot d'ameliorations."

---

## SLIDE 5 : Le Defi Technique - Vulgarise (1 minute 30)

### CE QUE VOUS DITES

> "Le coeur du defi, c'etait de faire comprendre le contexte a une machine.
>
> Prenons un exemple concret. Un utilisateur ecrit : 'Mon PC rame avec le TTS'. Un chatbot classique base sur les mots-cles va etre perdu. 'PC', ok c'est un ordinateur. 'Rame' ? Une pagaie de bateau ? 'TTS' ? Aucune idee.
>
> Mila-Assist, elle, analyse le contexte. 'PC' plus 'rame' plus 'TTS' dans la meme phrase. Elle comprend que 'rame' signifie lenteur en informatique, et que 'TTS' c'est le Text-to-Speech d'AI_licia. Resultat : elle propose une solution pour ameliorer les performances.
>
> C'est ca la difference entre un chatbot classique et une intelligence artificielle qui comprend vraiment."

---

## SLIDE 6 : Comment ca marche - Vulgarise (1 minute 30)

### CE QUE VOUS DITES

> "Alors comment ca fonctionne concretement ?
>
> Quand vous posez une question, Mila fait trois choses.
>
> Premiere etape : comprendre. La question est transformee en une sorte de code secret numerique. C'est comme traduire votre question dans un langage que la machine comprend parfaitement.
>
> Deuxieme etape : chercher. Mila parcourt sa memoire de 1366 questions et trouve les 5 plus proches de la votre. Cette recherche est ultra-rapide, quelques millisecondes.
>
> Troisieme etape : repondre. Avec ces 5 elements de contexte, l'intelligence artificielle formule une reponse naturelle et complete.
>
> Le tout en moins de 2 secondes."

---

## SLIDE 7 : L'Architecture - Vulgarise (1 minute)

### CE QUE VOUS DITES

> "Cote technique, j'ai une architecture simple mais robuste.
>
> D'un cote, les utilisateurs, que ce soit via l'application desktop ou l'interface web.
>
> De l'autre, un serveur NAS heberge chez moi. Ce serveur contient toute l'intelligence : l'API qui recoit les questions, le moteur d'intelligence artificielle qui comprend et genere les reponses, et la base de donnees avec les 1366 questions-reponses.
>
> Le point cle : tout est local. Pas de donnees qui partent sur le cloud. Pas de cout d'API mensuel. Conforme RGPD de A a Z."

---

## SLIDE 8 : Les Resultats (1 minute 30)

### CE QUE VOUS DITES

> "Passons aux resultats concrets.
>
> Premier chiffre : 90% de taux de reussite. Ca veut dire que 9 questions sur 10 trouvent une reponse pertinente dans le systeme. L'objectif etait 85%, donc mission accomplie et depassee.
>
> Deuxieme chiffre : 85% de qualite de classement. Ca mesure ou se trouve la bonne reponse. En moyenne, elle est presque toujours en premiere position.
>
> Troisieme chiffre : moins de 2 secondes pour le pipeline complet. De la question a la reponse, tout se passe quasi instantanement.
>
> Ces chiffres ne sont pas theoriques. Je les mesure en temps reel avec un endpoint de test que je vous montrerai pendant la demo."

---

## SLIDE 9 : Ce qui me rend fier (1 minute 30)

### CE QUE VOUS DITES

> "Parlons de ce qui me rend fier dans ce projet.
>
> Cote realisations : j'ai un systeme fonctionnel en production. Pas un prototype, un vrai produit qui tourne. Zero dependance au cloud, donc maitrise totale. Conforme RGPD puisque toutes les donnees restent locales. Et une architecture qui peut scaler si besoin.
>
> Cote competences, ce projet m'a fait grandir enormement. Machine Learning applique au traitement du langage. Architecture microservices avec Docker. Optimisation memoire avec la quantization. Gestion de projet avec des iterations successives.
>
> Le plus grand defi que j'ai resolu ? Faire tourner une intelligence artificielle complete sur un NAS de 8 GB de RAM sans carte graphique. C'etait un vrai puzzle technique."

---

## SLIDE 10 : Les Defis Rencontres (1 minute 30)

### CE QUE VOUS DITES

> "Bien sur, ca n'a pas ete un long fleuve tranquille. Laissez-moi vous raconter quelques defis.
>
> Premier probleme : memoire limitee. 8 GB de RAM pour tout le systeme. Solution : la quantization, une technique qui reduit l'empreinte memoire de 85%.
>
> Deuxieme probleme : pas de carte graphique. L'inference etait lente sur CPU. Solution : un format de modele optimise specifiquement pour le CPU.
>
> Troisieme probleme : les reponses sortaient parfois en anglais alors que je voulais du francais. Solution : des regles strictes dans le prompt.
>
> Quatrieme probleme : le modele inventait des liens internet fictifs. Solution : une interdiction absolue codee dans le prompt.
>
> Chaque probleme a ete une opportunite d'apprendre quelque chose de nouveau."

---

## SLIDE 11 : Demonstration Teaser (30 secondes)

### CE QUE VOUS DITES

> "Assez parle, place a l'action. Je vais vous montrer Mila-Assist en direct.
>
> Je vais faire trois tests. D'abord une question simple sur l'installation. Ensuite une question qui teste la comprehension, avec le fameux 'Mon PC rame'. Et enfin une question hors-sujet pour montrer que le systeme sait reconnaitre ses limites."

---

## SLIDE 12 : Demo Live (3-4 minutes)

### CE QUE VOUS FAITES

1. **Ouvrir l'interface web** : http://185.246.86.162:8080

2. **Test 1 - Question simple** :
   - Taper : "Comment installer AI_licia ?"
   - Montrer la reponse et le score de confiance
   - Commenter : "Confiance elevee, reponse complete"

3. **Test 2 - Comprehension semantique** :
   - Taper : "Mon PC rame avec le TTS"
   - Montrer la reponse
   - Commenter : "Le systeme a compris que 'rame' signifie lenteur"

4. **Test 3 - Question hors-sujet** :
   - Taper : "Quelle est la capitale de la France ?"
   - Montrer la confiance faible et le message d'avertissement
   - Commenter : "Le systeme reconnait qu'il ne sait pas"

5. **Page d'evaluation** (optionnel) :
   - Aller sur http://185.246.86.162:9000/api/v1/admin/evaluation?sample=20
   - Montrer les metriques en temps reel
   - Commenter : "C'est comme ca que je mesure les 90% de reussite"

### CE QUE VOUS DITES PENDANT LA DEMO

> "Voila l'interface. Simple et efficace.
>
> Premiere question : 'Comment installer AI_licia'. On voit la reponse qui arrive en moins de 2 secondes. Le score de confiance est eleve, ce qui indique que le systeme est sur de lui.
>
> Deuxieme question : 'Mon PC rame avec le TTS'. La, c'est interessant. Le systeme a compris que 'rame' dans ce contexte signifie lenteur informatique. Il propose des solutions de performance.
>
> Troisieme question : 'Quelle est la capitale de la France'. Regardez le score de confiance, il est bas. Le systeme dit clairement qu'il n'a pas trouve d'information pertinente. Il ne invente pas de reponse.
>
> Et si on va sur la page d'evaluation, on peut voir les metriques en temps reel sur un echantillon de 20 questions. C'est comme ca que j'obtiens les 90% de taux de reussite."

---

## SLIDE 13 : Perspectives d'Evolution (1 minute)

### CE QUE VOUS DITES

> "Et apres ? Quelles sont les perspectives ?
>
> A court terme, j'aimerais ameliorer l'interface utilisateur, ajouter plus de questions dans la base, et integrer un historique de conversation.
>
> A plus long terme, je vois du support vocal avec reconnaissance et synthese de parole, du multi-langues pour toucher plus d'utilisateurs, et pourquoi pas un apprentissage continu ou le systeme s'ameliore avec les retours des utilisateurs.
>
> La vision : un assistant intelligent qui evolue avec les besoins."

---

## SLIDE 14 : Ce que j'ai appris (1 minute 30)

### CE QUE VOUS DITES

> "Ce projet m'a enormement appris.
>
> En Machine Learning, j'ai decouvert les embeddings, les Transformers, et l'architecture RAG. En architecture logicielle, j'ai pratique les microservices et Docker. En optimisation, j'ai appris la quantization et le edge computing. Et en gestion de projet, j'ai compris l'importance des iterations.
>
> La lecon principale ? Un bon produit se construit par iterations. Ma premiere version avait 72% de reussite. En analysant les echecs, en ajustant les parametres, en testant encore et encore, je suis arrive a 90%.
>
> C'est cette approche iterative qui fait la difference."

---

## SLIDE 15 : Conclusion (1 minute)

### CE QUE VOUS DITES

> "En conclusion, Mila-Assist c'est :
>
> 90% de taux de reussite, ce qui depasse l'objectif initial. Zero euro de cout d'API mensuel. Disponible 24 heures sur 24.
>
> Ce projet demontre qu'il est possible de creer une intelligence artificielle performante, hebergee localement, sans cout d'API, conforme RGPD, sur du materiel accessible.
>
> L'intelligence artificielle au service de l'utilisateur, pas l'inverse.
>
> Merci pour votre attention."

---

## SLIDE 16 : Questions

### CE QUE VOUS DITES

> "Je suis maintenant disponible pour vos questions."

---

# QUESTIONS ANTICIPEES (non-techniques)

## Q1 : "Combien de temps a pris le projet ?"

> "Environ 5 mois au total. 2 mois d'exploration et de recherche, 2 mois de developpement intensif, et 1 mois d'optimisation et de tests. Mais le travail n'est jamais vraiment fini, il y a toujours des ameliorations a apporter."

## Q2 : "Pourquoi ne pas utiliser ChatGPT ?"

> "Trois raisons principales. Premierement, le cout : les API d'OpenAI peuvent couter plusieurs centaines d'euros par mois en fonction de l'usage. Deuxiemement, le RGPD : les donnees des utilisateurs partiraient sur des serveurs americains. Troisiemement, les hallucinations : ChatGPT peut inventer des reponses, ce qui est inacceptable pour du support technique."

## Q3 : "Ca coute combien a faire tourner ?"

> "Le cout est essentiellement l'electricite du NAS qui tourne 24/7, donc quelques euros par mois. Pas de cout d'API, pas d'abonnement cloud. L'investissement initial, c'est le NAS lui-meme, environ 500 euros."

## Q4 : "Et si la reponse n'est pas dans la base ?"

> "Le systeme le detecte grace au score de confiance. Si la similarite est trop faible, il indique clairement a l'utilisateur qu'il n'a pas trouve d'information pertinente. Il ne tente pas d'inventer une reponse."

## Q5 : "Comment avez-vous collecte les 1366 questions ?"

> "Elles proviennent de la documentation AI_licia, des FAQ existantes, et des questions frequemment posees au support humain. Chaque paire question-reponse a ete verifiee manuellement."

## Q6 : "C'est quoi le plus difficile dans ce projet ?"

> "L'optimisation memoire. Faire tourner une intelligence artificielle complete sur 8 GB de RAM sans GPU, c'etait un vrai defi. J'ai du apprendre la quantization, tester differents modeles, ajuster tous les parametres pour que ca rentre."

## Q7 : "Vous utiliseriez Mila-Assist dans d'autres contextes ?"

> "Absolument. L'architecture est generique. Il suffit de changer la base de questions-reponses pour l'adapter a un autre domaine : support produit, FAQ interne d'entreprise, assistance medicale non-diagnostic... Les possibilites sont nombreuses."

---

# TIMING RECOMMANDE

| Slide | Duree | Cumule |
|-------|-------|--------|
| 1. Titre | 30s | 0:30 |
| 2. Le Probleme | 1min30 | 2:00 |
| 3. AI_licia Contexte | 1min30 | 3:30 |
| 4. Mon Parcours | 2min | 5:30 |
| 5. Le Defi (vulgarise) | 1min30 | 7:00 |
| 6. Comment ca marche | 1min30 | 8:30 |
| 7. Architecture | 1min | 9:30 |
| 8. Les Resultats | 1min30 | 11:00 |
| 9. Fierte | 1min30 | 12:30 |
| 10. Defis | 1min30 | 14:00 |
| 11. Demo Teaser | 30s | 14:30 |
| 12. Demo Live | 3-4min | 18:00 |
| 13. Perspectives | 1min | 19:00 |
| 14. Apprentissages | 1min30 | (buffer) |
| 15. Conclusion | 1min | 20:00 |
| **Total** | | **~20 min** |

---

# CONSEILS SPECIFIQUES DEMODAY

## Ton et Style

- **Racontez une histoire** : "Laissez-moi vous raconter..."
- **Vulgarisez** : Evitez le jargon technique sauf si necessaire
- **Montrez votre enthousiasme** : C'est VOTRE projet, soyez fier
- **Utilisez des analogies** : "C'est comme..." pour expliquer les concepts

## Ce qui Impressionne

1. **La demo qui fonctionne** : C'est le moment "waouh"
2. **Les chiffres concrets** : 90%, 0 EUR, 24/7
3. **Le parcours personnel** : Les defis surmontes
4. **La vision** : Ou ca peut aller

## Ce qui NE fonctionne PAS

- Trop de technique (gardez ca pour l'entretien technique)
- Lire ses slides mot pour mot
- Parler trop vite par stress
- Une demo qui plante (testez avant !)

## Preparation Demo

1. Verifier la connexion internet 30 min avant
2. Avoir les URLs en favoris
3. Preparer des questions de secours si le serveur est lent
4. Avoir des captures d'ecran en backup

---

**Bonne presentation ! Vous allez cartonner !**
