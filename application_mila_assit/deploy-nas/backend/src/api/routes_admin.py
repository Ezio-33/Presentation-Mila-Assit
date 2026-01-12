"""
Routes API pour les fonctions d'administration.
Version Finale : Design Premium + Score de Confiance Réel + Fix Import Circulaire.
Refactoring : Utilisation de templates Jinja2 pour une meilleure séparation des responsabilités.
"""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from src.base_donnees.connexion import obtenir_curseur
from src.utilitaires.config import obtenir_config
from src.utilitaires.logger import obtenir_logger
import time
import asyncio
import httpx
from collections import defaultdict

# Logger
logger = obtenir_logger(__name__)
settings = obtenir_config()
router = APIRouter()

# Configuration des templates Jinja2
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# --- FONCTIONS UTILITAIRES (GÉNÉRATION HTML PREMIUM) ---

def generer_html_rapport(request: Request, metriques, resultats, interpretation_text, interpretation_class, gain_text):
    """Génère le rapport HTML en utilisant le template Jinja2."""

    # Construction des lignes du tableau
    lignes_tableau = ""
    for r in resultats[:50]:  # Top 50 pour l'affichage
        succes = r['hit_rate'] > 0

        # Icone et Style selon le succès
        if succes:
            status_icon = '<span style="color:#10b981; font-weight:bold; font-size:1.1em;">✅ TROUVÉ</span>'
            row_style = "background-color: #f0fdf4;"
        else:
            status_icon = '<span style="color:#ef4444; font-weight:bold; font-size:1.1em;">❌ ÉCHEC</span>'
            row_style = "background-color: #fef2f2;"

        # Score de confiance
        score_confiance = r['score_confiance']
        if score_confiance >= 0.80:
            score_style = "color:#059669; font-weight:bold;"
        elif score_confiance >= 0.70:
            score_style = "color:#d97706; font-weight:bold;"
        else:
            score_style = "color:#dc2626;"

        # Temps de réponse
        time_color = "#059669" if r['temps_ms'] < 1000 else "#d97706" if r['temps_ms'] < 2000 else "#dc2626"

        lignes_tableau += f"""
        <tr style="{row_style} transition: transform 0.2s;">
            <td style="padding: 16px; font-family:monospace; color:#6b7280; border-bottom: 1px solid #e5e7eb;"><strong>{r['id']}</strong></td>
            <td style="padding: 16px; font-weight:500; color:#1f2937; border-bottom: 1px solid #e5e7eb;">{r['question']}</td>
            <td style="padding: 16px; text-align:center; border-bottom: 1px solid #e5e7eb;">{status_icon}</td>
            <td style="padding: 16px; text-align:center; {score_style} border-bottom: 1px solid #e5e7eb;">{score_confiance:.1%}</td>
            <td style="padding: 16px; text-align:right; font-family:monospace; font-weight:bold; color:{time_color}; border-bottom: 1px solid #e5e7eb;">
                {r['temps_ms']} ms
            </td>
        </tr>
        """

    # Construction de la section des échecs
    echecs = [r for r in resultats if r['hit_rate'] == 0][:10]
    section_echecs = ""
    if echecs:
        for r in echecs:
            section_echecs += f"""
                    <div style="background: #fef2f2; padding: 12px 16px; border-left: 4px solid #ef4444; margin-bottom: 10px; border-radius: 6px;">
                        <strong style="color: #dc2626;">Q{r['id']}:</strong> {r['question']}
                        <span style="color: #6b7280; font-size: 0.85rem; margin-left: 10px;">(Confiance: {r['score_confiance']:.1%})</span>
                    </div>"""
    else:
        section_echecs = '<p style="color: #059669; font-weight: 500;">✅ Aucun échec détecté ! Toutes les questions ont obtenu une réponse pertinente.</p>'

    # Couleurs dynamiques pour le header
    colors = {
        "excellent": ("#10b981", "#059669"),
        "good":      ("#3b82f6", "#2563eb"),
        "medium":    ("#f59e0b", "#d97706"),
        "poor":      ("#ef4444", "#b91c1c")
    }
    c1, c2 = colors.get(interpretation_class, colors["medium"])

    # Générer les recommandations automatiques
    recommandations = []
    if metriques['hit_rate'] < 0.75:
        recommandations.append("📌 Améliorer la base de connaissances : ajouter plus de variantes de questions")
    if metriques['moyenne_confiance'] < 0.70:
        recommandations.append("📌 Optimiser les embeddings : considérer un modèle plus performant")
    if metriques['temps_p95_ms'] > 2000:
        recommandations.append("📌 Optimiser les performances : ajouter du caching ou augmenter les ressources")
    if metriques['confiance_faible'] > 0.30:
        recommandations.append("📌 Plus de 30% des réponses ont une confiance faible : réviser le système de scoring")
    if metriques['mrr'] < 0.80:
        recommandations.append("📌 Le rang moyen des résultats pertinents est trop bas : améliorer le ranking")

    if not recommandations:
        recommandations.append("✅ Le système performe excellemment ! Maintenir la qualité actuelle.")

    recommandations_html = "".join([f'<li style="margin-bottom: 10px; color: #1f2937; line-height: 1.6;">{r}</li>' for r in recommandations])

    # Benchmarks académiques
    benchmarks = {
        "MS MARCO (Industrie)": {"hit_rate": 0.85, "mrr": 0.75},
        "SQuAD (Académique)": {"hit_rate": 0.88, "mrr": 0.82},
        "Notre système": {"hit_rate": metriques['hit_rate'], "mrr": metriques['mrr']}
    }

    # Préparer les données pour Chart.js
    chart_labels = list(benchmarks.keys())
    chart_hit_rates = [v['hit_rate'] * 100 for v in benchmarks.values()]
    chart_mrrs = [v['mrr'] * 100 for v in benchmarks.values()]

    # Rendu du template
    return templates.TemplateResponse(
        "rapport_evaluation.html",
        {
            "request": request,
            "metriques": metriques,
            "resultats": resultats,
            "lignes_tableau": lignes_tableau,
            "section_echecs": section_echecs,
            "recommandations_html": recommandations_html,
            "interpretation_text": interpretation_text,
            "interpretation_class": interpretation_class,
            "gain_text": gain_text,
            "color1": c1,
            "color2": c2,
            "chart_labels": chart_labels,
            "chart_hit_rates": chart_hit_rates,
            "chart_mrrs": chart_mrrs,
            "timestamp": time.strftime('%d/%m/%Y à %H:%M:%S')
        }
    )



@router.post("/faiss/rebuild")
async def rebuild_faiss_index(request: Request):
    """Déclenche un rebuild asynchrone."""
    # IMPORT ICI pour éviter les cycles
    from src.clients.llm_client import obtenir_llm_client

    try:
        logger.info("🔨 Demande rebuild FAISS...")
        start_time = time.time()
        
        llm_client = obtenir_llm_client()
        resultat = await asyncio.to_thread(llm_client.forcer_rebuild_faiss)

        elapsed = time.time() - start_time
        return {
            "success": True,
            "message": "Rebuild terminé",
            "data": resultat,
            "duree": round(elapsed, 2)
        }
    except Exception as e:
        logger.error(f"Erreur rebuild: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/evaluation/export")
async def exporter_resultats_evaluation(
    request: Request,
    k: int = 5,
    sample: int = 20,
    delai_entre_requetes: float = 0.5,
    format_export: str = "json"
):
    """Endpoint pour exporter les résultats en JSON ou CSV."""
    try:
        from io import StringIO
        import csv
        import json as json_module
        from fastapi.responses import Response

        logger.info(f"[EXPORT] Format: {format_export}, sample: {sample}")

        # Appel interne à l'évaluation en mode JSON
        result = await evaluer_systeme_rag(request, format="json", k=k, sample=sample, delai_entre_requetes=delai_entre_requetes)

        # Extraire les données JSON
        if isinstance(result, JSONResponse):
            json_data = json_module.loads(result.body.decode())
        else:
            json_data = result

        if format_export == "csv":
            # Conversion en CSV
            output = StringIO()
            details = json_data.get('details', [])

            if details:
                # En-têtes CSV
                fieldnames = ['id', 'question', 'hit_rate', 'precision', 'mrr', 'score_confiance', 'temps_ms']
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(details)

                return Response(
                    content=output.getvalue(),
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename=evaluation_rag_{time.strftime('%Y%m%d_%H%M%S')}.csv"
                    }
                )
            else:
                raise HTTPException(500, "Aucune donnée à exporter")

        # Format JSON par défaut
        return Response(
            content=json_module.dumps(json_data, indent=2, ensure_ascii=False),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=evaluation_rag_{time.strftime('%Y%m%d_%H%M%S')}.json"
            }
        )

    except Exception as e:
        logger.error(f"[EXPORT ERROR] {e}")
        raise HTTPException(500, f"Erreur export: {e}")


@router.get("/evaluation", response_class=HTMLResponse)
async def evaluer_systeme_rag(
    request: Request,
    format: str = "html",
    k: int = 5,
    sample: int = 20,
    delai_entre_requetes: float = 0.5
):
    try:
        logger.info(f"[EVAL] Démarrage (k={k}, sample={sample})")
        start_time = time.time()

        # 1. DB 
        with obtenir_curseur() as (conn, cursor):
            cursor.execute("SELECT id, etiquette, question FROM base_connaissances ORDER BY id")
            questions = cursor.fetchall()

        if not questions:
            raise HTTPException(500, "Aucune question en base")

        # 2. Préparation Ground Truth
        ground_truths = {q['id']: [x['id'] for x in questions if x['etiquette'] == q['etiquette']] for q in questions}
        
        if 0 < sample < len(questions):
            step = max(1, len(questions) // sample)
            echantillon = questions[::step][:sample]
        else:
            echantillon = questions

        # 3. Boucle d'évaluation ASYNCHRONE
        resultats = []
        temps_total_api = 0
        api_url = "http://localhost:8000/api/v1/search"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, q in enumerate(echantillon, 1):
                
                if i > 1:
                    await asyncio.sleep(delai_entre_requetes)

                try:
                    t_start = time.time()
                    
                    payload = {
                        "question": q['question'], 
                        "id_session": f"eval-{int(t_start)}"
                    }
                    
                    response = await client.post(api_url, json=payload)
                    t_elapsed = int((time.time() - t_start) * 1000)
                    temps_total_api += t_elapsed

                    predictions = []
                    score_confiance = 0.0 
                    
                    if response.status_code == 200:
                        data = response.json()
                        predictions = data.get('sources', [])
                        # On récupère le vrai score de similarité
                        score_confiance = data.get('confiance', 0.0) 
                    
                    # --- CALCUL DES MÉTRIQUES ---
                    ground_truth = ground_truths[q['id']]
                    predictions_k = predictions[:k]
                    pertinents = len(set(predictions_k) & set(ground_truth))

                    # Hit Rate (Succès)
                    hit_rate = 1.0 if pertinents > 0 else 0.0

                    # Précision (pour info)
                    precision = pertinents / k if k > 0 else 0

                    # MRR (Mean Reciprocal Rank) - position du 1er résultat pertinent
                    mrr = 0.0
                    for rank, pred_id in enumerate(predictions_k, start=1):
                        if pred_id in ground_truth:
                            mrr = 1.0 / rank
                            break

                    resultats.append({
                        'id': q['id'],
                        'question': q['question'],
                        'predictions': predictions_k,
                        'temps_ms': t_elapsed,
                        'precision': precision,
                        'hit_rate': hit_rate,
                        'mrr': mrr,
                        'score_confiance': score_confiance
                    })

                except Exception as e:
                    logger.error(f"Erreur question {q['id']}: {e}")
                    continue

        # 4. Agrégation
        if not resultats:
             raise HTTPException(500, "L'évaluation n'a produit aucun résultat")

        # Moyennes
        hit_rate_avg = sum(r['hit_rate'] for r in resultats) / len(resultats)
        confiance_avg = sum(r['score_confiance'] for r in resultats) / len(resultats)
        precision_avg = sum(r['precision'] for r in resultats) / len(resultats)
        mrr_avg = sum(r['mrr'] for r in resultats) / len(resultats)

        temps_moyen = temps_total_api / len(resultats)
        duree_totale = time.time() - start_time

        # Calcul des percentiles de latence
        temps_list = sorted([r['temps_ms'] for r in resultats])
        n = len(temps_list)

        metriques = {
            'precision@k': precision_avg,
            'hit_rate': hit_rate_avg,
            'mrr': mrr_avg,
            'moyenne_confiance': confiance_avg,
            'k': k,
            'nb_questions_testees': len(resultats),
            'temps_moyen_ms': temps_moyen,
            'temps_p50_ms': temps_list[n//2],
            'temps_p95_ms': temps_list[int(n*0.95)] if n > 1 else temps_list[0],
            'temps_p99_ms': temps_list[int(n*0.99)] if n > 1 else temps_list[0],
            'temps_total_s': duree_totale,
            # Distribution de confiance
            'confiance_haute': sum(1 for r in resultats if r['score_confiance'] >= 0.8) / len(resultats),
            'confiance_moyenne': sum(1 for r in resultats if 0.65 <= r['score_confiance'] < 0.8) / len(resultats),
            'confiance_faible': sum(1 for r in resultats if r['score_confiance'] < 0.65) / len(resultats),
        }

        # 5. Retour JSON
        if format == "json":
            return JSONResponse({
                'success': True,
                'metriques': metriques,
                'details': resultats[:20]
            })

        # 6. Interprétation pour le Jury
        if hit_rate_avg >= 0.90:
            txt = "🚀 <strong>Système Excellent !</strong><br>L'IA trouve la bonne information dans plus de 90% des cas. Le système est prêt pour la production."
            cls = "excellent"
        elif hit_rate_avg >= 0.75:
            txt = "✅ <strong>Très Bon Système.</strong><br>La grande majorité des questions obtiennent une réponse pertinente."
            cls = "good"
        elif hit_rate_avg >= 0.50:
            txt = "⚠️ <strong>Système Correct.</strong><br>Le système fonctionne mais pourrait être optimisé."
            cls = "medium"
        else:
            txt = "❌ <strong>Performance Insuffisante.</strong><br>Le système a du mal à retrouver les informations."
            cls = "poor"
            
        temps_rep_moy = ""
        if hit_rate_avg > 0.5:
            temps_rep_moy = f"<p style='color:#059669; font-weight:bold; margin-top:15px; font-size:0.95rem; border-top:1px solid #eee; padding-top:10px;'>📈Temps de reponse moyen: (~{temps_moyen:.0f}ms).</p>"

        return generer_html_rapport(request, metriques, resultats, txt, cls, temps_rep_moy)

    except Exception as e:
        logger.error(f"[CRASH EVAL] {e}", exc_info=True)
        raise HTTPException(500, f"Erreur critique evaluation: {e}")