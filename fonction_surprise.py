from surprise import SVDpp
from surprise import Reader
from surprise import Dataset
from surprise.model_selection.search import GridSearchCV
import pandas as pd
import random
from textblob import TextBlob
import csv
import numpy as np

reader = Reader(rating_scale=(-1, 1))
df = pd.read_csv("surprise.csv")
df2 = pd.read_csv("blob.csv")
df3=pd.read_csv("df_commentaire.csv")
df4=pd.read_csv('df_hotel.csv',delimiter=";",encoding='cp1252')
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


def création_fit_model(df):
    data = Dataset.load_from_df(df[["User_id", "Hotel_id", "Sentiment"]], reader)
    trainset = data.build_full_trainset()

    grid = {'n_epochs': [8, 9, 10, 11, 12, 13, 14, 15, 20],
            'lr_all': [.0025, .005, .0075, .001, .005, .01]}

    gs = GridSearchCV(SVDpp, grid, measures=['RMSE', 'MAE'], cv=9)
    gs.fit(data)
    param = gs.best_params['rmse']
    svdpp = SVDpp(verbose=True, n_epochs=param['n_epochs'], lr_all=param['lr_all'])
    svdpp.fit(trainset)
    return svdpp


def refit(df, model):
    new_data = Dataset.load_from_df(df[["User_id", "Hotel_id", "Sentiment"]], reader)
    new_trainset = new_data.build_full_trainset()
    model.fit(new_trainset)
    return model


def predict_review(user_id, hotel_id, model):
    review_prediction = model.predict(uid=user_id, iid=hotel_id)
    return review_prediction.est


def generate_recommendation(nom_user, model, metadata,thresh=0.33):  # generation des recommendation avec sauvegarde si score predi>0,45
    user_id = dico_user_id[nom_user]
    liste_recommended_hotel = []
    liste_rating=[]
    recommended_hotel=[]
    hotel_ids = list(set(metadata['Hotel_id'].values))
    random.shuffle(hotel_ids)

    for hotel_id in hotel_ids:
        rating = predict_review(user_id, hotel_id, model)  # prédit une note de commentaire théorique
        if rating >= thresh:  # si score >0,45 on sauvegarde l'id de l'hotel
            liste_recommended_hotel.append(hotel_id)
            liste_rating.append(rating)
    for x in range (5):
        try:
            indice=np.argmax(liste_rating)
            recommended_hotel.append(dico_id_hotel[liste_recommended_hotel.pop(indice)])
            liste_rating.pop(indice)
        except:None
    return recommended_hotel





# def ajout_new_comm(nom_user, nom_hotel,comm,model=svdpp,df):
#     id_user = dico_user_id[nom_user]
#     id_hotel = dico_id_hotel[nom_hotel]
#     ajout_df = pd.DataFrame(
#         {"User_id": [id_user], "Hotel_id": [id_hotel], "Sentiment": [TextBlob(comm).sentiment.polarity]})
#     df3.at[id_hotel+1,nom_user]=comm
#     df= pd.concat(df, ajout_df)
#     model=refit(df,model)
#     return df,model


def find_comm(nom_user,df=df3):

    tab_comm = []
    collone=df[nom_user].values

    for x in range(len(liste_hotel)):
        comm=str(collone[x])
        if comm!="nan":
            tab_comm.append([dico_id_hotel[x+1],comm])

    # with open('df_commentaire_sans_caracteres_speciaux.csv', 'r', encoding='utf-8') as csvfile:
    #     reader = csv.reader(csvfile)
    #     header = next(reader)
    #     row = reader[id_user]
    #     for comm in row:
    #         if comm != "":
    #             tab_comm.append(comm)
    return tab_comm

def adresse_hotel(df=df4):
    dico_nom_adress={}
    for ligne in df.values:
        dico_nom_adress[ligne[0]]=ligne[1]
    return dico_nom_adress


