# SCRIPT ORAL - ENTRETIEN TECHNIQUE ML 2026

**Duree** : ~25 minutes
**Fichier presentation** : `Presentation_technique.html`

---

## SLIDE 1 : Titre (30 secondes)

> "Bonjour, je m'appelle Samuel Verschueren. Je vais vous presenter Mila-Assist, un chatbot de support technique.
> 
> Cette presentation se concentre sur les aspects Machine Learning du projet : le pipeline de tokenisation, les embeddings contextuels, la recherche vectorielle FAISS, et le SLM quantifie."

---

## SLIDE 2 : Projet & Contexte (1 minute)

> "AI_licia est une plateforme web pour streamers permettant de creer une IA personnalisee qui interagit automatiquement avec les viewers.
> 
> Mila-Assist est le systeme de support technique pour cette plateforme. Il repond aux questions des utilisateurs sur l'installation, la configuration et l'utilisation.

---

## SLIDE 3 : Pipeline RAG - Vue d'ensemble (1 minute 30)

> "Le pipeline RAG se decompose en deux phases distinctes.
> 
> **Phase d'indexation**, executee une seule fois : chaque document passe par la tokenisation, puis l'embedding avec CamemBERT, et enfin le stockage dans l'index FAISS.
> 
> **Phase d'inference**, a chaque requete : la question utilisateur suit le meme chemin de tokenisation et embedding, puis FAISS retourne les 5 documents les plus similaires. Ces documents servent de contexte au SLM qui genere la reponse finale.

---

## SLIDE 4 : Indexation - Les 3 Etapes (2 minutes)

> "L'indexation comprend trois etapes critiques. La premiere est le **chunking**, c'est-a-dire comment decouper les documents.
> 
> J'ai evalue trois strategies. Le chunking par taille fixe decoupe en blocs de N tokens, mais risque de couper des phrases importantes. Le chunking semantique decoupe par paragraphes, plus intelligent mais complexe.
> 
> J'ai choisi l'approche **document-level** : une paire question-reponse egale un vecteur. Pourquoi ? Ma base contient peu de Q&R courtes. Chunker ces paires couperait le contexte necessaire au Self-Attention du modele.

---

## SLIDE 5 : Tokenisation (2 minutes)

> "On tokenisation, puis on embed token par token, puis **pooling**.
> 
> Prenons l'exemple 'Comment configurer le TTS ?'. D'abord, le tokenizer **SentencePiece** decoupe en tokens : 'Comment', 'configurer', 'le', 'TTS', '?'.
> 
> Ensuite, chaque token passe par les couches du Transformer et obtient un embedding individuel. Enfin, le **Mean Pooling** fait la moyenne de tous ces embeddings pour obtenir le vecteur final de 768 dimensions.
> 
> C'est ce vecteur final qui est stocke dans FAISS et utilise pour la recherche de similarite."

---

## SLIDE 6 : Embedding CamemBERT (1 minute 30)

> "Pour l'embedding, j'utilise le modele camembert  avec un fine-tuning sur le dataset MS MARCO en francais.
> 
> J'ai compare plusieurs alternatives. Word2Vec est statique, le mot 'chat' aura toujours le meme vecteur que ce soit un animal ou une discussion Twitch. MiniLM multilingue dilue sa capacite sur 50 langues.
> 
> CamemBERT MS MARCO concentre ses 110 millions de parametres sur le francais et est optimise pour la recherche semantique. C'est le meilleur compromis pour mon cas d'usage avec un Hit Rate de 90%."

---

## SLIDE 7 : Self-Attention (1 minute 30)

> "Le Self-Attention est le mecanisme cle qui permet la comprehension contextuelle.
> 
> Prenons :
> 'AI_licia repond dans le chat pendant le stream'.
> 
> Le mot 'chat' calcule un score d'attention pour chaque autre mot. 
> 
> Il prete une attention moderee a '**répond**', mais une **tres forte attention** a 'stream'.
> 
> Cette forte attention a 'stream' indique au modele que 'chat' designe une discussion Twitch, pas un animal. C'est la force du Self-Attention : comprendre le sens par le contexte.

## SLIDE 8 : Alternatives Evaluees (1 minute)

> "J'ai evalue plusieurs alternatives pour les embeddings.
> 
> Word2Vec perd le contexte car les embeddings sont statiques. MiniLM multilingue est leger mais moins precis pour le francais. OpenAI est excellent mais pose des problemes de cout et de souveraineté des données.
> 
> CamemBERT MS MARCO offre la meilleure precision pour le francais, zero cout API, et nous somme souveraint de nos données. C'est donc pour moi le choix idéal."

---

## SLIDE 9 : FAISS - Recherche Vectorielle (1 minute 30)

> "Pour la recherche vectorielle, j'utilise FAISS de Facebook avec un index IndexFlatIP.
> 
> Pourquoi IndexFlatIP ? C'est une recherche exhaustive, donc precision 100%. Avec mes une base de connaissance avec peu de vecteur comme moi, ca reste tres rapide.
> 
> Les alternatives comme IndexIVFFlat ou IndexHNSW sont plus rapides sur de gros volumes mais perdent en precision. Pour moins de 10 000 vecteurs, IndexFlatIP est optimal.
> 
> "

---

## SLIDE 10 : Similarite Cosinus (1 minute)

> "La similarité entre vecteurs est calculée avec le produit scalaire sur des vecteurs normalisés L2.
> 
> La normalisation L2 transforme chaque vecteur en vecteur unitaire de norme 1. Après normalisation, le produit scalaire est mathématiquement équivalent à la similarité cosinus, mais beaucoup plus rapide à calculer.
> 
> Cette optimisation permet d'obtenir un temps de recherche d'environ 1.2 secondes pour comparer avec toute ma base de connaissances.
> 
> Le score retourné est entre 0 et 1 : plus le score est proche de 1, plus les deux phrases sont sémantiquement similaires.

---

## SLIDE 11 : SLM Gemma-2B (1 minute 30)

> " j'utilise le **SLM**, Small Language Model, Gemma-2-2B a 2 milliards de parametres.
> 
> Gemma-2 est le modele open-source de Google. La version IT signifie Instruction Tuned, donc optimisee pour suivre des instructions. Q4 indique la quantization 4 bits.
> 
> Pourquoi un si petit modele suffit-il ? Pour du RAG, le modele n'a pas besoin de connaissances internes. Il reformule simplement le contexte fourni par FAISS. Un SLM de 2 milliards de parametres est amplement suffisant pour cette tache."

---

## SLIDE 12 : Quantization Q4 & GGUF (1 minute 30)

> "La quantization Q4 reduit chaque parametre de 32 bits a 4 bits. Cela permet donc d'utiliser 8 fois moins de memoire. En pratique, environ 85% de reduction RAM.
> 
> Normalement, quantifier degrade la qualite. Mais pour du RAG, le SLM reformule un contexte fourni, il ne genere pas librement. La perte est compensee par la precision du contexte. 
> 
> GGUF est le format natif de llama.cpp. Il permet une inference efficace avec quantification, que ce soit sur CPU ou GPU avec CUDA. Au debut du projet sans GPU, c'etait le seul moyen viable de faire tourner un modele de 2 milliards de parametres."

---

## SLIDE 13 : Prompt Systeme (30 secondes)

> "Le prompt utilise le format Instruct. Deux regles critiques construites par iterations : francais obligatoire et interdiction d'inventer des URLs."

---

## SLIDE 14 : Prompt Systeme 2/2 & Parametres (30 secondes)

> "Le parametres N_CTX a 4096 definit combien de tokens le modele peut voir en meme temps. La temperature a 0.3 reduit l'aleatoire dans les choix de mots, donc des reponses plus determininistes et coherentes. Repetition penalty a 1.3 penalise les mots deja utilises pour eviter les boucles de repetition.

---

## SLIDE 15 : Fenetre de Contexte (1 minute)

> "L'architecture est **stateless**, l'historique de conversation n'est PAS inclus dans le contexte.
> 
> Chaque requete est independante et contient : le prompt systeme d'environ 200 tokens, les 5 documents FAISS de 800 a 1500 tokens, la question utilisateur de 50 tokens, et la reponse generee de maximum 512 tokens.
> 
> Au total, j'utilise environ 2000 a 2500 tokens sur les 4096 disponibles."

---

## SLIDE 16 : Architecture 4 Containers (30 secondes)

> "Pour mon Architecture j'utilise 4 containers Docker. Le point cle : le client PyQt5 calcule l'embedding localement, donc scalable sans charge serveur supplementaire c'est une evolution future pour le client web"

---

## SLIDE 17 : Metriques avec Preuves (2 minutes)

> "Les metriques sont mesurables et reproductibles via l'endpoint d'evaluation.
> 
> Hit Rate 90% signifie que 9 questions sur 10 trouvent au moins une reponse pertinente dans le top-5. MRR 85% signifie que la bonne reponse est en position moyenne 1.18, donc presque toujours en premiere position. Confiance moyenne 77.7% est la similarite cosinus moyenne.
> 
> Pour avoir ses information. D'abord on prend les top-K predictions de FAISS. Ensuite on calcule combien sont pertinents par intersection avec le ground truth. Le Hit Rate est binaire : 1 si au moins un resultat pertinent, 0 sinon. Le MRR est 1 divise par le rang du premier resultat pertinent.
> 
> Vous pouvez tester en direct sur l'endpoint affiche."

---

## SLIDE 18 : Hit Rate vs Precision@K (1 minute)

> "Precision@5 divise le nombre de resultats pertinents par 5. Si je trouve 2 bons resultats sur 5, j'ai 40%. Mais cette metrique est biaisee : meme avec un systeme parfait, si une seule reponse est correcte, Precision@5 = 1/5 = 20%.
> 
> le Hit Rate est plus adapte a un chatbot car l'utilisateur veut TROUVER au moins une bonne reponse. C'est binaire : succes ou echec. Sur 20 questions, 18 trouvent une reponse pertinente, donc 90%.

---

## SLIDE 19 : Demonstration (2 minutes)

> "Je vais maintenant vous montrer le systeme en action.
> 
> Premier test, une question simple : 'Comment installer AI_licia'. Le systeme devrait retourner la procedure d'installation avec une confiance elevee.
> 
> Deuxieme test, comprehension semantique : 'Mon PC rame quand je stream'. Ici, le Self-Attention doit comprendre que 'rame' dans le contexte de 'PC' signifie 'lent', pas une pagaie de bateau.
> 
> Troisieme test, question hors-sujet pour montrer que le score de confiance detecte les questions non pertinentes."

---

## SLIDE 20 : Succes & Apprentissages (30 secondes)

> "Voici le bilan du projet.
> 
> **Côté succès** : le système atteint 90% de Hit Rate sur mes tests, ce qui dépasse l'objectif de 85%. La quantization Q4 s'est révélée viable pour le RAG. L'architecture hybride avec edge computing est scalable. Et le déploiement Docker est stable en production.
> 
> **Côté défis résolus** : j'ai dû gérer le calcul d'embedding côté client ou serveur selon le contexte. L'optimisation Docker a nécessité plusieurs itérations. Et le prompt engineering du LLM a demandé beaucoup d'ajustements pour obtenir des réponses cohérentes.
> 
> Ce projet m'a permis d'approfondir les fondamentaux du Machine Learning appliqué au NLP : Self-Attention, embeddings, similarité vectorielle, quantization, et déploiement production."

---

## SLIDE 21 : Conclusion (30 secondes)

> "En conclusion, Mila-Assist démontre qu'un RAG francophone performant peut être déployé localement sans API cloud.
> 
> Le système combine CamemBERT pour les embeddings contextuels, FAISS pour la recherche vectorielle et un LLM quantifié Q4 pour la génération.
> 
> L'architecture edge computing avec 4 containers Docker garantit la scalabilité et la maintenabilité.
> 
> 
> 
> Merci pour votre attention. Je suis disponible pour vos questions."

---

## SLIDE 22 : Questions

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

"Pourquoi GGUF et pas un autre format ?"
  "GGUF remplace l'ancien format GGML avec de meilleures performances. Il supporte plusieurs niveaux de quantification : Q4, Q5, Q8, selon le compromis qualite/taille. J'utilise Q4 pour maximiser la reduction memoire."

  "GGUF c'est CPU only ?"
  "Non, GGUF fonctionne sur CPU ET GPU. Avec une carte NVIDIA, llama.cpp utilise CUDA pour accelerer l'inference tout en gardant les avantages de la quantification."

---

# TIMING RECOMMANDE

| Slide                           | Duree  | Cumule      |
| ------------------------------- | ------ | ----------- |
| 1. Titre                        | 30s    | 0:30        |
| 2. Contexte                     | 1min   | 1:30        |
| 3. Pipeline RAG                 | 1min30 | 3:00        |
| 4. Indexation/Chunking          | 2min   | 5:00        |
| 5. Tokenisation                 | 2min   | 7:00        |
| 6. Embedding CamemBERT          | 1min30 | 8:30        |
| 7. Self-Attention               | 1min30 | 10:00       |
| 8. Alternatives                 | 1min   | 11:00       |
| 9. FAISS                        | 1min30 | 12:30       |
| 10. Similarite Cosinus          | 1min   | 13:30       |
| 11. SLM Gemma                   | 1min30 | 15:00       |
| 12. Quantization GGUF           | 1min30 | 16:30       |
| 13. Prompt Systeme 1/2          | 30s    | 17:00       |
| 14. Prompt Systeme 2/2 + Params | 30s    | 17:30       |
| 15. Fenetre Contexte            | 1min   | 18:30       |
| 16. Architecture                | 30s    | 19:00       |
| 17. Metriques                   | 2min   | 21:00       |
| 18. Hit Rate vs Precision       | 1min   | 22:00       |
| 19. Demo                        | 2min   | 24:00       |
| 20. Succes                      | 30s    | 24:30       |
| 21. Conclusion                  | 30s    | 25:00       |
| 22. Questions                   | -      | -           |
| **Total**                       |        | **~20 min** |

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
