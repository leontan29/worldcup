#!/usr/bin/env python3
"""Generates seed.sql with real 2022 FIFA World Cup data."""

def q(s):
    return str(s).replace("'", "''")

out = []
w = out.append

w("USE worldcup;")
w("SET FOREIGN_KEY_CHECKS=0;")
for t in ["session_audit","user_activity","predictions","match_events","matches","players","users","venues","teams"]:
    w(f"TRUNCATE TABLE {t};")
w("SET FOREIGN_KEY_CHECKS=1;")
w("")

# ── Venues ────────────────────────────────────────────────────────────────────
VENUES = [
    ("Lusail Stadium",                "Lusail",     "Qatar", 89000),
    ("Al Bayt Stadium",               "Al Khor",    "Qatar", 60000),
    ("Al Janoub Stadium",             "Al Wakrah",  "Qatar", 40000),
    ("Education City Stadium",        "Al Rayyan",  "Qatar", 45350),
    ("Ahmad Bin Ali Stadium",         "Al Rayyan",  "Qatar", 44740),
    ("Khalifa International Stadium", "Doha",       "Qatar", 45416),
    ("Al Thumama Stadium",            "Doha",       "Qatar", 40000),
    ("Stadium 974",                   "Doha",       "Qatar", 40000),
]
w("-- Venues")
for name, city, country, cap in VENUES:
    w(f"INSERT INTO venues (name,city,country,capacity) VALUES ('{q(name)}','{city}','{country}',{cap});")
V = {name: i+1 for i,(name,*_) in enumerate(VENUES)}
w("")

# ── Teams ─────────────────────────────────────────────────────────────────────
TEAMS = [
    # Group A
    ("Qatar",        "QAT","A", 50,"Felix Sanchez"),
    ("Ecuador",      "ECU","A", 44,"Gustavo Alfaro"),
    ("Senegal",      "SEN","A", 18,"Aliou Cisse"),
    ("Netherlands",  "NED","A",  8,"Louis van Gaal"),
    # Group B
    ("England",      "ENG","B",  5,"Gareth Southgate"),
    ("Iran",         "IRN","B", 20,"Carlos Queiros"),
    ("USA",          "USA","B", 16,"Gregg Berhalter"),
    ("Wales",        "WAL","B", 19,"Rob Page"),
    # Group C
    ("Argentina",    "ARG","C",  3,"Lionel Scaloni"),
    ("Saudi Arabia", "KSA","C", 51,"Herve Renard"),
    ("Mexico",       "MEX","C", 13,"Gerardo Martino"),
    ("Poland",       "POL","C", 26,"Czeslaw Michniewicz"),
    # Group D
    ("France",       "FRA","D",  4,"Didier Deschamps"),
    ("Australia",    "AUS","D", 38,"Graham Arnold"),
    ("Denmark",      "DEN","D", 10,"Kasper Hjulmand"),
    ("Tunisia",      "TUN","D", 30,"Jalel Kadri"),
    # Group E
    ("Spain",        "ESP","E",  7,"Luis Enrique"),
    ("Costa Rica",   "CRC","E", 31,"Luis Fernando Suarez"),
    ("Germany",      "GER","E", 11,"Hansi Flick"),
    ("Japan",        "JPN","E", 24,"Hajime Moriyasu"),
    # Group F
    ("Belgium",      "BEL","F",  2,"Roberto Martinez"),
    ("Canada",       "CAN","F", 41,"John Herdman"),
    ("Morocco",      "MAR","F", 22,"Walid Regragui"),
    ("Croatia",      "CRO","F", 12,"Zlatko Dalic"),
    # Group G
    ("Brazil",       "BRA","G",  1,"Tite"),
    ("Serbia",       "SRB","G", 21,"Dragan Stojkovic"),
    ("Switzerland",  "SUI","G", 15,"Murat Yakin"),
    ("Cameroon",     "CMR","G", 43,"Rigobert Song"),
    # Group H
    ("Portugal",     "POR","H",  9,"Fernando Santos"),
    ("Ghana",        "GHA","H", 61,"Otto Addo"),
    ("Uruguay",      "URU","H", 14,"Diego Alonso"),
    ("South Korea",  "KOR","H", 28,"Paulo Bento"),
]
w("-- Teams")
for name, code, grp, rank, coach in TEAMS:
    w(f"INSERT INTO teams (name,country_code,group_name,fifa_ranking,coach) VALUES ('{q(name)}','{code}','{grp}',{rank},'{q(coach)}');")
T = {name: i+1 for i,(name,*_) in enumerate(TEAMS)}
w("")

# ── Players ───────────────────────────────────────────────────────────────────
# (name, pos, jersey, goals, assists)
SQUADS = {
    "Argentina": [
        ("Emiliano Martinez","GK", 23,0,0),("Juan Musso","GK",1,0,0),("Franco Armani","GK",12,0,0),
        ("Nahuel Molina","DEF",26,1,1),("Gonzalo Montiel","DEF",4,0,0),("Cristian Romero","DEF",13,0,0),
        ("German Pezzella","DEF",6,0,0),("Nicolas Otamendi","DEF",19,1,0),("Lisandro Martinez","DEF",25,0,0),
        ("Marcos Acuna","DEF",8,0,0),("Nicolas Tagliafico","DEF",3,0,0),
        ("Rodrigo De Paul","MID",7,0,1),("Leandro Paredes","MID",5,0,0),("Alexis Mac Allister","MID",20,1,0),
        ("Enzo Fernandez","MID",24,1,1),("Guido Rodriguez","MID",18,0,0),("Alejandro Gomez","MID",14,0,1),
        ("Julian Alvarez","FWD",9,4,2),("Lionel Messi","FWD",10,7,3),("Lautaro Martinez","FWD",22,0,1),
        ("Angel Di Maria","FWD",11,1,1),("Paulo Dybala","FWD",21,0,0),("Joaquin Correa","FWD",16,0,0),
    ],
    "France": [
        ("Hugo Lloris","GK",1,0,0),("Alphonse Areola","GK",23,0,0),("Steve Mandanda","GK",16,0,0),
        ("Benjamin Pavard","DEF",5,0,0),("Jules Kounde","DEF",21,0,0),("Raphael Varane","DEF",4,0,0),
        ("Dayot Upamecano","DEF",2,0,0),("Ibrahima Konate","DEF",13,0,0),("Theo Hernandez","DEF",22,1,0),
        ("Lucas Hernandez","DEF",3,0,0),("William Saliba","DEF",17,0,0),
        ("Aurelien Tchouameni","MID",8,1,0),("Adrien Rabiot","MID",14,2,0),("Youssouf Fofana","MID",15,0,0),
        ("Antoine Griezmann","MID",7,0,3),("Matteo Guendouzi","MID",19,0,0),("Kingsley Coman","MID",12,0,0),
        ("Kylian Mbappe","FWD",10,8,2),("Olivier Giroud","FWD",9,4,0),("Ousmane Dembele","FWD",11,0,2),
        ("Marcus Thuram","FWD",6,1,0),("Randal Kolo Muani","FWD",20,1,1),("Christopher Nkunku","FWD",18,0,0),
    ],
    "Brazil": [
        ("Alisson Becker","GK",1,0,0),("Ederson","GK",23,0,0),("Weverton","GK",12,0,0),
        ("Danilo","DEF",13,0,1),("Thiago Silva","DEF",3,1,0),("Marquinhos","DEF",4,1,0),
        ("Eder Militao","DEF",6,0,0),("Bremer","DEF",14,0,0),("Alex Sandro","DEF",16,0,0),
        ("Alex Telles","DEF",17,0,0),
        ("Casemiro","MID",5,1,0),("Fred","MID",15,0,0),("Lucas Paqueta","MID",10,1,1),
        ("Bruno Guimaraes","MID",18,0,0),("Fabinho","MID",8,0,0),("Everton Ribeiro","MID",19,0,0),
        ("Neymar","FWD",10,2,1),("Vinicius Jr","FWD",20,1,1),("Richarlison","FWD",9,3,0),
        ("Gabriel Jesus","FWD",21,0,2),("Raphinha","FWD",22,0,1),("Rodrygo","FWD",11,2,0),
        ("Antony","FWD",24,0,0),
    ],
    "England": [
        ("Jordan Pickford","GK",1,0,0),("Nick Pope","GK",23,0,0),("Aaron Ramsdale","GK",13,0,0),
        ("Kyle Walker","DEF",2,0,0),("John Stones","DEF",5,0,0),("Harry Maguire","DEF",6,0,0),
        ("Luke Shaw","DEF",3,0,1),("Kieran Trippier","DEF",12,0,2),("Eric Dier","DEF",15,0,0),
        ("Ben White","DEF",4,0,0),("Conor Coady","DEF",16,0,0),
        ("Declan Rice","MID",19,0,0),("Jude Bellingham","MID",22,1,0),("Mason Mount","MID",18,0,0),
        ("Phil Foden","MID",7,0,1),("Jordan Henderson","MID",8,0,0),("Conor Gallagher","MID",20,0,0),
        ("Harry Kane","FWD",9,3,0),("Raheem Sterling","FWD",10,0,0),("Marcus Rashford","FWD",11,3,0),
        ("Bukayo Saka","FWD",17,3,0),("Jack Grealish","FWD",14,1,0),("James Maddison","MID",21,0,0),
    ],
    "Portugal": [
        ("Rui Patricio","GK",1,0,0),("Jose Sa","GK",22,0,0),("Diogo Costa","GK",12,0,0),
        ("Joao Cancelo","DEF",20,0,1),("Danilo Pereira","DEF",3,0,0),("Pepe","DEF",3,1,0),
        ("Ruben Dias","DEF",4,0,0),("Antonio Silva","DEF",16,0,0),("Nuno Mendes","DEF",19,0,0),
        ("Raphael Guerreiro","DEF",5,0,0),
        ("Bernardo Silva","MID",10,2,0),("Bruno Fernandes","MID",8,3,1),("Ruben Neves","MID",15,0,0),
        ("Joao Moutinho","MID",11,0,0),("Vitinha","MID",17,0,0),("Otavio","MID",13,0,0),
        ("Cristiano Ronaldo","FWD",7,3,1),("Joao Felix","FWD",21,1,0),("Goncalo Ramos","FWD",9,3,0),
        ("Rafael Leao","FWD",18,0,1),("Diogo Jota","FWD",11,0,0),("Ricardo Horta","FWD",14,1,0),
        ("Andre Silva","FWD",23,0,0),
    ],
    "Croatia": [
        ("Dominik Livakovic","GK",1,0,0),("Ivica Ivusic","GK",23,0,0),("Ivo Grbic","GK",12,0,0),
        ("Josip Juranovic","DEF",2,0,0),("Dejan Lovren","DEF",6,0,0),("Josko Gvardiol","DEF",24,1,0),
        ("Domagoj Vida","DEF",21,0,0),("Borna Sosa","DEF",20,0,1),("Borna Barisic","DEF",3,0,0),
        ("Martin Erlic","DEF",5,0,0),("Josip Stanisic","DEF",22,0,0),
        ("Luka Modric","MID",10,1,1),("Mateo Kovacic","MID",8,1,0),("Marcelo Brozovic","MID",11,0,1),
        ("Mario Pasalic","MID",19,1,0),("Lovro Majer","MID",7,0,0),("Nikola Vlasic","MID",13,0,1),
        ("Ivan Perisic","FWD",4,2,1),("Andrej Kramaric","FWD",9,2,1),("Bruno Petkovic","FWD",16,1,0),
        ("Marko Livaja","FWD",15,0,0),("Mislav Orsic","FWD",18,0,0),("Kristijan Jakic","MID",26,0,0),
    ],
    "Morocco": [
        ("Yassine Bounou","GK",1,0,0),("Munir Mohamedi","GK",16,0,0),("Ahmed Tagnaouti","GK",23,0,0),
        ("Achraf Hakimi","DEF",2,0,1),("Nayef Aguerd","DEF",5,0,0),("Romain Saiss","DEF",6,0,0),
        ("Noussair Mazraoui","DEF",12,0,0),("Jawad El Yamiq","DEF",3,0,0),("Achraf Dari","DEF",15,0,0),
        ("Yahia Attiyat Allah","DEF",22,0,0),("Badr Benoun","DEF",14,0,0),
        ("Sofyan Amrabat","MID",4,0,0),("Azzedine Ounahi","MID",8,0,0),("Selim Amallah","MID",18,0,0),
        ("Bilal El Khannouss","MID",17,0,0),("Ilias Chair","MID",21,0,0),
        ("Hakim Ziyech","FWD",7,0,2),("Youssef En-Nesyri","FWD",19,3,0),("Sofiane Boufal","FWD",11,1,1),
        ("Zakaria Aboukhlal","FWD",20,1,0),("Walid Cheddira","FWD",9,0,0),("Amine Harit","MID",10,0,0),
        ("Abdelhamid Sabiri","MID",13,1,0),
    ],
    "Germany": [
        ("Manuel Neuer","GK",1,0,0),("Marc-Andre ter Stegen","GK",22,0,0),("Kevin Trapp","GK",12,0,0),
        ("Joshua Kimmich","DEF",6,0,1),("Antonio Rudiger","DEF",2,0,0),("Niklas Sule","DEF",5,0,0),
        ("Thilo Kehrer","DEF",13,0,0),("David Raum","DEF",3,0,1),("Matthias Ginter","DEF",4,0,0),
        ("Nico Schlotterbeck","DEF",15,0,0),
        ("Leon Goretzka","MID",8,0,0),("Ilkay Gundogan","MID",21,2,0),("Kai Havertz","MID",7,2,1),
        ("Jamal Musiala","MID",14,4,2),("Thomas Muller","MID",25,0,1),("Julian Draxler","MID",11,0,0),
        ("Serge Gnabry","FWD",10,0,1),("Leroy Sane","FWD",19,1,1),("Jonas Hofmann","FWD",17,1,0),
        ("Niclas Fullkrug","FWD",9,1,0),("Karim Adeyemi","FWD",27,0,0),("Kevin Volland","FWD",24,0,0),
        ("Mario Gotze","MID",18,1,0),
    ],
}

# Fallback squad generator for teams without detailed data
POSITIONS_TEMPLATE = (
    ["GK"]*3 + ["DEF"]*8 + ["MID"]*7 + ["FWD"]*5
)
def generated_squad(team_name):
    return [(f"Player {i+1}", pos, i+1, 0, 0)
            for i, pos in enumerate(POSITIONS_TEMPLATE)]

# Fix jersey conflict in Portugal (Pepe and Danilo Pereira both #3, Joao Moutinho and Diogo Jota both #11)
SQUADS["Portugal"] = [
    ("Rui Patricio","GK",1,0,0),("Jose Sa","GK",22,0,0),("Diogo Costa","GK",12,0,0),
    ("Joao Cancelo","DEF",20,0,1),("Danilo Pereira","DEF",15,0,0),("Pepe","DEF",3,1,0),
    ("Ruben Dias","DEF",4,0,0),("Antonio Silva","DEF",16,0,0),("Nuno Mendes","DEF",19,0,0),
    ("Raphael Guerreiro","DEF",5,0,0),
    ("Bernardo Silva","MID",10,2,0),("Bruno Fernandes","MID",8,3,1),("Ruben Neves","MID",6,0,0),
    ("Joao Moutinho","MID",11,0,0),("Vitinha","MID",17,0,0),("Otavio","MID",13,0,0),
    ("Cristiano Ronaldo","FWD",7,3,1),("Joao Felix","FWD",21,1,0),("Goncalo Ramos","FWD",9,3,0),
    ("Rafael Leao","FWD",18,0,1),("Diogo Jota","FWD",14,0,0),("Ricardo Horta","FWD",23,1,0),
    ("Andre Silva","FWD",24,0,0),
]

# Fix Brazil (Neymar and Lucas Paqueta both #10)
SQUADS["Brazil"] = [
    ("Alisson Becker","GK",1,0,0),("Ederson","GK",23,0,0),("Weverton","GK",12,0,0),
    ("Danilo","DEF",13,0,1),("Thiago Silva","DEF",3,1,0),("Marquinhos","DEF",4,1,0),
    ("Eder Militao","DEF",6,0,0),("Bremer","DEF",14,0,0),("Alex Sandro","DEF",16,0,0),
    ("Alex Telles","DEF",17,0,0),
    ("Casemiro","MID",5,1,0),("Fred","MID",15,0,0),("Lucas Paqueta","MID",10,1,1),
    ("Bruno Guimaraes","MID",18,0,0),("Fabinho","MID",8,0,0),("Everton Ribeiro","MID",19,0,0),
    ("Neymar","FWD",20,2,1),("Vinicius Jr","FWD",11,1,1),("Richarlison","FWD",9,3,0),
    ("Gabriel Jesus","FWD",21,0,2),("Raphinha","FWD",22,0,1),("Rodrygo","FWD",26,2,0),
    ("Antony","FWD",24,0,0),
]

w("-- Players")
player_id = 1
PLAYER_IDS = {}  # (team_name, player_name) -> id
for team_name, *_ in TEAMS:
    tid = T[team_name]
    squad = SQUADS.get(team_name, generated_squad(team_name))
    for pname, pos, jersey, goals, assists in squad:
        w(f"INSERT INTO players (team_id,name,position,jersey_number,goals,assists) VALUES ({tid},'{q(pname)}','{pos}',{jersey},{goals},{assists});")
        PLAYER_IDS[(team_name, pname)] = player_id
        player_id += 1
w("")

# ── Matches ───────────────────────────────────────────────────────────────────
# Group stage: 48 matches, all completed with real scores.
# Knockout: 16 matches, all completed.
# Total: 64 matches.
# Format: (home, away, venue_key, date, stage, group, home_score, away_score)

GROUP_MATCHES = [
    # Group A
    ("Qatar","Ecuador",        "Al Bayt Stadium",               "2022-11-20 19:00","A",0,2),
    ("Senegal","Netherlands",  "Al Thumama Stadium",            "2022-11-21 16:00","A",0,2),
    ("Qatar","Senegal",        "Al Thumama Stadium",            "2022-11-25 13:00","A",1,3),
    ("Netherlands","Ecuador",  "Khalifa International Stadium", "2022-11-25 19:00","A",1,1),
    ("Ecuador","Senegal",      "Khalifa International Stadium", "2022-11-29 19:00","A",1,2),
    ("Netherlands","Qatar",    "Al Bayt Stadium",               "2022-11-29 19:00","A",2,0),
    # Group B
    ("England","Iran",         "Khalifa International Stadium", "2022-11-21 13:00","B",6,2),
    ("USA","Wales",            "Ahmad Bin Ali Stadium",         "2022-11-21 19:00","B",1,1),
    ("Wales","Iran",           "Ahmad Bin Ali Stadium",         "2022-11-25 10:00","B",0,2),
    ("England","USA",          "Al Bayt Stadium",               "2022-11-25 19:00","B",0,0),
    ("Wales","England",        "Ahmad Bin Ali Stadium",         "2022-11-29 19:00","B",0,3),
    ("Iran","USA",             "Al Thumama Stadium",            "2022-11-29 19:00","B",0,1),
    # Group C
    ("Argentina","Saudi Arabia","Lusail Stadium",               "2022-11-22 13:00","C",1,2),
    ("Mexico","Poland",        "Stadium 974",                   "2022-11-22 19:00","C",0,0),
    ("Poland","Saudi Arabia",  "Education City Stadium",        "2022-11-26 13:00","C",2,0),
    ("Argentina","Mexico",     "Lusail Stadium",                "2022-11-26 19:00","C",2,0),
    ("Poland","Argentina",     "Stadium 974",                   "2022-11-30 19:00","C",0,2),
    ("Saudi Arabia","Mexico",  "Lusail Stadium",                "2022-11-30 19:00","C",1,2),
    # Group D
    ("Denmark","Tunisia",      "Education City Stadium",        "2022-11-22 13:00","D",0,0),
    ("France","Australia",     "Al Janoub Stadium",             "2022-11-22 19:00","D",4,1),
    ("Tunisia","Australia",    "Al Janoub Stadium",             "2022-11-26 13:00","D",0,1),
    ("France","Denmark",       "Stadium 974",                   "2022-11-26 19:00","D",2,1),
    ("Australia","Denmark",    "Al Janoub Stadium",             "2022-11-30 19:00","D",1,0),
    ("France","Tunisia",       "Education City Stadium",        "2022-11-30 19:00","D",0,1),
    # Group E
    ("Spain","Costa Rica",     "Al Thumama Stadium",            "2022-11-23 16:00","E",7,0),
    ("Germany","Japan",        "Khalifa International Stadium", "2022-11-23 13:00","E",1,2),
    ("Japan","Costa Rica",     "Ahmad Bin Ali Stadium",         "2022-11-27 10:00","E",0,1),
    ("Spain","Germany",        "Al Bayt Stadium",               "2022-11-27 19:00","E",1,1),
    ("Japan","Spain",          "Khalifa International Stadium", "2022-12-01 19:00","E",2,1),
    ("Costa Rica","Germany",   "Al Bayt Stadium",               "2022-12-01 19:00","E",2,4),
    # Group F
    ("Morocco","Croatia",      "Al Bayt Stadium",               "2022-11-23 10:00","F",0,0),
    ("Belgium","Canada",       "Ahmad Bin Ali Stadium",         "2022-11-23 19:00","F",1,0),
    ("Belgium","Morocco",      "Al Thumama Stadium",            "2022-11-27 13:00","F",0,2),
    ("Croatia","Canada",       "Khalifa International Stadium", "2022-11-27 16:00","F",4,1),
    ("Croatia","Belgium",      "Ahmad Bin Ali Stadium",         "2022-12-01 19:00","F",0,0),
    ("Canada","Morocco",       "Al Thumama Stadium",            "2022-12-01 19:00","F",1,2),
    # Group G
    ("Brazil","Serbia",        "Lusail Stadium",                "2022-11-24 19:00","G",2,0),
    ("Switzerland","Cameroon", "Al Janoub Stadium",             "2022-11-24 13:00","G",1,0),
    ("Brazil","Switzerland",   "Stadium 974",                   "2022-11-28 13:00","G",1,0),
    ("Cameroon","Serbia",      "Al Janoub Stadium",             "2022-11-28 19:00","G",3,3),
    ("Brazil","Cameroon",      "Lusail Stadium",                "2022-12-02 19:00","G",0,1),
    ("Serbia","Switzerland",   "Stadium 974",                   "2022-12-02 19:00","G",2,3),
    # Group H
    ("Uruguay","South Korea",  "Education City Stadium",        "2022-11-24 10:00","H",0,0),
    ("Portugal","Ghana",       "Stadium 974",                   "2022-11-24 16:00","H",3,2),
    ("South Korea","Ghana",    "Education City Stadium",        "2022-11-28 10:00","H",2,3),
    ("Portugal","Uruguay",     "Lusail Stadium",                "2022-11-28 16:00","H",2,0),
    ("South Korea","Portugal", "Education City Stadium",        "2022-12-02 19:00","H",2,1),
    ("Ghana","Uruguay",        "Al Janoub Stadium",             "2022-12-02 19:00","H",0,2),
]

KNOCKOUT_MATCHES = [
    # (home, away, venue, date, stage, home_score, away_score, winner)
    # Round of 16
    ("Netherlands","USA",      "Khalifa International Stadium", "2022-12-03 19:00","round_of_16", 3,1,"Netherlands"),
    ("Argentina","Australia",  "Ahmad Bin Ali Stadium",         "2022-12-03 22:00","round_of_16", 2,1,"Argentina"),
    ("France","Poland",        "Al Thumama Stadium",            "2022-12-04 19:00","round_of_16", 3,1,"France"),
    ("England","Senegal",      "Al Bayt Stadium",               "2022-12-04 22:00","round_of_16", 3,0,"England"),
    ("Japan","Croatia",        "Al Janoub Stadium",             "2022-12-05 19:00","round_of_16", 1,1,"Croatia"),    # Croatia won on pens
    ("Brazil","South Korea",   "Stadium 974",                   "2022-12-05 22:00","round_of_16", 4,1,"Brazil"),
    ("Morocco","Spain",        "Education City Stadium",        "2022-12-06 19:00","round_of_16", 0,0,"Morocco"),    # Morocco won on pens
    ("Portugal","Switzerland", "Lusail Stadium",                "2022-12-06 22:00","round_of_16", 6,1,"Portugal"),
    # Quarterfinals
    ("Croatia","Brazil",       "Education City Stadium",        "2022-12-09 19:00","quarterfinal", 1,1,"Croatia"),   # Croatia won on pens
    ("Netherlands","Argentina","Lusail Stadium",                "2022-12-09 22:00","quarterfinal", 2,2,"Argentina"),  # Argentina won on pens
    ("Morocco","Portugal",     "Al Thumama Stadium",            "2022-12-10 19:00","quarterfinal", 1,0,"Morocco"),
    ("England","France",       "Al Bayt Stadium",               "2022-12-10 22:00","quarterfinal", 1,2,"France"),
    # Semifinals
    ("Argentina","Croatia",    "Lusail Stadium",                "2022-12-13 21:00","semifinal",    3,0,"Argentina"),
    ("France","Morocco",       "Al Bayt Stadium",               "2022-12-14 21:00","semifinal",    2,0,"France"),
    # Third place
    ("Croatia","Morocco",      "Khalifa International Stadium", "2022-12-17 17:00","third_place",  2,1,"Croatia"),
    # Final — Argentina won 4-2 on pens after 3-3 AET
    ("Argentina","France",     "Lusail Stadium",                "2022-12-18 17:00","final",        3,3,"Argentina"),
]

w("-- Group stage matches")
for home, away, venue, date, grp, hs, aws in GROUP_MATCHES:
    hid, aid, vid = T[home], T[away], V[venue]
    if hs > aws:
        winner = str(hid)
    elif aws > hs:
        winner = str(aid)
    else:
        winner = "NULL"
    w(f"INSERT INTO matches (home_team_id,away_team_id,venue_id,match_date,stage,status,home_score,away_score,winner_team_id,group_name) "
      f"VALUES ({hid},{aid},{vid},'{date}','group','completed',{hs},{aws},{winner},'{grp}');")

w("")
w("-- Knockout matches")
for home, away, venue, date, stage, hs, aws, winner in KNOCKOUT_MATCHES:
    hid, aid, vid = T[home], T[away], V[venue]
    wid = T[winner]
    w(f"INSERT INTO matches (home_team_id,away_team_id,venue_id,match_date,stage,status,home_score,away_score,winner_team_id,group_name) "
      f"VALUES ({hid},{aid},{vid},'{date}','{stage}','completed',{hs},{aws},{wid},NULL);")

w("")
print("\n".join(out))
