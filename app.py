from flask import Flask, render_template, request, redirect,session
import pandas as pd
import csv
from fonction_surprise import adresse_hotel,generate_recommendation,predict_review,création_fit_model,refit,find_comm
from textblob import TextBlob

app = Flask(__name__, template_folder='templates')
app.secret_key = '1234'

df = pd.read_csv("surprise.csv")
df2 = pd.read_csv("blob.csv")
df3 = pd.read_csv("df_commentaire.csv")
dico_user_id = {}
dico_id_user = {}
compteur = 0

column = list(df2.columns)
column.pop(0)

for user in column:
    compteur += 1
    dico_user_id[user] = compteur
    dico_id_user[compteur] = user

liste_hotel = list(df2["Unnamed: 0"].values)
dico_hotel_id = {}
dico_id_hotel = {}
compteur = 0
for hotel in liste_hotel:
    compteur += 1
    dico_id_hotel[compteur] = hotel
    dico_hotel_id[hotel] = compteur


svdpp=création_fit_model(df)
newdf=pd.DataFrame()

def User_login(user):
    with open('df_commentaire.csv', 'r', newline='',encoding='utf-8') as fichier_csv:
        reader = csv.reader(fichier_csv)
        premiere_ligne = next(reader)
        if user in premiere_ligne:
            return True
        else:
            return False


def obtenir_hotels_commentes(utilisateur, df=df3):
    numero_colonne = None
    hotels_commentes = []

    colone = df[utilisateur].values
    for x in range(len(liste_hotel)):
        comm = str(colone[x])
        if comm != "nan":
            hotels_commentes.append(dico_id_hotel[x+1])

    # with open('df_commentaire.csv', 'r', newline='') as fichier_csv:
    #     reader = csv.reader(fichier_csv)
    #     premiere_ligne = next(reader)  # Lire la première ligne du fichier CSV

    # if utilisateur in premiere_ligne:
    #     numero_colonne = premiere_ligne.index(utilisateur)  # Trouver le numéro de colonne pour l'utilisateur
    #
    # if numero_colonne is not None:
    #     for ligne in reader:
    #         if len(ligne) > numero_colonne:
    #             commentaire = ligne[numero_colonne].strip()
    #             if commentaire:  # Vérifier si le commentaire n'est pas vide
    #                 hotel = ligne[0]  # Récupérer le nom de l'hôtel dans la première colonne
    #                 hotels_commentes.append(hotel)

    return hotels_commentes


def obtenir_commentaires(utilisateur, df=df3):
    numero_colonne = None
    commentaires = {}
    commentaires2 = {}

    tab_comm = []
    colone = df[utilisateur].values
    for x in range(len(liste_hotel)):
        comm = str(colone[x])
        if comm != "nan":
            new_comm = ""
            compteur = 0
            for y in comm:
                if compteur == 0 and y==" ":
                    None
                else:
                    new_comm = new_comm + y
                compteur += 1
            print(dico_id_hotel[x+1])

            commentaires[dico_id_hotel[x + 1]] = str(new_comm).strip("\n")

    # with open('df_commentaire.csv', 'r', newline='', encoding="utf-8") as fichier_csv:
    #     reader = csv.reader(fichier_csv)
    #     premiere_ligne = next(reader)  # Lire la première ligne du fichier CSV
    #
    #     if utilisateur in premiere_ligne:
    #         numero_colonne = premiere_ligne.index(utilisateur)  # Trouver le numéro de colonne pour l'utilisateur
    #
    #     if numero_colonne is not None:
    #         for ligne in reader:
    #             if len(ligne) > numero_colonne:
    #                 commentaire = ligne[numero_colonne].strip()
    #                 if commentaire:  # Vérifier si le commentaire n'est pas vide
    #                     hotel = ligne[0]  # Récupérer le nom de l'hôtel dans la première colonne
    #                     commentaires2[hotel] = commentaire

    return commentaires

def obtenir_tous_les_hotels():
    hotels = []
    with open('df_commentaire.csv', 'r', newline='',encoding='utf-8') as fichier_csv:
        reader = csv.reader(fichier_csv)
        next(reader)
        for ligne in reader:
            hotel = ligne[0]
            hotels.append(hotel)

    return hotels

def obtenir_hotels_non_commentes(utilisateur):
    hotels_commentes = obtenir_hotels_commentes(utilisateur)  # Obtient les hôtels commentés par l'utilisateur
    hotels_tous = obtenir_tous_les_hotels()  # Obtient tous les hôtels disponibles
    hotels_non_commentes = [hotel for hotel in hotels_tous if hotel not in hotels_commentes]

    return hotels_non_commentes

def ajout_new_comm(nom_user, nom_hotel,comm,model=svdpp,df=df):
    id_user = dico_user_id[nom_user]
    id_hotel = dico_hotel_id[nom_hotel]
    ajout_df = pd.DataFrame(
        {"User_id": [id_user], "Hotel_id": [id_hotel], "Sentiment": [TextBlob(comm).sentiment.polarity]})
    df3.at[id_hotel-1,nom_user]=comm
    df= pd.concat([df,ajout_df])
    model=refit(df,model)
    return df,model





@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    if User_login(username):
        session['username']=username
        return redirect('/recommandation?username={}'.format(username))
    else:
        return redirect('/log_echec')


@app.route('/recommandation')
def page_log():
    username = session.get('username')
    hotels_commentes = obtenir_hotels_commentes(username)

    hotel_selectionne = request.args.get('hotel')
    commentaires = obtenir_commentaires(username)
    commentaire = commentaires.get(hotel_selectionne, "") if hotel_selectionne else ""
    recommendation=generate_recommendation(username,svdpp,df)
    dico_hotel_adresse=adresse_hotel()



    return render_template('recommandation.html', username=username, hotels_commentes=hotels_commentes,
                           commentaire=commentaire, commentaires=commentaires, hotel_selectionne=hotel_selectionne,recommendation=recommendation,dico_hotel_adresse=dico_hotel_adresse)


@app.route('/log_echec')
def page_echec():
    return render_template('log_echec.html')

@app.route('/ajout_commentaire_bdd',methods=['POST'])
def ajout():
    if request.method == 'POST' and 'submit'in request.form :
        hotel=request.form['hotel']
        commentaire=request.form['commentaire']
        utilisateur=session.get("username")
        newdf,newsvdpp=ajout_new_comm(str(utilisateur),str(hotel),str(commentaire))
        global df
        df=newdf
        global svdpp
        svdpp=newsvdpp
        return redirect("/recommandation")




@app.route('/ajouter-commentaire')
def page_new_comment():
    username =session.get('username')

    hotels_non_commentes = obtenir_hotels_non_commentes(username)
    return render_template('new_comment.html', hotels_non_commentes=hotels_non_commentes)

@app.route('/logout')
def logout():
    session["username"]=None
    return redirect("/")



if __name__ == '__main__':
     app.run(debug=True)
