# SCRIPT ORAL - ENTRETIEN TECHNIQUE ML 2026

**Duree** : ~20 minutes
**Fichier presentation** : `Presentation_technique.html`

---

## SLIDE 1 : Titre (30 secondes)

### CE QUE VOUS DITES

> "Bonjour, je m'appelle Samuel Verschueren. Je vais vous presenter Mila-Assist, un chatbot de support technique base sur une architecture RAG.
>
> Cette presentation se concentre sur les aspects Machine Learning du projet : le pipeline de tokenisation, les embeddings contextuels, la recherche vectorielle FAISS, et le SLM quantifie."

---

## SLIDE 2 : Projet & Contexte (1 minute)

### CE QUE VOUS DITES

> "AI_licia est une plateforme web pour streamers permettant de creer une IA personnalisee qui interagit automatiquement avec les viewers.
>
> Mila-Assist est le systeme de support technique pour cette plateforme. Il repond aux questions des utilisateurs sur l'installation, la configuration et l'utilisation.
>
> J'ai quatre contraintes majeures : hebergement local sur un NAS, precision superieure a 85%, zero cout d'API externe, et conformite RGPD."

---

## SLIDE 3 : Pipeline RAG - Vue d'ensemble (1 minute 30)

### CE QUE VOUS DITES

> "Le pipeline RAG se decompose en deux phases distinctes.
>
> **Phase d'indexation**, executee une seule fois : chaque document passe par la tokenisation, puis l'embedding avec CamemBERT, et enfin le stockage dans l'index FAISS.
>
> **Phase d'inference**, a chaque requete : la question utilisateur suit le meme chemin de tokenisation et embedding, puis FAISS retourne les 5 documents les plus similaires. Ces documents servent de contexte au SLM qui genere la reponse finale.
>
> L'avantage majeur du RAG : le modele ne peut pas halluciner car il reformule uniquement le contexte fourni par FAISS."

---

## SLIDE 4 : Indexation - Les 3 Etapes (2 minutes)

### CE QUE VOUS DITES

> "L'indexation comprend trois etapes critiques. La premiere est le **chunking**, c'est-a-dire comment decouper les documents.
>
> J'ai evalue trois strategies. Le chunking par taille fixe decoupe en blocs de N tokens, mais risque de couper des phrases importantes. Le chunking semantique decoupe par paragraphes, plus intelligent mais complexe.
>
> J'ai choisi l'approche **document-level** : une paire question-reponse egale un vecteur. Pourquoi ? Ma base contient 1366 paires Q&A courtes et autonomes. Chunker ces paires couperait le contexte necessaire au Self-Attention du modele.
>
> Concretement dans le code, je concatene la question et la reponse : `texte = f"{question} {reponse}"` et ca devient un embedding de 768 dimensions."

---

## SLIDE 5 : Tokenisation (2 minutes)

### CE QUE VOUS DITES

> "On n'embede pas des phrases directement. Le processus correct est tokenisation, puis embedding token par token, puis pooling.
>
> Prenons l'exemple 'Comment configurer le TTS ?'. D'abord, le tokenizer SentencePiece decoupe en tokens : 'Comment', 'configurer', 'le', 'TTS', '?'.
>
> Ensuite, chaque token passe par les couches du Transformer et obtient un embedding individuel. Enfin, le Mean Pooling fait la moyenne de tous ces embeddings pour obtenir le vecteur final de 768 dimensions.
>
> C'est ce vecteur final qui est stocke dans FAISS et utilise pour la recherche de similarite."

---

## SLIDE 6 : Embedding CamemBERT (1 minute 30)

### CE QUE VOUS DITES

> "Pour l'embedding, j'utilise le modele `antoinelouis/biencoder-camembert-base-mmarcoFR`. C'est CamemBERT, le BERT francais de Facebook, avec un fine-tuning sur le dataset MS MARCO en francais.
>
> J'ai compare plusieurs alternatives. Word2Vec est statique, le mot 'chat' aura toujours le meme vecteur que ce soit un animal ou une discussion Twitch. MiniLM multilingue dilue sa capacite sur 50 langues.
>
> CamemBERT MS MARCO concentre ses 110 millions de parametres sur le francais et est optimise pour la recherche semantique. C'est le meilleur compromis pour mon cas d'usage avec un Hit Rate de 90%."

---

## SLIDE 7 : Self-Attention (1 minute 30)

### CE QUE VOUS DITES

> "Le Self-Attention est le mecanisme cle qui permet la comprehension contextuelle.
>
> Prenons 'AI_licia repond dans le chat pendant le stream'. Le mot 'chat' calcule un score d'attention pour chaque autre mot. Il prete une attention moderee a 'repond' avec 0.65, mais une **tres forte attention** a 'stream' avec 0.88.
>
> Cette forte attention a 'stream' indique au modele que 'chat' designe une discussion Twitch, pas un animal. C'est la force du Self-Attention : comprendre le sens par le contexte.
>
> CamemBERT utilise 12 tetes d'attention en parallele. 768 dimensions divisees par 12 tetes egale 64 dimensions par tete."

---

## SLIDE 8 : Alternatives Evaluees (1 minute)

### CE QUE VOUS DITES

> "J'ai evalue plusieurs alternatives pour les embeddings.
>
> Word2Vec perd le contexte car les embeddings sont statiques. MiniLM multilingue est leger mais moins precis pour le francais. OpenAI ada-002 est excellent mais pose des problemes de cout et RGPD.
>
> CamemBERT MS MARCO offre la meilleure precision pour le francais, zero cout API, et conformite RGPD. C'est donc mon choix final."

---

## SLIDE 9 : FAISS - Recherche Vectorielle (1 minute 30)

### CE QUE VOUS DITES

> "Pour la recherche vectorielle, j'utilise FAISS de Facebook avec un index IndexFlatIP.
>
> Pourquoi IndexFlatIP ? C'est une recherche exhaustive, donc precision 100%, mais en complexite O(n). Avec mes 1366 vecteurs, ca reste tres rapide.
>
> Les alternatives comme IndexIVFFlat ou IndexHNSW sont plus rapides sur de gros volumes mais perdent 2 a 5% de precision. Pour moins de 10 000 vecteurs, IndexFlatIP est optimal.
>
> Je n'ai pas besoin d'approximation ANN car ma base est petite."

---

## SLIDE 10 : Similarite Cosinus (1 minute)

### CE QUE VOUS DITES

> "Une optimisation importante : j'utilise le produit scalaire sur des vecteurs normalises L2, ce qui est mathematiquement equivalent a la similarite cosinus mais plus rapide a calculer.
>
> Cote client, j'utilise `normalize_embeddings=True` dans le model.encode. Cote serveur, j'applique `faiss.normalize_L2` sur le vecteur de requete.
>
> IndexFlatIP exploite cette optimisation. La recherche prend environ 1.2 secondes parmi 1366 vecteurs."

---

## SLIDE 11 : SLM Gemma-2B (1 minute 30)

### CE QUE VOUS DITES

> "Precision terminologique importante : j'utilise un **SLM**, Small Language Model, pas un LLM. Gemma-2-2B a 2 milliards de parametres contre 70 milliards ou plus pour un vrai LLM comme GPT-4.
>
> Gemma-2 est le modele open-source de Google, licence Apache 2.0. La version IT signifie Instruction Tuned, donc optimisee pour suivre des instructions. Q4 indique la quantization 4 bits.
>
> Pourquoi un si petit modele suffit-il ? Pour du RAG, le modele n'a pas besoin de connaissances internes. Il reformule simplement le contexte fourni par FAISS. Un SLM de 2 milliards de parametres est amplement suffisant pour cette tache."

---

## SLIDE 12 : Quantization Q4 & GGUF (1 minute 30)

### CE QUE VOUS DITES

> "La quantization Q4 reduit chaque parametre de 32 bits a 4 bits. Calcul simple : 32 divise par 4 egale 8, donc 8 fois moins de memoire. En pratique, environ 85% de reduction RAM.
>
> Normalement, quantifier degrade la qualite de 5 a 10%. Mais pour du RAG, le SLM reformule un contexte fourni, il ne genere pas librement. La perte est compensee par la precision du contexte. En pratique, degradation de 0 a 2%, negligeable.
>
> Le format GGUF est specifique a llama.cpp, optimise pour l'inference CPU. Mon NAS actuel a 12 Go de RAM et une RTX 3060. Au debut du projet, je n'avais que 6 Go sans GPU, donc GGUF etait indispensable."

---

## SLIDE 13 : Prompt Systeme (1 minute)

### CE QUE VOUS DITES

> "Le prompt systeme utilise le format Instruct avec les balises [INST] et [/INST]. Le code se trouve dans `generateur_llm.py` ligne 97.
>
> J'ai du construire ce prompt par iterations pour obtenir des reponses coherentes. Deux regles critiques : la langue obligatoire francais car le modele tendait a repondre en anglais, et l'interdiction stricte d'inventer des URLs car le modele generait des liens fictifs.
>
> Les parametres importants : temperature basse a 0.3 pour des reponses focalisees, top-p a 0.9 et top-k a 40 pour la diversite, et maximum 512 tokens en sortie."

---

## SLIDE 14 : Fenetre de Contexte (1 minute)

### CE QUE VOUS DITES

> "La fenetre de contexte est de 4096 tokens, mais l'architecture est **stateless**.
>
> Ca signifie que l'historique de conversation n'est PAS inclus dans le contexte. Chaque requete est independante et contient : le prompt systeme d'environ 200 tokens, les 5 documents FAISS de 800 a 1500 tokens, la question utilisateur de 50 tokens environ, et la reponse generee de maximum 512 tokens.
>
> Au total, j'utilise environ 2000 a 2500 tokens sur les 4096 disponibles. Ce choix est volontaire pour simplifier l'architecture."

---

## SLIDE 15 : Architecture 4 Containers (1 minute 30)

### CE QUE VOUS DITES

> "L'architecture utilise 4 containers Docker sur un NAS avec 12 Go de RAM et une RTX 3060.
>
> Le client PyQt5 fait de l'edge computing : il charge CamemBERT localement et calcule l'embedding de chaque question. Le client web envoie la question brute, et le serveur calcule l'embedding.
>
> Le Container 2 API Backend valide la question et delegue au Container 3. Le Container 3 fait la recherche FAISS, recupere le contexte depuis MySQL Container 1, et genere la reponse avec le SLM.
>
> Cette architecture est tres scalable : chaque nouveau client PyQt5 calcule son propre embedding, donc zero charge serveur supplementaire pour cette partie."

---

## SLIDE 16 : Metriques avec Preuves (2 minutes)

### CE QUE VOUS DITES

> "Les metriques sont mesurables et reproductibles via l'endpoint d'evaluation.
>
> Hit Rate 90% signifie que 9 questions sur 10 trouvent au moins une reponse pertinente dans le top-5. MRR 85% signifie que la bonne reponse est en position moyenne 1.18, donc presque toujours en premiere position. Confiance moyenne 77.7% est la similarite cosinus moyenne.
>
> Le code est dans `routes_admin.py` lignes 273 a 287. D'abord on prend les top-K predictions de FAISS. Ensuite on calcule combien sont pertinents par intersection avec le ground truth. Le Hit Rate est binaire : 1 si au moins un resultat pertinent, 0 sinon. Le MRR est 1 divise par le rang du premier resultat pertinent.
>
> Vous pouvez tester en direct sur l'endpoint affiche."

---

## SLIDE 17 : Hit Rate vs Precision@K (1 minute)

### CE QUE VOUS DITES

> "Precision@5 divise le nombre de resultats pertinents par 5. Si je trouve 2 bons resultats sur 5, j'ai 40%. Mais cette metrique est biaisee : meme avec un systeme parfait, si une seule reponse est correcte, Precision@5 = 1/5 = 20%.
>
> Hit Rate est plus adapte a un chatbot : l'utilisateur veut TROUVER au moins une bonne reponse. C'est binaire : succes ou echec. Sur 20 questions, 18 trouvent une reponse pertinente, donc 90%.
>
> Le MRR complete en mesurant la position de cette bonne reponse. 85% signifie qu'elle est presque toujours en premiere position."

---

## SLIDE 18 : Demonstration (2 minutes)

### CE QUE VOUS DITES

> "Je vais maintenant vous montrer le systeme en action.
>
> Premier test, une question simple : 'Comment installer AI_licia'. Le systeme devrait retourner la procedure d'installation avec une confiance elevee.
>
> Deuxieme test, comprehension semantique : 'Mon PC rame avec le TTS'. Ici, le Self-Attention doit comprendre que 'rame' dans le contexte de 'PC' signifie 'lent', pas une pagaie de bateau.
>
> Troisieme test, question hors-sujet pour montrer que le score de confiance detecte les questions non pertinentes."

---

## SLIDE 19 : Succes & Apprentissages (1 minute)

### CE QUE VOUS DITES

> "En resume, les succes du projet : Hit Rate 90% qui depasse l'objectif de 85%, MRR 85% confirmant que les bonnes reponses sont bien classees, la quantization Q4 viable pour du RAG, et l'architecture hybride scalable avec Docker stable en production.
>
> Les apprentissages cles : le Self-Attention capture le contexte contrairement aux embeddings statiques, la normalisation L2 est une optimisation simple mais efficace, et un SLM suffit pour du RAG car il reformule du contexte."

---

## SLIDE 20 : Conclusion (1 minute)

### CE QUE VOUS DITES

> "Pour conclure, j'ai demontre plusieurs fondamentaux ML dans ce projet.
>
> Les embeddings contextuels avec CamemBERT, le mecanisme Self-Attention avec 12 tetes multi-head, la recherche vectorielle FAISS exhaustive, l'optimisation par normalisation L2, et la quantization Q4 avec 85% de reduction memoire.
>
> Le resultat : un pipeline ML optimise avec un Hit Rate de 90% et un MRR de 85%, tournant sur un client PyQt5 et 4 containers Docker."

---

## SLIDE 21 : Questions

### CE QUE VOUS DITES

> "Merci pour votre attention. Je suis disponible pour vos questions."

---

# QUESTIONS ANTICIPEES

## Q1 : "Quelle est votre strategie de chunking ?"

> "Ma strategie est document-level : une paire Q&A egale un vecteur. Je n'utilise pas de chunking par taille car ma base contient des paires Q&A courtes et autonomes. Chunker couperait le contexte necessaire au Self-Attention du SLM. Concretement, je concatene question et reponse pour creer un seul embedding de 768 dimensions."

## Q2 : "On n'embede pas des phrases, on embede des tokens. Expliquez."

> "Exact. Le processus correct est en trois etapes. Premiere etape : le tokenizer SentencePiece decoupe la phrase en tokens. Deuxieme etape : chaque token passe par les couches du Transformer et obtient un embedding individuel. Troisieme etape : le Mean Pooling fait la moyenne de tous ces embeddings pour obtenir le vecteur final de 768 dimensions. C'est ce vecteur agrege qui est stocke dans FAISS."

## Q3 : "Qu'est-ce qu'un LLM quantifie ?"

> "La quantization reduit la precision des poids du modele. En FP32, chaque parametre utilise 32 bits. En Q4, seulement 4 bits. Donc 8 fois moins de memoire, soit environ 85% de reduction. La degradation de qualite est de 5 a 10% pour de la generation libre, mais pour du RAG ou le modele reformule un contexte fourni, la perte est de 0 a 2%, negligeable."

## Q4 : "Quelle est la compatibilite GGUF ?"

> "GGUF est le format de llama.cpp, optimise pour l'inference CPU. C'est different de VLLM qui necessite un GPU. Mon NAS peut utiliser les deux maintenant avec la RTX 3060, mais j'ai garde GGUF pour la compatibilite. GGUF supporte aussi le GPU si disponible via le parametre n_gpu_layers."

## Q5 : "Avez-vous teste d'autres modeles que Gemma ?"

> "Oui, j'ai evalue plusieurs options. Mistral 7B etait trop gros pour mon NAS initial de 6 GB RAM. Llama-2-7B aussi. Les modeles plus petits comme TinyLlama 1B generaient des reponses moins coherentes. Gemma-2-2B en Q4 offre le meilleur equilibre entre qualite et consommation memoire pour mon cas d'usage."

## Q6 : "Quelle est votre fenetre de contexte ?"

> "4096 tokens, mais l'architecture est stateless. Chaque requete est independante : prompt systeme de 200 tokens, 5 documents FAISS de 800 a 1500 tokens, question de 50 tokens, reponse de max 512 tokens. L'historique de conversation n'est pas inclus pour simplifier l'architecture."

## Q7 : "Comment avez-vous construit votre prompt systeme ?"

> "Par iterations. Le prompt initial generait parfois des reponses en anglais, j'ai ajoute une regle absolue de francais. Il inventait des URLs fictives, j'ai ajoute une interdiction stricte. J'utilise le format Mistral Instruct avec [INST][/INST] car c'est le format sur lequel le modele a ete entraine."

## Q8 : "Quels sont les specs de votre NAS ?"

> "Le NAS actuel a 12 GB RAM, 4 coeurs CPU, et une RTX 3060. Au debut du projet, je n'avais que 6 GB sans GPU. La repartition : MySQL 1.5 GB, API Backend 2 GB, LLM+FAISS 3.5 GB, phpMyAdmin 512 MB."

## Q9 : "Pourquoi 768 dimensions / 12 tetes = 64 dimensions par tete ?"

> "C'est l'architecture du Multi-Head Attention. Le vecteur de 768 dimensions est divise en 12 sous-espaces de 64 dimensions chacun. Chaque tete d'attention travaille sur un sous-espace different, capturant des aspects contextuels differents. Ensuite, les 12 sorties sont concatenees pour reformer un vecteur de 768 dimensions."

## Q10 : "Comment stockez-vous les prompts dans la base de donnees ?"

> "Les prompts ne sont pas stockes en base. Le prompt systeme est code en dur dans `generateur_llm.py`. Seuls les historiques de conversation sont stockes dans MySQL : la question utilisateur, la reponse generee, le score de confiance, et les IDs des sources utilisees."

---

# TIMING RECOMMANDE

| Slide | Duree | Cumule |
|-------|-------|--------|
| 1. Titre | 30s | 0:30 |
| 2. Contexte | 1min | 1:30 |
| 3. Pipeline RAG | 1min30 | 3:00 |
| 4. Indexation/Chunking | 2min | 5:00 |
| 5. Tokenisation | 2min | 7:00 |
| 6. Embedding CamemBERT | 1min30 | 8:30 |
| 7. Self-Attention | 1min30 | 10:00 |
| 8. Alternatives | 1min | 11:00 |
| 9. FAISS | 1min30 | 12:30 |
| 10. Similarite Cosinus | 1min | 13:30 |
| 11. SLM Gemma | 1min30 | 15:00 |
| 12. Quantization GGUF | 1min30 | 16:30 |
| 13. Prompt Systeme | 1min | 17:30 |
| 14. Fenetre Contexte | 1min | 18:30 |
| 15. Architecture | 1min30 | 20:00 |
| 16-17. Metriques | 3min | (demo) |
| 18. Demo | 2min | (demo) |
| 19. Succes | 1min | |
| 20. Conclusion | 1min | |
| **Total** | | **~20-25 min** |

---

# PIEGES A EVITER

- NE PAS dire "On embede des phrases" -> dire "On tokenise puis embede token par token"
- NE PAS dire "WordPiece" -> CamemBERT utilise **SentencePiece**
- NE PAS confondre indexation (document -> vecteur) et reconstruction index (structure FAISS)
- NE PAS dire "LLM" -> dire "SLM" (Small Language Model, 2B parametres)
- NE PAS confondre GGUF (CPU/llama.cpp) et VLLM (GPU)
- NE PAS dire "12 x 64 = 768" -> dire "768 / 12 = 64 dimensions par tete"

---

**Bonne presentation !**
