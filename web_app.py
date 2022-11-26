import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
from statistics import mean
import random

st.set_page_config(
    page_title = 'Bolão dos Amigos',
    page_icon = '⚽',
)

#Importar o Dataset "wcmatches_history.csv" e limpar os dados para a análise
jogos_copa = pd.read_csv('538_wc_matches.csv')
jogos_copa = jogos_copa.drop(columns=['league_id', 'league', 'spi1', 'spi2', 'prob1', 'prob2', 'probtie', 'proj_score1', 'proj_score2', 'score1', 'score2', 'xg1', 'xg2', 'nsxg1', 'nsxg2', 'adj_score1', 'adj_score2'])

# Importar Dataset de dados da Copa
dados = pd.read_excel('DadosCopaDoMundoQatar2022.xlsx', sheet_name='selecoes').rename(columns={'NomeEmIngles': 'team'}).set_index('team').rename(index={'United States': 'USA'})

# Criar lista de seleções da Copa 2022
teams = []
for team in dados.index:
    if team not in teams:
        teams.append(team)

# Importar o Dataset "international_matches.csv" e limpar os dados para a análise
hist_jogos = pd.read_csv('international_matches_filtered.csv')

# Remover histórico das seleções que não estão na Copa
# for i in hist_jogos.index:
#     if hist_jogos['home_team'][i] not in teams or hist_jogos['away_team'][i] not in teams:
#         hist_jogos = hist_jogos.drop(i)
# hist_jogos = hist_jogos.reset_index(drop=True)

# Transformar datas dos jogos em ano dos jogos
for i in hist_jogos.index:
    hist_jogos.at[i, 'date'] = hist_jogos['date'][i][-4:]
hist_jogos = hist_jogos.rename(columns={'date': 'year'})
hist_jogos['year'] = hist_jogos['year'].astype(int)
hist_jogos = hist_jogos.sort_values('year', ascending=False)

# Criar Dataframe com status de cada seleção
columns = ['fifa_rank', 'fifa_points', 'goalkeeper_score', 'defense_score', 'offense_score', 'midfield_score']
team_stats = pd.DataFrame(index= teams, columns= columns)

for team in team_stats.index:
    for i in hist_jogos.index:
        if team == hist_jogos['home_team'][i]:
            team_stats['fifa_rank'][team] = hist_jogos['home_team_fifa_rank'][i]
            team_stats['fifa_points'][team] = hist_jogos['home_team_total_fifa_points'][i]
            team_stats['goalkeeper_score'][team] = hist_jogos['home_team_goalkeeper_score'][i]
            team_stats['defense_score'][team] = hist_jogos['home_team_mean_defense_score'][i]
            team_stats['offense_score'][team] = hist_jogos['home_team_mean_offense_score'][i]
            team_stats['midfield_score'][team] = hist_jogos['home_team_mean_midfield_score'][i]
            break
        elif team == hist_jogos['away_team'][i]:
            team_stats['fifa_rank'][team] = hist_jogos['away_team_fifa_rank'][i]
            team_stats['fifa_points'][team] = hist_jogos['away_team_total_fifa_points'][i]
            team_stats['goalkeeper_score'][team] = hist_jogos['away_team_goalkeeper_score'][i]
            team_stats['defense_score'][team] = hist_jogos['away_team_mean_defense_score'][i]
            team_stats['offense_score'][team] = hist_jogos['away_team_mean_offense_score'][i]
            team_stats['midfield_score'][team] = hist_jogos['away_team_mean_midfield_score'][i]
            break

team_stats['fifa_rank'] = team_stats['fifa_rank'].astype(int)
team_stats['fifa_points'] = team_stats['fifa_points'].astype(int)
team_stats = team_stats.sort_values('fifa_points', ascending= False)

team_stats.at['Qatar', 'goalkeeper_score'] = round((team_stats['goalkeeper_score']['Saudi Arabia'] * team_stats['fifa_points']['Qatar']) / team_stats['fifa_points']['Saudi Arabia'], 1)
team_stats.loc['Qatar', 'defense_score'] = round((team_stats['defense_score']['Saudi Arabia'] * team_stats['fifa_points']['Qatar']) / team_stats['fifa_points']['Saudi Arabia'], 1)
team_stats.loc['Qatar', 'offense_score'] = round((team_stats['offense_score']['Saudi Arabia'] * team_stats['fifa_points']['Qatar']) / team_stats['fifa_points']['Saudi Arabia'], 1)
team_stats.loc['Qatar', 'midfield_score'] = round((team_stats['midfield_score']['Saudi Arabia'] * team_stats['fifa_points']['Qatar']) / team_stats['fifa_points']['Saudi Arabia'], 1)
team_stats.loc['Tunisia', 'goalkeeper_score'] = round((team_stats['goalkeeper_score']['Canada'] * team_stats['fifa_points']['Tunisia']) / team_stats['fifa_points']['Canada'], 1)

# Pegar média de gols das copas
torneios = hist_jogos.groupby('tournament').mean(numeric_only= True)
mgols = (torneios['home_team_score']['FIFA World Cup'] + torneios['away_team_score']['FIFA World Cup'])

# Remover jogos anteriores a 2018, utilizar apenas os últimos 5 anos de histórico 
for i in range(len(hist_jogos['year'])):
    if hist_jogos['year'][i] < 2018:
        hist_jogos = hist_jogos.drop(i)
hist_jogos = hist_jogos.reset_index(drop=True)

#Remover jogos amistosos
for i in hist_jogos.index:
    if hist_jogos['tournament'][i] == 'Friendly':
        hist_jogos = hist_jogos.drop(index= i)
hist_jogos = hist_jogos.reset_index(drop=True)

# Definir função que identifica possível média de gols por partida
def media_gols(team1, team2):
    if team1 not in teams:
        raise ValueError(f'{team1} not  in the  World Cup!')
    elif team2 not in teams:
        raise ValueError(f'{team2} not  in the  World Cup!')

    gols = 0
    partidas = 0

    for i in hist_jogos.index:
        if (hist_jogos['home_team'][i] == team1 and hist_jogos['away_team'][i] == team2) or (hist_jogos['home_team'][i] == team2 and hist_jogos['away_team'][i] == team1):
            gols += hist_jogos['home_team_score'][i] + hist_jogos['away_team_score'][i]
            partidas += 1

    try:
        return gols / partidas
    except:
        return mgols

# Definir função  que identifica força de cada equipe em campo
def lam(team1, team2):
    gols = media_gols(team1, team2)
    fifa1, fifa2 = team_stats['fifa_points'][team1], team_stats['fifa_points'][team2]
    off1, off2 = team_stats['offense_score'][team1], team_stats['offense_score'][team2]
    def1, def2 = team_stats['defense_score'][team1], team_stats['defense_score'][team2]
    mid1, mid2 = team_stats['midfield_score'][team1], team_stats['midfield_score'][team2]
    gk1, gk2  = team_stats['goalkeeper_score'][team1], team_stats['goalkeeper_score'][team2]
    
    pwr1 = (fifa1 / fifa2) * ((0.9 * off1 + 0.1 * mid1) / (0.8 * def2 + 0.2 * gk2))
    pwr2 = (fifa2 / fifa1) * ((0.9 * off2 + 0.1 * mid2) / (0.8 * def1 + 0.2 * gk1))

    l1 = gols * pwr1 / (pwr1 + pwr2)
    l2 = gols * pwr2 / (pwr1 + pwr2)

    return l1, l2

# Definir a função que identifica o resultado de cada jogo
def resultado(gols1, gols2):
    if gols1 > gols2:
        return 'V'
    elif gols2 > gols1:
        return 'D'
    else:
        return 'E'

# Definir a função que distribui os pontos baseados no resultado do jogo
def pontos(gols1, gols2):
    rst = resultado(gols1, gols2)
    if rst == 'V':
        pts1, pts2 = 3, 0
    if rst == 'D':
        pts1, pts2 = 0, 3
    if rst == 'E':
        pts1, pts2 = 1, 1
    return pts1, pts2

# Definir a função que simula cada jogo
def jogo(team1, team2):
    l1, l2 = lam(team1, team2)
    gols1 = int(np.random.poisson(lam=l1 , size=1))
    gols2 = int(np.random.poisson(lam=l2 , size=1))
    saldo1 = gols1 - gols2
    saldo2 = -saldo1
    rst = resultado(gols1, gols2)
    pts1, pts2 = pontos(gols1, gols2)
    placar = f'{gols1}x{gols2}'
    return {'gols1': gols1, 'gols2': gols2, 'saldo1': saldo1, 'saldo2': saldo2, 
            'pts1': pts1, 'pts2': pts2, 'rst': rst, 'placar': placar}

#  Definir função que calcula a probalidade da quantidade de gols baseado na média de gols da partida
def distribuicao(media):
    probs = []
    for i in range(7):
        probs.append(poisson.pmf(i, media))
    probs.append(1 - sum(probs))
    return pd.Series(probs, index= ['0', '1', '2', '3', '4', '5', '6', '7+'])

# Definir os 3 placares de  maior  probabilidade

# Definir probabilidades de resultado de cada jogo
def probabilidades_partida(team1, team2):
    l1, l2 = lam(team1, team2)
    d1, d2 = distribuicao(l1), distribuicao(l2)
    matriz = np.outer(d1, d2)
    
    sort = np.sort(matriz)
    max_values = []
    for i in sort:
        for j in i:
            max_values.append(j)
    max_values.sort(reverse= True)
    placares = []
    for i in range(5):
        a = int(np.where(matriz == max_values[i])[0])
        b = int(np.where(matriz == max_values[i])[1])
        placares.append((f'{max_values[i] * 100 :.1f}%', f'{a}x{b}'))


    v = np.tril(matriz).sum() - np.trace(matriz)
    d = np.triu(matriz).sum() - np.trace(matriz)
    e = np.trace(matriz)

    probs = np.around([v, e, d], 3)
    probsp = [f'{100 * i :.1f}%'  for i in  probs]
    
    nomes = ['0', '1', '2', '3', '4', '5', '6', '7+']
    matriz = pd.DataFrame(matriz, columns = nomes, index = nomes)
    matriz.index = pd.MultiIndex.from_product([[selecao1], matriz.index])
    matriz.columns = pd.MultiIndex.from_product([[selecao2], matriz.columns])

    return {'probabilidades': probsp, 'placares': placares, 'matriz': matriz}

# Definir simulação de jogo mata-mata
def jogo_matamata(team1, team2):
    partida = jogo(team1, team2)
    rst = partida['rst']
    if rst == 'V':
        return team1
    elif rst == 'D':
        return team2
    else:
        return random.sample([team1, team2], 1)[0]

######## COMEÇO DO APP

st.markdown("<h1 style='text-align: center; color: blue;'>🍻 Cervejaria do Meu Amigo 🍻</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>🏆 Bolão dos Amigos 🏆</h1>", unsafe_allow_html=True)

st.markdown('---')
st.markdown("## ⚽ Probabilidades das Partidas")

listaselecoes1 = list(dados['Seleção'])
listaselecoes1.sort()
listaselecoes2 = listaselecoes1.copy()

col1, col2 = st.columns(2)
selecao1 = col1.selectbox('Escolha a primeira Seleção', listaselecoes1)
listaselecoes2.remove(selecao1)
selecao2 = col2.selectbox('Escolha a segunda Seleção', listaselecoes2, index= 1)
st.markdown('---')

team1 = dados.index[dados['Seleção'] == selecao1][0]
team2 = dados.index[dados['Seleção'] == selecao2][0]
partida = probabilidades_partida(team1, team2)
prob = partida['probabilidades']
matriz = partida['matriz']
placares = partida['placares']

col1, col2, col3, col4, col5 = st.columns(5)
col1.image(dados.loc[team1, 'LinkBandeiraPequena'])  
col2.metric(selecao1, prob[0])
col3.metric('Empate', prob[1])
col4.metric(selecao2, prob[2]) 
col5.image(dados.loc[team2, 'LinkBandeiraPequena'])

st.markdown('---')
st.markdown("## 📊 Probabilidades dos Placares") 

def aux(x):
	return f'{str(round(100*x,1))}%'
st.table(matriz.applymap(aux))

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(placares[0][0], placares[0][1])
col2.metric(placares[1][0], placares[1][1])
col3.metric(placares[2][0], placares[2][1])
col4.metric(placares[3][0], placares[3][1])
col5.metric(placares[4][0], placares[4][1])

st.markdown('---')
st.markdown("## 🌍 Probabilidades dos Jogos da Copa") 

jogos_copa['Grupo'] = None
for i in jogos_copa.index:
    jogos_copa.at[i, 'Grupo'] = dados['Grupo'][jogos_copa['team1'][i]]

jogos_copa['Vitória 1'] = None
jogos_copa['Empate'] = None
jogos_copa['Vitória 2'] = None

for i in jogos_copa.index:
    team1, team2 = jogos_copa['team1'][i], jogos_copa['team2'][i]
    v, e, d = probabilidades_partida(team1, team2)['probabilidades']
    jogos_copa['Vitória 1'][i] = v
    jogos_copa['Empate'][i] = e
    jogos_copa['Vitória 2'][i] = d
    jogos_copa.at[i, 'team1'] = dados['Seleção'][team1]
    jogos_copa.at[i, 'team2'] = dados['Seleção'][team2]

jogos_copa = jogos_copa.rename(columns={'date' : 'Data', 'team1' : 'Seleção 1', 'team2' : 'Seleção 2'})
st.table(jogos_copa)

st.markdown('---')
st.markdown("<h1 style='text-align: right;'>🍺 Bom Jogo!</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: right;'>- Cervejaria do Meu Amigo</p>", unsafe_allow_html=True)
