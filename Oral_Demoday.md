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
> Avec Mila-Assist, tout change. Reponse 24 heures sur 24, 7 jours sur 7. Le systeme comprend les questions, meme formulees differemment. Une base de connaissances complete. Et le support humain peut enfin se concentrer sur les cas complexes.
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
> En resume : une base de connaissances complete, disponibilite 24/7, et un temps de reponse variable selon la complexite."

---

## SLIDE 4 : Le Defi Technique - Vulgarise (1 minute 30)

### CE QUE VOUS DITES

> "Le coeur du defi, c'etait de faire comprendre le contexte a une machine.
>
> Prenons un exemple concret. Un utilisateur ecrit : 'Mon PC rame avec le TTS'. Un chatbot classique base sur les mots-cles va etre perdu. 'PC', ok c'est un ordinateur. 'Rame' ? Une pagaie de bateau ? 'TTS' ? Aucune idee.
>
> Mila-Assist, elle, analyse le contexte. 'PC' plus 'rame' plus 'TTS' dans la meme phrase. Elle comprend que 'rame' signifie lenteur en informatique, et que 'TTS' c'est le Text-to-Speech d'AI_licia. Resultat : elle propose une solution pour ameliorer les performances.
>
> C'est ca la difference entre un chatbot classique et une intelligence artificielle qui comprend vraiment."

---

## SLIDE 5 : Comment ca marche - Vulgarise (1 minute 30)

### CE QUE VOUS DITES

> "Alors comment ca fonctionne concretement ?
>
> Quand vous posez une question, Mila fait trois choses.
>
> Premiere etape : comprendre. La question est transformee en une sorte de code secret numerique. C'est comme traduire votre question dans un langage que la machine comprend parfaitement.
>
> Deuxieme etape : chercher. Mila parcourt sa base de connaissances et trouve les 5 questions les plus proches de la votre. Cette recherche est ultra-rapide.
>
> Troisieme etape : repondre. Avec ces 5 elements de contexte, l'intelligence artificielle formule une reponse naturelle et complete.
>
> Le tout en moins de 2 secondes."

---

## SLIDE 6 : L'Architecture - Vulgarise (1 minute)

### CE QUE VOUS DITES

> "Cote technique, j'ai une architecture simple mais robuste.
>
> D'un cote, les utilisateurs, que ce soit via l'application desktop ou l'interface web.
>
> De l'autre, un serveur local. Ce serveur contient toute l'intelligence : l'API qui recoit les questions, le moteur d'intelligence artificielle qui comprend et genere les reponses, et la base de connaissances.
>
> Le point cle : tout est local. Pas de donnees qui partent sur le cloud. Pas de cout d'API mensuel. Souverainete des donnees garantie."

---

## SLIDE 7 : Les Resultats (1 minute 30)

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

## SLIDE 8 : Ce qui me rend fier (1 minute 30)

### CE QUE VOUS DITES

> "Parlons de ce qui me rend fier dans ce projet.
>
> Cote realisations : j'ai un systeme fonctionnel en production. Pas un prototype, un vrai produit qui tourne. Zero dependance au cloud, donc maitrise totale. Souverainete des donnees puisque tout reste local. Et une architecture qui peut scaler si besoin.
>
> Cote competences, ce projet m'a fait grandir enormement. Machine Learning applique au traitement du langage. Architecture microservices avec Docker. Optimisation memoire avec la quantization. Gestion de projet avec des iterations successives.
>
> Le plus grand defi que j'ai resolu ? Faire tourner une intelligence artificielle complete sur un serveur avec des ressources limitees. C'etait un vrai puzzle technique."

---

## SLIDE 9 : Les Defis Rencontres (1 minute 30)

### CE QUE VOUS DITES

> "Bien sur, ca n'a pas ete un long fleuve tranquille. Laissez-moi vous raconter quelques defis.
>
> Premier probleme : memoire limitee. Solution : la quantization, une technique qui reduit l'empreinte memoire de 85%.
>
> Deuxieme probleme : ressources limitees au debut. Solution : optimiser le format du modele et upgrader progressivement le serveur.
>
> Troisieme probleme : les reponses sortaient parfois en anglais alors que je voulais du francais. Solution : des regles strictes dans le prompt.
>
> Quatrieme probleme : le modele inventait des liens internet fictifs. Solution : une interdiction absolue codee dans le prompt.
>
> Chaque probleme a ete une opportunite d'apprendre quelque chose de nouveau."

---

## SLIDE 10 : Demonstration Live (3-4 minutes)

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

> "Assez parle, place a l'action. Je vais vous montrer Mila-Assist en direct avec trois tests.
>
> Voila l'interface. Simple et efficace.
>
> Premiere question : 'Comment installer AI_licia'. On voit la reponse qui arrive en moins de 2 secondes. Le score de confiance est eleve, ce qui indique que le systeme est sur de lui.
>
> Deuxieme question : 'Mon PC rame avec le TTS'. La, c'est interessant. Le systeme a compris que 'rame' dans ce contexte signifie lenteur informatique. Il propose des solutions de performance.
>
> Troisieme question : 'Quelle est la capitale de la France'. Regardez le score de confiance, il est bas. Le systeme dit clairement qu'il n'a pas trouve d'information pertinente. Il ne invente pas de reponse.
>
> Et si on va sur la page d'evaluation, on peut voir les metriques en temps reel sur un echantillon de 20 questions. C'est comme ca que j'obtiens les 90% de taux de reussite."

---

## SLIDE 11 : Perspectives d'Evolution (1 minute)

### CE QUE VOUS DITES

> "Et apres ? Quelles sont les perspectives ?
>
> A court terme, j'aimerais ameliorer l'interface utilisateur, ajouter plus de questions dans la base, et integrer un historique de conversation.
>
> A plus long terme, je vois du support vocal avec reconnaissance et synthese de parole, du multi-langues pour toucher plus d'utilisateurs, et pourquoi pas un apprentissage continu ou le systeme s'ameliore avec les retours des utilisateurs.
>
> La vision : un assistant intelligent qui evolue avec les besoins."

---

## SLIDE 12 : Ce que j'ai appris (1 minute 30)

### CE QUE VOUS DITES

> "Ce projet m'a enormement appris.
>
> En Machine Learning, j'ai decouvert les embeddings, les Transformers, et l'architecture RAG. En architecture logicielle, j'ai pratique les microservices et Docker. En optimisation, j'ai appris la quantization et le edge computing. Et en gestion de projet, j'ai compris l'importance des iterations.
>
> La lecon principale ? Un bon produit se construit par iterations. Ma premiere version avait 72% de reussite. En analysant les echecs, en ajustant les parametres, en testant encore et encore, je suis arrive a 90%.
>
> C'est cette approche iterative qui fait la difference."

---

## SLIDE 13 : Conclusion (1 minute)

### CE QUE VOUS DITES

> "En conclusion, Mila-Assist c'est :
>
> 90% de taux de reussite, ce qui depasse l'objectif initial. Zero euro de cout d'API mensuel. Disponible 24 heures sur 24.
>
> Ce projet demontre qu'il est possible de creer une intelligence artificielle performante, hebergee localement, sans cout d'API, avec souverainete des donnees, sur du materiel accessible.
>
> L'intelligence artificielle au service de l'utilisateur, pas l'inverse.
>
> Merci pour votre attention."

---

## SLIDE 14 : Questions

### CE QUE VOUS DITES

> "Je suis maintenant disponible pour vos questions."

---

# QUESTIONS ANTICIPEES (non-techniques)

## Q1 : "Combien de temps a pris le projet ?"

> "Quelques mois de developpement. J'avais deja fait des recherches en amont sur les solutions existantes. Ensuite du developpement intensif et une phase d'optimisation et de tests. Mais le travail n'est jamais vraiment fini, il y a toujours des ameliorations a apporter."

## Q2 : "Pourquoi ne pas utiliser ChatGPT ?"

> "Trois raisons principales. Premierement, le cout : les API d'OpenAI peuvent couter plusieurs centaines d'euros par mois en fonction de l'usage. Deuxiemement, la souverainete des donnees : les donnees des utilisateurs partiraient sur des serveurs externes. Troisiemement, les hallucinations : ChatGPT peut inventer des reponses, ce qui est inacceptable pour du support technique."

## Q3 : "Ca coute combien a faire tourner ?"

> "Le cout est essentiellement l'electricite du NAS qui tourne 24/7, donc quelques euros par mois. Pas de cout d'API, pas d'abonnement cloud. L'investissement initial, c'est le NAS lui-meme, environ 500 euros."

## Q4 : "Et si la reponse n'est pas dans la base ?"

> "Le systeme le detecte grace au score de confiance. Si la similarite est trop faible, il indique clairement a l'utilisateur qu'il n'a pas trouve d'information pertinente. Il ne tente pas d'inventer une reponse."

## Q5 : "Comment avez-vous collecte les questions de la base ?"

> "Elles proviennent de la documentation AI_licia, des FAQ existantes, et des questions frequemment posees au support humain. Chaque paire question-reponse a ete verifiee manuellement."

## Q6 : "C'est quoi le plus difficile dans ce projet ?"

> "L'optimisation memoire. Faire tourner une intelligence artificielle complete sur un serveur avec des ressources limitees, c'etait un vrai defi. J'ai du apprendre la quantization, tester differents modeles, ajuster tous les parametres."

## Q7 : "Vous utiliseriez Mila-Assist dans d'autres contextes ?"

> "Absolument. L'architecture est generique. Il suffit de changer la base de questions-reponses pour l'adapter a un autre domaine : support produit, FAQ interne d'entreprise, assistance medicale non-diagnostic... Les possibilites sont nombreuses."

---

# TIMING RECOMMANDE

| Slide | Duree | Cumule |
|-------|-------|--------|
| 1. Titre | 30s | 0:30 |
| 2. Le Probleme | 1min30 | 2:00 |
| 3. AI_licia Contexte | 1min30 | 3:30 |
| 4. Le Defi (vulgarise) | 1min30 | 5:00 |
| 5. Comment ca marche | 1min30 | 6:30 |
| 6. Architecture | 1min | 7:30 |
| 7. Les Resultats | 1min30 | 9:00 |
| 8. Fierte | 1min30 | 10:30 |
| 9. Defis | 1min30 | 12:00 |
| 10. Demo Live | 4-5min | 17:00 |
| 11. Perspectives | 1min | 18:00 |
| 12. Apprentissages | 1min | 19:00 |
| 13. Conclusion | 1min | 20:00 |
| 14. Questions | - | - |
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
