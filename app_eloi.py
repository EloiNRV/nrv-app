import matplotlib
matplotlib.use('Agg')  # Non-interactive backend to prevent Tkinter issues

from flask import Flask, render_template, request, redirect, url_for, session, flash
import logging

# 🔹 Configuration du logging
logging.basicConfig(
    level=logging.INFO,  # Niveau de log : INFO (change en DEBUG pour plus de détails)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format des logs
    handlers=[
        logging.FileHandler("app.log"),  # Stocke les logs dans un fichier
        logging.StreamHandler()  # Affiche aussi les logs dans la console
    ]
)



from whitenoise import WhiteNoise
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

app = Flask(__name__)
app.secret_key = 'some_random_secret_key'  # Use a secure key for session management

# WhiteNoise setup: Wrap the Flask app to serve static files
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')
app.config['STATIC_FOLDER'] = 'static'

# Définition des valeurs par défaut pour toutes les variables utilisées dans le calcul
default_values = {
    'surface_batie': 0.0,
    'surface_dalle': 0.0,
    'surface_pleine_terre': 0.0,

    'T1_surface': 0.0,
    'T2_surface': 0.0,
    'T3_surface': 0.0,
    'T4_surface': 0.0,
    'T5_surface': 0.0,

    'num_T1': 0,  # Nombre de T1
    'num_T2': 0,  # Nombre de T2
    'num_T3': 0,  # Nombre de T3
    'num_T4': 0,  # Nombre de T4
    'num_T5': 0,  # Nombre de T5

    # Variables générales
    'Cc': 0.0,  # Coût de construction
    'Ti': 0.0,  # Taux d'intérêt initial
    'Tib': 0.0,  # Réduction du taux d'intérêt
    'Tiv': 0.0,  # Taux d'intérêt avec végétalisation
    'Ps': 0.0,  # Subventions

    # Durée moyenne d'occupation par type de logement (en années)
    'T2_duration': 2,
    'T3_duration': 5,
    'T4_duration': 10,
    'T5_duration': 15,


    # Coûts des différentes végétalisations
    'Pfv': 0.0,  # Coût de végétalisation des façades
    'Ptv': 0.0,  # Coût de végétalisation des toitures

    # Coûts d’entretien des végétalisations
    'Pe': 0.0,   # Prix d’entretien des façades végétalisées
    'Pe1': 0.0,  # Prix d’entretien des toitures végétalisées

    # Nouvelles variables liées aux questions
    'Pae': 0.0,  # Coût de l'arrivée d'eau
    'Pc': 0.0,   # Coût du compost
    'PrEP': 0.0,  # Coût de la récupération d’eau pluviale
    'PrEU': 0.0,  # Coût de la récupération d’eau usée

    # Scores des critères environnementaux (Radar)
    'Biodiversité': 0.0,
    'Énergie': 0.0,
    'CO2': 0.0,
    'Eau': 0.0,
    'Confort': 0.0,
    'Risques': 0.0,

    # Scores spécifiques aux végétalisations
    'ScoreFv': 0.0,  # Score pour la végétalisation des façades
    'ScoreTv': 0.0,  # Score pour la végétalisation des toitures

    # Coefficients pour les calculs du radar
    'CoefFv': 0.0,  # Coefficient pour la végétalisation des façades
    'CoefTv': 0.0,  # Coefficient pour la végétalisation des toitures

    # Scores des risques spécifiques
    'RisquesFv': 0.0,  # Score des risques pour façades végétalisées
    'RisquesTv': 0.0,  # Score des risques pour toitures végétalisées

    # CBS - Coefficient de Biotope par Surface
    'CBS': 0.0
}

responses = {}

def initialize_session():
    for key, value in default_values.items():
        # Vérifie si la variable est absente ou mal initialisée
        if key not in session or session[key] is None:
            session[key] = value








@app.route('/')
def index():
    initialize_session()  # Initialize all values before starting the questions
    return render_template('index.html')


@app.route('/question1', methods=['GET', 'POST'])
def question1():
    if request.method == 'POST':
        try:
            session['surface_batie'] = float(request.form['surface_batie'])
            session['surface_dalle'] = float(request.form['surface_dalle'])
            session['surface_pleine_terre'] = float(request.form['surface_pleine_terre'])

            if session['surface_batie'] < 0 or session['surface_dalle'] < 0 or session['surface_pleine_terre'] < 0:
                flash("Les surfaces ne peuvent pas être négatives.", "error")
                return redirect(url_for('question1'))

        except ValueError:
            flash("Veuillez entrer des valeurs numériques valides pour les surfaces.", "error")
            return redirect(url_for('question1'))

        return redirect(url_for('question2'))  # Redirection vers la prochaine question

    return render_template('question1.html')

@app.route('/question2', methods=['GET', 'POST'])
def question2():
    if request.method == 'POST':
        try:
            session['T1_surface'] = float(request.form['T1_surface'])
            session['T2_surface'] = float(request.form['T2_surface'])
            session['T3_surface'] = float(request.form['T3_surface'])
            session['T4_surface'] = float(request.form['T4_surface'])
            session['T5_surface'] = float(request.form['T5_surface'])

            if any(s <= 0 for s in [session['T1_surface'], session['T2_surface'], session['T3_surface'], session['T4_surface'], session['T5_surface']]):
                flash("Veuillez entrer des surfaces valides (positives) pour tous les types de logements.", "error")
                return redirect(url_for('question2'))

        except ValueError:
            flash("Veuillez entrer uniquement des valeurs numériques.", "error")
            return redirect(url_for('question2'))

        return redirect(url_for('question3'))  # Redirection vers la question suivante

    return render_template('question2.html')


@app.route('/question3', methods=['GET', 'POST'])
def question3():
    if request.method == 'POST':
        try:
            # Récupération et conversion des données
            session['num_T1'] = int(request.form['num_T1'])
            session['num_T2'] = int(request.form['num_T2'])
            session['num_T3'] = int(request.form['num_T3'])
            session['num_T4'] = int(request.form['num_T4'])
            session['num_T5'] = int(request.form['num_T5'])

            # Vérification que les valeurs sont positives ou nulles
            if any(n < 0 for n in [session['num_T1'], session['num_T2'], session['num_T3'], session['num_T4'], session['num_T5']]):
                flash("Le nombre de logements ne peut pas être négatif.", "error")
                return redirect(url_for('question3'))

        except ValueError:
            flash("Veuillez entrer un nombre valide pour chaque type de logement.", "error")
            return redirect(url_for('question3'))

        return redirect(url_for('question4'))  # Passer à la question suivante

    return render_template('question3.html')



@app.route('/question4', methods=['GET', 'POST'])
def question4():
    if request.method == 'POST':
        try:
            session['Cc'] = float(request.form['Cc'])
            if session['Cc'] <= 0:
                raise ValueError
        except ValueError:
            flash("Veuillez entrer un coût de construction valide.", "error")
            return redirect(url_for('question4'))
        
        

        return redirect(url_for('question5'))  # Redirection vers la question suivante

    return render_template('question4.html', Cc=session.get('Cc', 0))

@app.route('/question5', methods=['GET', 'POST'])
def question5():
    if request.method == 'POST':
        try:
            taux_interet = request.form['Ti'].replace(",", ".")  # Gère les virgules
            taux_interet = float(taux_interet)

            # Vérifie que le taux d'intérêt est bien entre 0 et 10 %
            if 0 <= taux_interet <= 10:
                session['Ti'] = taux_interet
            else:
                flash("Le taux d'intérêt doit être compris entre 0 et 10 %.", "error")
                return redirect(url_for('question5'))
        except ValueError:
            flash("Veuillez entrer un taux d'intérêt valide.", "error")
            return redirect(url_for('question5'))

        return redirect(url_for('question6'))  # Passe à la question suivante

    return render_template('question5.html')


@app.route('/question6', methods=['GET', 'POST'])
def question6():
    
    if request.method == 'POST':
        
        try:
            Tib = float(request.form['Tib'])  # Récupérer l'entrée utilisateur
            Ti = session.get('Ti', 0.0)  # Récupérer le taux d'intérêt initial

            # Vérification : Tib doit être positif et ≤ Ti
            if not (0 <= Tib <= Ti):
                raise ValueError("Le taux bonifié doit être inférieur ou égal au taux standard.")

            # Calcul du nouveau taux après végétalisation
            Tiv = Ti - Tib

            # Sauvegarde dans la session
            session['Tib'] = Tib
            session['Tiv'] = Tiv  # Stocke le taux après végétalisation
            
            return redirect(url_for('question7'))  # Passer à la question suivante

        except ValueError as e:
            flash(f"Erreur : {e}", "error")

    return render_template('question6.html', Ti=session.get('Ti', 0.0))

@app.route('/question7', methods=['GET', 'POST'])
def question7():
    if request.method == 'POST':
        try:
            # Récupérer la valeur proprement
            entered_value = request.form['Ps']

            # Vérifier si l'entrée est un nombre valide
            session['Ps'] = float(entered_value)  # Convertir et stocker

            return redirect(url_for('question8'))  # Passer à la question suivante

        except ValueError:
            flash("Veuillez entrer un montant valide en chiffres (ex: 10 000).", "error")

    return render_template('question7.html')


@app.route('/question8', methods=['GET', 'POST'])
def question8():
    if request.method == 'POST':
        try:
            # Récupérer la durée sélectionnée (ex: "10 ans" -> 10)
            session['T2_duration'] = int(request.form['T2_duration'].split()[0])
            session['T3_duration'] = int(request.form['T3_duration'].split()[0])
            session['T4_duration'] = int(request.form['T4_duration'].split()[0])
            session['T5_duration'] = int(request.form['T5_duration'].split()[0])

            return redirect(url_for('question9'))  # Rediriger vers la question suivante

        except ValueError:
            flash("Veuillez sélectionner une durée pour chaque type de logement.", "error")

    return render_template('question8.html')




@app.route('/question9', methods=['GET', 'POST'])
def question9():
    if request.method == 'POST':
        try:
            # 🔹 1. Récupérer les valeurs saisies
            T2_additional = float(request.form['T2_additional'])
            T3_additional = float(request.form['T3_additional'])
            T4_additional = float(request.form['T4_additional'])
            T5_additional = float(request.form['T5_additional'])

            # 🔹 2. Vérification des valeurs (0 à 10 ans)
            if not (0 <= T2_additional <= 10):
                raise ValueError("T2")
            if not (0 <= T3_additional <= 10):
                raise ValueError("T3")
            if not (0 <= T4_additional <= 10):
                raise ValueError("T4")
            if not (0 <= T5_additional <= 10):
                raise ValueError("T5")

            # 🔹 3. Sauvegarde des valeurs dans la session
            session['T2_additional'] = T2_additional
            session['T3_additional'] = T3_additional
            session['T4_additional'] = T4_additional
            session['T5_additional'] = T5_additional

            session['T2_duration_total'] = session['T2_duration'] + T2_additional
            session['T3_duration_total'] = session['T3_duration'] + T3_additional
            session['T4_duration_total'] = session['T4_duration'] + T4_additional
            session['T5_duration_total'] = session['T5_duration'] + T5_additional

           

            # 🔹 6. Redirection vers la question suivante
            return redirect(url_for('question10'))

        except ValueError as e:
            field = str(e)
            flash(f"Veuillez entrer une durée valide (entre 0 et 10 ans) pour {field}.", "error")
            return redirect(url_for('question9'))

    return render_template('question9.html', 
                           T2_duration=session.get('T2_duration'),  # Valeur choisie par l'utilisateur
                           T3_duration=session.get('T3_duration'),
                           T4_duration=session.get('T4_duration'),
                           T5_duration=session.get('T5_duration'),
                           T2_additional=session.get('T2_additional', 0),
                           T3_additional=session.get('T3_additional', 0),
                           T4_additional=session.get('T4_additional', 0),
                           T5_additional=session.get('T5_additional', 0))



@app.route('/question10', methods=['GET', 'POST'])
def question10():
    if request.method == 'POST':
        try:
            # Récupération du choix de l'utilisateur
            rotation_cost = float(request.form['rotation_cost'])

            # Vérification de la validité de la valeur sélectionnée
            valid_choices = [100, 150, 200, 250, 300, 350, 400, 450, 500]
            if rotation_cost not in valid_choices:
                raise ValueError("Valeur non autorisée")

            # Enregistrement de la valeur dans la session
            session['rotation_cost'] = rotation_cost

            return redirect(url_for('question11'))  # Redirection vers la question suivante

        except ValueError as e:
            flash(f"Erreur : {e}", "error")  # Message d'erreur pour l'utilisateur
        except Exception as e:
            flash(f"Une erreur est survenue : {e}", "error")

    return render_template('question10.html', 
                           rotation_cost=session.get('rotation_cost', 150))


@app.route('/question11', methods=['GET', 'POST'])
def question11():
    if request.method == 'POST':
        try:
            

            # Vérifie si "Pas de façade végétale" est sélectionné
            no_facade_selected = 'no_facade_selected' in request.form
            session['no_facade_selected'] = no_facade_selected

            if no_facade_selected:
                session['surface_grimpantes_mur'] = 0
                session['surface_grimpantes_cables'] = 0
                session['nombre_jardiniere'] = 0
                session['cout_jardiniere'] = 0
                session['surface_hydroponie_substrat'] = 0
                session['surface_hydroponie_feutre'] = 0
            else:
                # 🔹 Assurer que les champs vides sont bien convertis en 0
                session['surface_grimpantes_mur'] = float(request.form.get('grimpantes_mur_surface', '0') or '0')
                session['surface_grimpantes_cables'] = float(request.form.get('grimpantes_cables_surface', '0') or '0')
                session['nombre_jardiniere'] = int(request.form.get('jardiniere_nombre', '0') or '0')
                session['cout_jardiniere'] = float(request.form.get('jardiniere_cout', '0') or '0')
                session['surface_hydroponie_substrat'] = float(request.form.get('hydroponie_substrat_surface', '0') or '0')
                session['surface_hydroponie_feutre'] = float(request.form.get('hydroponie_feutre_surface', '0') or '0')


            return redirect(url_for('question12'))  # Redirection vers la question suivante

        except ValueError as e:
            flash(f"Erreur : veuillez entrer une surface valide en m². Détail : {e}", "error")
            return redirect(url_for('question11'))

    return render_template('question11.html',
                           grimpantes_mur=session.get('surface_grimpantes_mur', 0),
                           grimpantes_cables=session.get('surface_grimpantes_cables', 0),
                           jardiniere_nombre=session.get('nombre_jardiniere', 0),
                           jardiniere_cout=session.get('cout_jardiniere', 0),
                           hydroponie_substrat=session.get('surface_hydroponie_substrat', 0),
                           hydroponie_feutre=session.get('surface_hydroponie_feutre', 0),
                           no_facade_selected=session.get('no_facade_selected', False))




@app.route('/question12', methods=['GET', 'POST'])
def question12():
    if request.method == 'POST':
        try:
           

            # Vérifie si "Pas de toiture végétale" est sélectionné
            no_toiture_selected = 'no_toiture_selected' in request.form
            session['no_toiture_selected'] = no_toiture_selected

            if no_toiture_selected:
                session['intensive_surface'] = 0
                session['semi_intensive_surface'] = 0
                session['extensive_surface'] = 0
            else:
                # 🔹 Vérifier que les champs vides sont bien convertis en 0
                session['intensive_surface'] = float(request.form.get('intensive_surface', '0') or '0')
                session['semi_intensive_surface'] = float(request.form.get('semi_intensive_surface', '0') or '0')
                session['extensive_surface'] = float(request.form.get('extensive_surface', '0') or '0')

            return redirect(url_for('question13'))  # Redirection vers la question suivante

        except ValueError as e:
            flash(f"Erreur : veuillez entrer une surface valide en m². Détail : {e}", "error")
            return redirect(url_for('question12'))

    return render_template('question12.html', 
                           intensive=session.get('intensive_surface', 0),
                           semi_intensive=session.get('semi_intensive_surface', 0),
                           extensive=session.get('extensive_surface', 0),
                           no_toiture_selected=session.get('no_toiture_selected', False))



@app.route('/question13', methods=['GET', 'POST'])
def question13():
    if request.method == 'POST':
        try:
            # Vérifier si l'utilisateur a choisi "oui"
            has_water_installation = request.form.get('water_installation') == "oui"

            if has_water_installation:
                # Récupération et conversion des valeurs
                cost_per_logement = float(request.form.get('cost_per_logement', 0) or 0)
                num_logements = int(request.form.get('num_logements_water', 0) or 0)
                total_pae = cost_per_logement * num_logements
                session['score_q13'] = 3  # Score attribué si installation d’arrivée d’eau
            else:
                total_pae = 0  # Si "non", le coût est 0
                session['score_q13'] = 0  # Score 0 si pas d’arrivée d’eau

            # Stocker dans Flask
            session['Pae'] = total_pae
            responses["q13"] = session['score_q13']  # Ajout du score dans responses

            # Debug : Vérifier si les valeurs sont bien stockées
           

            return redirect(url_for('question14'))  # Redirection vers la question suivante

        except ValueError:
            flash("Erreur : veuillez entrer une valeur numérique valide.", "error")
            return redirect(url_for('question13'))

    return render_template('question13.html', 
                           has_water_installation=session.get('Pae', 0) > 0,
                           cost_per_logement=session.get('Pae', 0),
                           num_logements_water=session.get('num_logements_water', 0),
                           Pae=session.get('Pae', 0))



@app.route('/question14', methods=['GET', 'POST'])
def question14():
    if request.method == 'POST':
        try:
            # Vérifier si "Oui" a été sélectionné
            has_composte = request.form.get('composte') == "oui"

            if has_composte:
                # Récupérer et stocker le prix du compost
                session['Pc'] = float(request.form.get('composte_price', 0) or 0)
                session['score_q14'] = 1  # Score de 1 si l'utilisateur ajoute un compost
            else:
                # Si "Non", on met Pc à 0
                session['Pc'] = 0  
                session['score_q14'] = 0  # Score de 0 si pas de compost

            # Mettre à jour le dictionnaire `responses`
            responses["q14"] = session['score_q14']

           

            return redirect(url_for('question15'))  # Redirection vers la question suivante

        except ValueError:
            flash("Erreur : veuillez entrer une valeur numérique valide.", "error")
            return redirect(url_for('question14'))

    return render_template('question14.html', 
                           has_composte=session.get('Pc', 0) > 0,
                           composte_price=session.get('Pc', 0),
                           score_q14=responses.get("q14", 0))  # Utilisation de responses



@app.route('/question15', methods=['GET', 'POST'])
def question15():
    if request.method == 'POST':
        try:
            # Vérifier si l'utilisateur a choisi "oui"
            has_rainwater_recovery = request.form.get('rainwater_recovery') == "oui"

            if has_rainwater_recovery:
                # Récupération et conversion des valeurs
                rainwater_cost = float(request.form.get('rainwater_cost', 0) or 0)
                session['PrEP'] = rainwater_cost
                session['score_q15'] = 3  # Score attribué si récupération d’eau pluviale
            else:
                session['PrEP'] = 0  # Si "non", le coût est 0
                session['score_q15'] = 0  # Score 0 si pas de récupération

            # Stocker le score dans responses
            responses["q15"] = session['score_q15']

            

            return redirect(url_for('question16'))  # Redirection vers la question suivante

        except ValueError:
            flash("Erreur : veuillez entrer une valeur numérique valide.", "error")
            return redirect(url_for('question15'))

    return render_template('question15.html', 
                           has_rainwater_recovery=session.get('PrEP', 0) > 0,
                           rainwater_cost=session.get('PrEP', 0))



@app.route('/question16', methods=['GET', 'POST'])
def question16():
    if request.method == 'POST':
        try:
            # Vérifier si l'utilisateur a choisi "oui"
            has_wastewater_recovery = request.form.get('wastewater_recovery') == "oui"

            if has_wastewater_recovery:
                # Récupération et conversion des valeurs
                wastewater_cost = float(request.form.get('wastewater_cost', 0) or 0)
                session['PrEU'] = wastewater_cost
                session['score_q16'] = 3  # Score attribué si récupération d’eau usée
            else:
                session['PrEU'] = 0  # Si "non", le coût est 0
                session['score_q16'] = 0  # Score 0 si pas de récupération

            # Stocker le score dans responses
            responses["q16"] = session['score_q16']

           

            return redirect(url_for('question17'))  # Redirection vers la question suivante

        except ValueError:
            flash("Erreur : veuillez entrer une valeur numérique valide.", "error")
            return redirect(url_for('question16'))

    return render_template('question16.html', 
                           has_wastewater_recovery=session.get('PrEU', 0) > 0,
                           wastewater_cost=session.get('PrEU', 0))



@app.route('/question17', methods=['GET', 'POST'])
def question17():
    if request.method == 'POST':
        try:
            # Récupérer la réponse sélectionnée
            selected_option = request.form.get('q17', "0%")  # Par défaut 0% si rien n'est sélectionné

            # Définition des scores associés aux réponses
            score_mapping = {
                "0%": 0,
                "25%": 2,
                "50%": 3,
                "75%": 4,
                "100%": 5
            }
            score = score_mapping.get(selected_option, 0)  # Score attribué

            # Stocker la réponse et le score dans la session
            session['q17'] = selected_option
            session['score_q17'] = score  # Stockage du score sous une variable uniforme
            responses["q17"] = session['score_q17']  # Stockage dans responses pour le radar

            

            return redirect(url_for('question18'))  # Redirection vers la question suivante

        except Exception as e:
            flash(f"Une erreur est survenue : {e}", "error")
            return redirect(url_for('question17'))

    return render_template('question17.html', 
                           selected_option=session.get('q17', "0%"),
                           score_q17=session.get('score_q17', 0))


@app.route('/question18', methods=['GET', 'POST'])
def question18():
    if request.method == 'POST':
        try:
            # Récupérer la réponse principale (Oui / Non)
            connectivite = request.form.get('connectivite', "Non")

            # Vérifier si "Oui" a été sélectionné
            if connectivite == "Oui":
                selected_option = request.form.get('connectivite_type', "Aucun")

                # Attribution du score selon la sélection
                score_connectivite = {
                    "Aucun": 0,
                    "Ilot": 2,
                    "Corridor": 3,
                    "Reserve": 5
                }.get(selected_option, 0)
            else:
                selected_option = "Aucun"
                score_connectivite = 1  # Si "Non", score par défaut

            # Stocker les valeurs en session
            session['connectivite'] = connectivite
            session['connectivite_type'] = selected_option
            session['score_q18'] = score_connectivite  # Stocker le score

            # Ajouter le score à `responses`
            responses["q18"] = session['score_q18']

          

            return redirect(url_for('question19'))  # Redirection vers la question suivante

        except Exception as e:
            flash(f"Erreur : {e}", "error")
            return redirect(url_for('question18'))

    return render_template('question18.html',
                           connectivite=session.get('connectivite', "Non"),
                           connectivite_type=session.get('connectivite_type', "Aucun"),
                           score_q18=session.get('score_q18', 1))



@app.route('/question19', methods=['GET', 'POST'])
def question19():
    if request.method == 'POST':
        try:
            # Récupérer la réponse sélectionnée
            entretien_frequence = request.form.get('entretien_frequence', "1 fois /an ou moins")

            # Dictionnaire des scores
            scores_entretien = {
                "plus d’1 fois /mois": 5,
                "1 fois /mois": 4,
                "4 fois /an": 2,
                "2 fois /an": 1,
                "1 fois /an ou moins": 0
            }

            # Attribution du score
            session['score_q19'] = scores_entretien.get(entretien_frequence, 0)

            # Stocker le score dans responses
            responses["q19"] = session['score_q19']

         

            return redirect(url_for('question20'))  # Redirection vers la question suivante

        except Exception as e:
            flash(f"Erreur : {e}", "error")
            return redirect(url_for('question19'))

    return render_template('question19.html',
                           entretien_frequence=session.get('entretien_frequence', "1 fois /an ou moins"),
                           score_q19=session.get('score_q19', 0))


@app.route('/question20', methods=['GET', 'POST'])
def question20():
    if request.method == 'POST':
        try:
            # Récupérer la réponse sélectionnée
            proportion_especes = request.form.get('proportion_especes', "0%")

            # Dictionnaire des scores
            scores_especes = {
                "0%": 0,
                "25%": 2,
                "50%": 3,
                "75%": 4,
                "100%": 5
            }

            # Attribution du score
            session['score_q20'] = scores_especes.get(proportion_especes, 0)

            # Stocker le score dans responses
            responses["q20"] = session['score_q20']


            return redirect(url_for('question21'))  # Redirection vers la question suivante

        except Exception as e:
            flash(f"Erreur : {e}", "error")
            return redirect(url_for('question20'))

    return render_template('question20.html',
                           proportion_especes=session.get('proportion_especes', "0%"),
                           score_q20=session.get('score_q20', 0))


@app.route('/question21', methods=['GET', 'POST'])
def question21():
    if request.method == 'POST':
        try:
            # Récupérer la réponse sélectionnée
            haies_percentage = request.form.get('haies_percentage', "0%")

            # Définition des scores en fonction de la réponse
            score_mapping = {"0%": 0, "25%": 2, "50%": 3, "75%": 4, "100%": 5}
            session['score_q21'] = score_mapping.get(haies_percentage, 0)  # Stocker le score

            # Stocker la réponse dans la session
            session['haies_percentage'] = haies_percentage

            # Ajouter dans responses pour cohérence avec les autres questions
            responses["q21"] = session['score_q21']


            return redirect(url_for('question22'))  # Redirection vers la question suivante

        except Exception as e:
            flash(f"Erreur : {e}", "error")
            return redirect(url_for('question21'))

    return render_template('question21.html',
                           haies_percentage=session.get('haies_percentage', "0%"),
                           score_q21=session.get('score_q21', 0))

@app.route('/question22', methods=['GET', 'POST'])
def question22():
    if request.method == 'POST':
        try:
            # Récupérer la réponse sélectionnée
            jardins_partages = request.form.get('jardins_partages', "Non")

            # Définition des scores en fonction de la réponse
            score_mapping = {"Non": 0, "Partiellement": 3, "Oui": 5}
            session['score_q22'] = score_mapping.get(jardins_partages, 0)  # Stocker le score

            # Stocker la réponse dans la session
            session['jardins_partages'] = jardins_partages

            # Ajouter dans responses pour cohérence avec les autres questions
            responses["q22"] = session['score_q22']


            return redirect(url_for('question23'))  # Redirection vers la question suivante

        except Exception as e:
            flash(f"Erreur : {e}", "error")
            return redirect(url_for('question22'))

    return render_template('question22.html',
                           jardins_partages=session.get('jardins_partages', "Non"),
                           score_q22=session.get('score_q22', 0))


@app.route('/question23', methods=['GET', 'POST'])
def question23():
    if request.method == 'POST':
        try:
            # Récupérer la réponse sélectionnée
            zone_humide = request.form.get('zone_humide', "0%")

            # Définition des scores en fonction de la réponse
            score_mapping = {"0%": 0, "25%": 2, "50%": 3, "75%": 4, "100%": 5}
            session['score_q23'] = score_mapping.get(zone_humide, 0)  # Stocker le score

            # Stocker la réponse dans la session
            session['zone_humide'] = zone_humide

            # Ajouter dans responses pour cohérence avec les autres questions
            responses["q23"] = session['score_q23']


            return redirect(url_for('question24'))  # Redirection vers la question suivante

        except Exception as e:
            flash(f"Erreur : {e}", "error")
            return redirect(url_for('question23'))

    return render_template('question23.html',
                           zone_humide=session.get('zone_humide', "0%"),
                           score_q23=session.get('score_q23', 0))


@app.route('/question24', methods=['GET', 'POST'])
def question24():
    if request.method == 'POST':
        try:
            # Récupération de la réponse
            valuation_input = request.form.get('valuation_percentage', "5%")

            # Vérification si l'utilisateur a sélectionné "Aucune idée"
            if valuation_input == "Aucune idée":
                session['valuation_percentage'] = 0.05  # Stocker 5% en tant que valeur réelle
            else:
                session['valuation_percentage'] = float(valuation_input.replace("%", "")) / 100


            # Stocker le score basé sur la valorisation
            session["score_q24"] = 5 if session['valuation_percentage'] > 0 else 0
            responses["q24"] = session["score_q24"]

            return redirect(url_for('results'))  # Redirection vers la page des résultats

        except ValueError:
            flash("Erreur : veuillez sélectionner une valeur valide.", "error")
            return redirect(url_for('question24'))

    return render_template('question24.html', valuation_percentage=session.get('valuation_percentage', "Aucune idée"))


def calculate_rotation_gain():
    try:
        # 🔹 Récupération des données de session
        cost_per_m2 = session.get('rotation_cost', 0)  # Coût de rotation par m²
        
        num_T2 = session.get('num_T2', 0)
        num_T3 = session.get('num_T3', 0)
        num_T4 = session.get('num_T4', 0)
        num_T5 = session.get('num_T5', 0)

        T2_surface = session.get('T2_surface', 0)
        T3_surface = session.get('T3_surface', 0)
        T4_surface = session.get('T4_surface', 0)
        T5_surface = session.get('T5_surface', 0)

        T2_duration = session.get('T2_duration_total', 2)  # Durée avec végétalisation
        T3_duration = session.get('T3_duration_total', 5)
        T4_duration = session.get('T4_duration_total', 10)
        T5_duration = session.get('T5_duration_total', 15)

        T2_duration_initial = session.get('T2_duration', 2)  # Durée initiale sans végétalisation
        T3_duration_initial = session.get('T3_duration', 5)
        T4_duration_initial = session.get('T4_duration', 10)
        T5_duration_initial = session.get('T5_duration', 15)

        # 🔹 Calcul des taux de rotation
        T2_rotation_rate_standard = 1 / T2_duration_initial
        T3_rotation_rate_standard = 1 / T3_duration_initial
        T4_rotation_rate_standard = 1 / T4_duration_initial
        T5_rotation_rate_standard = 1 / T5_duration_initial

        T2_rotation_rate_veget = 1 / T2_duration
        T3_rotation_rate_veget = 1 / T3_duration
        T4_rotation_rate_veget = 1 / T4_duration
        T5_rotation_rate_veget = 1 / T5_duration

        # 🔹 Calcul des coûts de rotation
        T2_cost_standard = num_T2 * T2_surface * cost_per_m2 * T2_rotation_rate_standard
        T3_cost_standard = num_T3 * T3_surface * cost_per_m2 * T3_rotation_rate_standard
        T4_cost_standard = num_T4 * T4_surface * cost_per_m2 * T4_rotation_rate_standard
        T5_cost_standard = num_T5 * T5_surface * cost_per_m2 * T5_rotation_rate_standard

        T2_cost_veget = num_T2 * T2_surface * cost_per_m2 * T2_rotation_rate_veget
        T3_cost_veget = num_T3 * T3_surface * cost_per_m2 * T3_rotation_rate_veget
        T4_cost_veget = num_T4 * T4_surface * cost_per_m2 * T4_rotation_rate_veget
        T5_cost_veget = num_T5 * T5_surface * cost_per_m2 * T5_rotation_rate_veget

        # 🔹 Calcul des économies
        T2_saving = T2_cost_standard - T2_cost_veget
        T3_saving = T3_cost_standard - T3_cost_veget
        T4_saving = T4_cost_standard - T4_cost_veget
        T5_saving = T5_cost_standard - T5_cost_veget

        total_saving_rota = T2_saving + T3_saving + T4_saving + T5_saving

        # 🔹 Stocker le résultat dans Flask
        session['rotation_savings'] = total_saving_rota

        # Debug dans la console Flask
        print(f"Économies liées à la rotation : {total_saving_rota:.2f} €")

        return total_saving_rota

    except Exception as e:
        print(f"Erreur lors du calcul des économies de rotation : {e}")
        return 0


def calculate_annual_interest_gain():
    try:
        # Données d'entrée depuis la session
        construction_cost = session.get('Cc', 0.0)  # Coût de construction
        standard_rate = session.get('Ti', 0.0) / 100  # Taux standard en décimal
        reduced_rate = session.get('Tiv', 0.0) / 100  # Taux réduit avec végétalisation en décimal
        loan_duration_years = 20  # Durée du prêt en années
        loan_duration_months = loan_duration_years * 12  # Converti en mois

        # Vérification des valeurs
        if construction_cost <= 0 or standard_rate <= 0 or reduced_rate <= 0:
            return 0  # Évite les erreurs mathématiques

        # Fonction pour calculer les mensualités
        def calculate_monthly_payment(principal, rate, months):
            monthly_rate = rate / 12  # Taux mensuel
            return (principal * monthly_rate * (1 + monthly_rate) ** months) / \
                   ((1 + monthly_rate) ** months - 1)

        # Mensualités avant et après végétalisation
        monthly_payment_standard = calculate_monthly_payment(construction_cost, standard_rate, loan_duration_months)
        monthly_payment_reduced = calculate_monthly_payment(construction_cost, reduced_rate, loan_duration_months)

        # Calcul du gain annuel
        gain_TI = (monthly_payment_standard - monthly_payment_reduced) * 12

        # Stockage dans la session pour utilisation en HTML
        session['gain_TI'] = gain_TI

        return gain_TI
    except Exception as e:
        print(f"Erreur lors du calcul du gain d'intérêt annuel : {e}")
        return 0


def calculate_totals_facade():
    try:
        # 🔹 Vérification des valeurs récupérées
        Sgm = float(session.get('surface_grimpantes_mur', 0))
        Sgc = float(session.get('surface_grimpantes_cables', 0))
        Nj = float(session.get('nombre_jardiniere', 0))
        Cj = float(session.get('cout_jardiniere', 0))
        ShS = float(session.get('surface_hydroponie_substrat', 0))
        ShF = float(session.get('surface_hydroponie_feutre', 0))


        # 🔹 Initialisation des coûts
        Pe = 0  # Coût total d'entretien annuel
        Pfv = 0  # Coût total de mise en place

        # 🔹 Calcul des coûts
        if Sgm > 0:
            PSgm = Sgm * 20  # Coût de pose : 20 €/m²
            Pe += 10 * Sgm  # Entretien : 10 €/m²/an
            Pfv += PSgm

        if Sgc > 0:
            PSgc = Sgc * 150  # Coût de pose : 150 €/m²
            Pe += 10 * Sgc  # Entretien : 10 €/m²/an
            Pfv += PSgc

        if Nj > 0 and Cj > 0:
            Pjc = Nj * Cj  # Coût des jardinières
            Pe += 40 * Nj  # Entretien : 40 €/unité/an
            Pfv += Pjc

        if ShS > 0:
            Phs = ShS * 750  # Coût de pose : 750 €/m²
            Pe += 45 * ShS  # Entretien : 45 €/m²/an
            Pfv += Phs

        if ShF > 0:
            Phf = ShF * 1000  # Coût de pose : 1000 €/m²
            Pe += 75 * ShF  # Entretien : 75 €/m²/an
            Pfv += Phf

    

        # 🔹 Stockage dans Flask session
        session['Pe'] = Pe
        session['Pfv'] = Pfv

        return Pfv, Pe

    except Exception as e:
        print(f"ERREUR dans calculate_totals_facade : {e}")
        return 0, 0

def calculate_totals_toiture():
    """ Calcule les coûts d'installation et d'entretien des toitures végétalisées. """
    try:
        # Initialisation des coûts
        Pe1 = 0  # Coût total d'entretien annuel
        Ptv = 0  # Coût total de mise en place

        # Récupération des surfaces depuis Flask session
        Sti = session.get('intensive_surface', 0)
        Stsi = session.get('semi_intensive_surface', 0)
        Ste = session.get('extensive_surface', 0)

        

        # Calcul des coûts d'installation et d'entretien
        Pti = Sti * 180  # Coût de pose : 180 €/m²
        Ptsi = Stsi * 150  # Coût de pose : 150 €/m²
        Pte = Ste * 70  # Coût de pose : 70 €/m²

        Pe1 += (10 * Sti) + (10 * Stsi) + (10 * Ste)  # Coût annuel d'entretien total
        Ptv += (Pti + Ptsi + Pte)  # Coût total d'installation

        # Stockage dans Flask session
        session['Pe1'] = Pe1
        session['Ptv'] = Ptv

    

        return Ptv, Pe1

    except Exception as e:
        print(f"Erreur lors du calcul des coûts des toitures : {e}")
        return 0, 0
    

import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from scipy.optimize import fsolve


def generate_roi_graph():
    plt.style.use('bmh')

    years = np.arange(21)  # Période de 0 à 20 ans

    # Coûts et gains récupérés depuis Flask (session)
    cost_setup = session.get('Pfv', 0) + session.get('Ptv', 0)
    cost_fixed = session.get('Pc', 0) + session.get('Pae', 0) + session.get('PrEP', 0) + session.get('PrEU', 0)
    cost_maintenance = session.get('Pe', 0) + session.get('Pe1', 0)
    gain_rotation = session.get('rotation_savings', 0)
    gain_interest = session.get('gain_TI', 0)
    gain_aid = session.get('Ps', 0)
    gain_valuation = session.get('Cc', 0) * session.get('valuation_percentage', 0)

    # Courbes de coûts et gains
    costs = cost_setup + cost_fixed + (cost_maintenance * years)
    gains = ((gain_rotation + gain_interest) * years) + gain_aid + np.where(years >= 3, gain_valuation, 0)

    # Définition de l'intersection
    def difference(x):
        return (cost_setup + cost_fixed + cost_maintenance * x) - ((gain_rotation + gain_interest) * x + gain_aid + (gain_valuation if x >= 3 else 0))

    x_guess = 10  # Hypothèse initiale
    intersection_year = fsolve(difference, x_guess)[0]

    # Création du graphique
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(years, costs, label="Coût total de la végétalisation", color="#C96049", linewidth=2)
    ax.plot(years, gains, label="Gains total apporté par la végétalisation", color="#2E8B57", linewidth=2)

    # Ajout du point d'intersection
    if intersection_year > 0 and intersection_year < 20:
        plt.axvline(x=intersection_year, color='black', linestyle='--', alpha=0.7)
        plt.scatter(intersection_year, (gain_rotation + gain_interest) * intersection_year + gain_aid, color='black', zorder=5)
        plt.text(intersection_year + 0.5, (gain_rotation + gain_interest) * intersection_year + gain_aid, f'{intersection_year:.1f} ans', color='black')

    # Ajout des titres et labels
    plt.xlabel("Temps (années)")
    plt.ylabel("Montant (€)")
    plt.title("Évolution des coûts et gains liés à la végétalisation")
    plt.xticks(range(0, 21, 2))
    plt.yticks(np.arange(0, max(max(costs), max(gains)), step=50000))
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)

    #  Sauvegarde en Base64 pour affichage dans Flask
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    return f"data:image/png;base64,{image_base64}"




@app.route('/results')
def results():
    try:
        # 🔹 Recalculer les coûts des façades et des toitures
        Pfv, Pe = calculate_totals_facade()
        Ptv, Pe1 = calculate_totals_toiture()

        # 🔹 Récupérer les valeurs stockées dans Flask session
        cost_setup = Pfv + Ptv  # Coût d'installation
        cost_fixed = session.get('Pc', 0) + session.get('Pae', 0) + session.get('PrEP', 0) + session.get('PrEU', 0)
        cost_maintenance = Pe + Pe1  # Coût d'entretien annuel

        # 🔹 Récupération des gains
        gain_rotation = calculate_rotation_gain()  # Appelle la fonction pour recalculer
        gain_interest = calculate_annual_interest_gain()  # Recalcule les gains d'intérêt
        gain_aid = session.get('Ps', 0)  # Subventions
        gain_valuation = session.get('Cc', 0) * session.get('valuation_percentage', 0)  # Gain en valeur immobilière

        # 🔹 Vérification et correction des données stockées
        session['Pfv'] = Pfv
        session['Ptv'] = Ptv
        session['Pe'] = Pe
        session['Pe1'] = Pe1
        session['rotation_savings'] = gain_rotation
        session['gain_TI'] = gain_interest

        # 🔹 Logs pour vérifier les valeurs
        app.logger.info("🔹 DEBUG - Vérification des coûts et gains :")
        app.logger.info(f"Pfv (Façades) = {Pfv} €, Ptv (Toitures) = {Ptv} €")
        app.logger.info(f"Pe (Entretien façades) = {Pe} €/an, Pe1 (Entretien toitures) = {Pe1} €/an")
        app.logger.info(f"Cost Setup = {cost_setup} €, Cost Fixed = {cost_fixed} €, Cost Maintenance = {cost_maintenance} €/an")
        app.logger.info(f"Gain Rotation = {gain_rotation} €, Gain Intérêt = {gain_interest} €")
        app.logger.info(f"Gain Subventions = {gain_aid} €, Gain Valorisation = {gain_valuation} €")

        # 🔹 Générer le graphique ROI
        roi_graph_url = generate_roi_graph()

        return render_template('results.html', roi_graph_url=roi_graph_url)

    except Exception as e:
        app.logger.error(f"Erreur lors du calcul des résultats : {e}")
        flash("Une erreur est survenue lors du calcul des résultats.", "error")
        return redirect(url_for('index'))







if __name__ == "__main__":
    app.run(debug=True)