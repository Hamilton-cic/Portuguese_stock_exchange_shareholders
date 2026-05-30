# -*- coding: utf-8 -*-
"""
Update boardmembers_2024.csv from conselhos.txt document.
1. Rename garbled company labels
2. Add missing members to existing companies
3. Add entirely new companies
4. When a person already exists in the dataset under a slightly different name,
   use the name already in the dataset.
"""

import pandas as pd
import unicodedata
import re
from collections import defaultdict

CSV = "boardmembers_2024.csv"

# ── Step 0: rename garbled company labels ────────────────────────────────────
COMPANY_RENAMES = {
    "B.COM.PORTUGUES":                              "Millennium BCP",
    "CORTICEIRA AMORIM":                            "Corticeira Amorim",
    "CTT CORREIOS PORT":                            "CTT Correios de Portugal",
    "EDP RENOVAVEIS":                               "EDP Renováveis",
    "ESTORIL SOL N":                                "Estoril Sol",
    "FUT.CLUBE PORTO":                              "FC Porto",
    "GALP ENERGIA-NOM":                             "Galp Energia",
    "IBERSOL,SGPS":                                 "Ibersol",
    "IMPRESA,SGPS":                                 "Impresa",
    "J.MARTINS,SGPS":                               "Jerónimo Martins",
    "Martifer":                                     "MARTIFER",   # lowercase dupe → uppercase
    "MOTA ENGIL":                                   "Mota-Engil",
    "NOS, SGPS":                                    "NOS SGPS",
    "NOVABASE,SGPS":                                "Novabase",
    "SONAECOM,SGPS":                                "Sonaecom",
    "THE NAVIGATOR COMP":                           "The Navigator Company",
    "TOYOTA CAETANO":                               "Toyota Caetano Portugal",
    "VAA VISTA ALEGRE":                             "Vista Alegre Atlantis",
    "BENFICA":                                      "SL Benfica",
    "SPORTING":                                     "Sporting CP",
    "brisa_auto_estradas_de_portugal_sociedade_2024": "Brisa",
    "cofina_s_g_p_s_s_a_sociedade_2024":            "Cofina SGPS",
    "banco_montepio":                               "Banco Montepio",
    "Grupo José de Mello":                     "Grupo José de Mello",
    "Luz Saúde":                               "Luz Saúde",
}

# ── Step 1: data from the document ───────────────────────────────────────────
# key = canonical company name to use in the dataset
# value = list of member names (exactly as in the document, we'll normalise below)
DOCUMENT_DATA = {

    # ── Companies already in dataset — check for new members ─────────────────

    "CUF": [
        "Salvador Maria Guimarães José de Mello",
        "Ema Isabel Gouveia Martins Paulino Pires",
        "João Pedro Stilwell Rocha e Melo",
        "Rui Alexandre Pires Diniz",
        "Inácio António Ponte de Metello Almeida e Brito",
        "Guilherme Barata Pereira Dias de Magalhães",
        "Catarina Marques da Rocha Gouveia",
        "Francisco Pedro Ramos Gonçalves Pereira",
        "Paula Alexandra Pais de Brito Silva",
        "Diogo Miguel Parreira de Gouveia",
        "Paulo José Marques Fernandes",
        "Paula Maria Brinca Borralho Nunes",
        "Fausto Manuel da Silva Almeida",
        "Cláudia Filipa Henriques de Almeida e Silva de Matos Sequeira",
        "Filipa Moreira da Silva de Pimentel Caldeira",
    ],

    "Brisa": [
        "António de Magalhães Pires de Lima",
        "Daniel Alexandre Miguel Amaral",
        "Manuel Rebelo Teixeira Melo Ramos",
        "Eduardo António da Costa Ramos",
        "Marta Brugnini de Sousa Uva Martinha",
        "Henrique José Marques da Costa Pulido Pereira",
        "Luis Eduardo Brito Freixial de Goes",
        "Fernando Aboudib Camargo",
        "António José Louçã Pargana",
        "Maria de Fátima Henriques da Silva Barros",
        "Joana Presas Pinto Balsemão",
        "Ana Teresa Cunha de Pinho Tavares Lehmann",
    ],

    "Jerónimo Martins": [
        "Pedro Manuel de Castro Soares dos Santos",
        "José Soares dos Santos",
        "Elizabeth Ann Bastoni",
        "María Ángela Holguín Cuéllar",
        "Sérgio Tavares Rebelo",
        "Agnieszka Slomka-Golebiovska",
        "António Domingues",
        "Fabio Villegas",
        "Francisco Sá Carneiro",
        "João Vale de Almeida",
        "Nigyar Makhmudova",
    ],

    "Corticeira Amorim": [
        "António Rios de Amorim",
        "Luísa Alexandra Ramos Amorim",
        "Cristina Rios de Amorim Baptista",
        "Nuno Filipe Vilela Barroca de Oliveira",
        "Fernando José de Araújo dos Santos Almeida",
        "Juan Ginesta Viñas",
        "João Nuno de Sottomayor Pinto de Castello Branco",
        "José Pereira Alves",
        "Maria Cristina Galhardo Vilão",
        "António Manuel Mónica Lopes de Seabra",
        "Helena Sofia Silva Borges Salgado Fonseca Cerveira Pinto",
    ],

    "Banco Big": [
        "Carlos Rodrigues",
        "Mário Bolota",
        "Ana Rita Gil",
        "João Henrique",
        "Vitor Luís",
        "Sara Carbonell",
        "José Galamba de Oliveira",
        "Teresa Cardoso de Menezes",
    ],

    "Millennium BCP": [
        "Nuno Manuel da Silva Amado",
        "Jorge Manuel Baptista Magalhães Correia",
        "Valter Rui Dias de Barros",
        "Miguel Maya Dias Pinheiro",
        "António Ferreira Pinto Júnior",
        "Carla Sofia Pereira Bambulo",
        "Fernando da Costa Lima",
        "Isabel Maria de Oliveira Capeloa Gil",
        "João Nuno de Oliveira Jorge Palma",
        "José Pedro Rivera Ferreira Malaquias",
        "Luís Miguel Manso Correia dos Santos",
        "Maria Madalena Cascais Mendes Tomé",
        "Maria José Henriques Barreto de Matos de Campos",
        "Miguel de Campos Pereira de Bragança",
        "Patrícia Andrea Bastos Teixeira Lopes Couto Viana",
        "Vicent Li",
    ],

    "Vista Alegre Atlantis": [
        "Nuno Miguel Rodrigues Terras Marques",
        "Fernando Daniel Leocádio Campos Nunes",
        "Paulo Jorge Lourenço Pires",
        "Nuno Miguel Ferreira de Assunção Barra",
        "Teodorico Figueiredo Pais",
        "Alexandra da Conceição Lopes",
        "Carlos Alberto Sá Garcia da Costa",
        "Alda Alexandra Abrantes Costa",
        "Cristina Isabel Sousa Lopes",
        "Maria Isabel Couto Fernandes",
        "Nuno Maria Pinto de Magalhães Fernandes Thomaz",
        "Céline Dora Judith Abecassis-Moedas",
        "Mário Godinho de Matos",
        "Luís Miguel Poiares Pessoa Maduro",
        "Tiago de Moura Pacheco Coelho Craveiro",
    ],

    "CTT Correios de Portugal": [
        "Raul Catarino Galamba de Oliveira",
        "Guy Patrick Guimarães de Goyri Pacheco",
        "João Sousa",
        "Joana Freitas",
        "María del Carmen Gil Marín",
        "Duarte Palma Leal Champalimaud",
        "Jürgen Schröder",
        "Margarida Maria Correia de Barros Couto",
        "Ana Isabel dos Santos Dias Garcia da Fonseca",
        "Christopher James Torino",
        "Luís Miguel Gonçalves Lopes",
    ],

    "Galp Energia": [
        "Paula Amorim",
        "Maria João Borges Carioca Rodrigues",
        "João Diogo Marques da Silva",
        "Georgios Papadimitriou",
        "Ronald Doesburg",
        "Rodrigo Vilanova",
        "Nuno Holbech Bastos",
        "Adolfo Mesquita Nunes",
        "Diogo Tavares",
        "Cristina Fonseca",
        "Rui Paulo Gonçalves",
        "Javier Cavada",
        "Jorge Seabra de Freitas",
        "Cláudia Almeida e Silva",
        "Francisco Teixeira Rêgo",
        "Ana Lúcia Zambelli",
        "Fedra Ribeiro",
        "Carlos Eduardo Ferraz Pinto",
        "Marta Amorim",
    ],

    "EDP": [
        "Miguel Stilwell de Andrade",
        "Rui Manuel Rodrigues Lopes Teixeira",
        "Vera de Morais Pinto Pereira Carneiro",
        "Ana Paula Garrido de Pina Marques",
        "Pedro Collares Pereira de Vasconcelos",
        "António Bernardo Aranha da Gama Lobo Xavier",
    ],

    "EDP Renováveis": [
        "António Sarmento Gomes Mota",
        "Miguel Stilwell de Andrade",
        "Rui Lopes Teixeira",
        "Manuel Menéndez Menéndez",
        "Rosa María García",
        "José Manuel Félix Morgado",
        "Allan J. Katz",
        "Cynthia Kay Mc Call",
        "Ana Paula Serra",
    ],

    "Mota-Engil": [
        "Carlos António Vasconcelos Mota dos Santos",
        "Gonçalo Nuno Gomes de Andrade Moura Martins",
        "Wang Jingchun",
        "Manuel António da Fonseca Vasconcelos da Mota",
        "Clare Akamanzi",
        "Francisco Manuel Seixas da Costa",
        "Guangsheng Peng",
        "Helena Sofia Silva Borges Salgado Fonseca Cerveira Pinto",
        "Isabel Maria Pereira Aníbal Vaz",
        "José Carlos Barroso Pereira Pinto Nogueira",
        "Maria Paula Queirós Vasconcelos Mota de Meireles",
        "Paulo Sacadura Cabral Portas",
        "Ping Ping",
        "Li Guangming",
    ],

    "ALTRI SGPS": [
        "Alberto João Coraceiro de Castro",
        "Carlos Alberto Sousa Van Zeller e Silva",
        "Paulo Jorge dos Santos Fernandes",
        "João Manuel Matos Borges de Oliveira",
        "Vítor Miguel Martins Jorge da Silva",
        "Miguel Allegro Garcez Palha de Sousa da Silveira",
        "João Carlos Ribeiro Pereira",
        "Sofia Isabel Henriques Reis Jorge",
        "Maria do Carmo Guedes Antunes de Oliveira",
        "Paula Simões de Figueiredo Pimentel Freixo Matos Chaves",
        "José Armindo Farinha Soares de Pina",
    ],

    "Fidelidade": [
        "Jorge Manuel Baptista Magalhães Correia",
        "Rogério Miguel Antunes Campos Henriques",
        "André Simões Cardoso",
        "António José Alves Valente",
        "António Manuel Marques de Sousa Noronha",
        "Carlos António Torroaes Albuquerque",
        "Eduardo José Stock da Cunha",
        "Hui Chen",
        "Jiefei Wang",
        "Juan Ignacio Arsuaga Serrats",
        "Lingjiang Xu",
        "Maria João Vellez Caroço Honório Paulino de Sales Luís",
        "Miguel Barbosa Namorado Rosa",
        "Miguel Barroso Abecasis",
        "Tao Li",
        "Wai Lam William Mak",
        "Xueyin Feng",
    ],

    "Luz Saúde": [
        "Jorge Manuel Baptista Magalhães Correia",
        "Isabel Maria Pereira Aníbal Vaz",
        "Artur Aires Rodrigues de Morais Vaz",
        "Ivo Joaquim Antão",
        "João Paulo da Cunha Leite de Abreu Novais",
        "Tomás Leitão Branquinho da Fonseca",
        "Margarida Maria Correia de Barros Couto",
        "Maria Isabel Toucedo Lage",
        "Rogério Miguel Antunes Campos Henriques",
        "Teresa Alexandra Pires Marques Leitão Abecasis",
        "Vítor Manuel Lopes Fernandes",
        "Fang Yao",
        "Juan Caño",
        "Thierry Chiche",
        "Gabriele Duesberg",
    ],

    "Estoril Sol": [
        "Pansy Catalina Ho Chiu-King",
        "Calvin Ka Wing Chann",
        "Daisy Ho Chiu Fung",
        "Chiu Ha Maisy Ho",
        "Miguel Queiroz",
        "Dionísio Vinagre",
        "Jorge Armindo",
    ],

    "Media Capital": [
        "Mário Ferreira",
        "Paulo Francisco Gaspar",
        "Cristina Ferreira",
        "Avelino Francisco Gaspar",
        "Luís Manuel de Oliveira da Cunha Velho",
        "João da Costa Serrenho",
        "Miguel Maria Bragança Cunha Osório Araújo",
        "Rui Freitas",
    ],

    "Toyota Caetano Portugal": [
        "José Reis da Silva Ramos",
        "Maria Angelina Martins Caetano Ramos",
        "Miguel Pedro Caetano Ramos",
        "Tom Fux",
        "Kazunori Takagi",
        "Gisela Maria Falcão Sousa Pires Passos",
    ],

    "Sonae SGPS": [
        "Duarte Paulo Teixeira de Azevedo",
        "Maria Cláudia Teixeira de Azevedo",
        "João Pedro Magalhães da Silva Torres Dolores",
        "Ângelo Gabriel Ribeirinho dos Santos Paupério",
        "José Manuel Neves Adelino",
        "Eve Henrikson",
        "Fuencisla Clemares",
        "Maria Teresa Ballester Fornes",
        "Marcelo Faria de Lima",
        "Philippe Cyriel Elodie Haspeslagh",
    ],

    "Grupo José de Mello": [
        "António Mota de Sousa Horta Osório",
    ],

    # ── New companies ─────────────────────────────────────────────────────────

    "Grupo Nabeiro / Delta Cafés": [
        "João Manuel Nabeiro",
        "Helena Nabeiro",
        "Marcos Nabeiro Tenório",
        "António Cachola",
        "Paula Nascimento",
        "David Azevedo Lopes",
        "Rui Miguel Nabeiro",
        "Rita Nabeiro",
        "Ivan Nabeiro",
    ],

    "Lusiaves": [
        "Avelino da Mota Francisco Gaspar",
        "Paulo Gaspar",
    ],

    "Grupo Alves Ribeiro": [
        "Vítor Silva Alves Ribeiro",
        "José Pais Alves Ribeiro",
        "Sofia Penaguião Silva Alves Ribeiro Pinto Coelho",
        "Rita Maria de Matos Silva Alves Ribeiro Fontão de Carvalho",
    ],

    "Banco Best": [
        "Albert Sylvain May",
        "Nuno Miguel Gomes Moutinho Rocha",
        "Pedro Alexandre Lemos Cabral das Neves",
        "Marta Carolina Mota Leite Machado Mariz",
        "Jorge Daniel Lopes da Silva",
        "João Carlos Brito da Silva Dias",
        "Ana Catarina Carvalho Gaspar Cardoso Resende Gomes",
    ],

    "Rothschild & Co (Portugal)": [
        "Bruno Scoglio de Carvalho",
        "Raul Jorge Godinho dos Santos Marques",
        "João Folque Antunes",
        "Duarte Manuel Teles Raposo Pinho de Oliveira",
    ],

    "Morais Leitão": [
        "Eduardo António Salvador Verde Rodrigues Pinho",
        "Filipe Vaz Pinto",
        "Luís do Nascimento Ferreira",
        "Magda Viçoso",
        "Tiago Félix da Costa",
    ],

    "Banco CTT": [
        "João Nuno de Sottomayor Pinto de Castello Branco",
        "Luís Maria França de Castro Pereira Coutinho",
        "António Pedro Ferreira Vaz da Silva",
        "Guy Patrick Guimarães de Goyri Pacheco",
        "João Maria de Magalhães Barros de Mello Franco",
        "Pedro Rui Fontela Coimbra",
        "Nuno Carlos Dias dos Santos Fórneas",
        "Clementina Maria Dâmaso de Jesus Silva Barroso",
        "António Emídio Pessoa Corrêa d'Oliveira",
        "João Manuel de Matos Loureiro",
        "Susana Maria Morgado Gomez Smith",
    ],

    "Bondalti": [
        "João de Mello",
        "André de Albuquerque",
        "David Fernandes Lopes",
        "Luís Rebelo da Silva",
        "Marisa Poncela",
        "Carlos Silva Lopes",
        "Pedro Rocha e Melo",
        "Vasco Luís de Mello",
        "Miguel Mantas",
    ],

    "Cimpor": [
        "Suat Çalbiyik",
        "Cevat Mert",
        "Nelson Chang",
        "Roman Cheng",
        "Eralp Tunçsoy",
        "Todd Yang",
        "Ignacio Gomez",
    ],

    "Grupo Valouro": [
        "José António dos Santos",
        "Maria Júlia dos Santos",
        "António José dos Santos",
        "Dinis dos Santos",
    ],

    "Sonae MC": [
        "Maria Cláudia Teixeira de Azevedo",
        "Ângelo Gabriel Ribeirinho dos Santos Paupério",
        "João Pedro Magalhães da Silva Torres Dolores",
        "Eduardo Humberto dos Santos Piedade",
        "Jan Reinier Voûte",
        "Álvaro Sendagorta Cudos",
        "Nina Sichtermann",
        "David Oliver Walmsley",
        "Luís Miguel Mesquita Soares Moutinho",
        "Fernando Peixoto Van Zeller",
        "Isabel Sofia Bragança Simões de Barros",
        "José Manuel Cardoso Fortunato",
    ],

    "Sonae Sierra": [
        "Maria Cláudia Teixeira de Azevedo",
        "Ângelo Gabriel Ribeirinho dos Santos Paupério",
        "Doris Pittlinger",
        "Neil Jones",
        "José Baeta Tomás",
        "João Pedro Magalhães da Silva Torres Dolores",
        "Simon Marisson",
        "Fernando Guedes de Oliveira",
        "Luís Mota Duarte",
        "Miguel Costa Moreira",
        "Ana Guedes de Oliveira",
        "Cristina Santos",
        "Alexandre Fernandes",
    ],

    "Worten": [
        "Minette Bellingan",
        "Joana Ribeiro da Silva",
        "Paulo Simões",
        "Mário Pereira",
        "Rui Cohen",
    ],

    "Super Bock Group": [
        "Manuel Soares de Oliveira Violas",
        "Carlos Manuel Gomes da Silva",
        "Pedro Américo Violas de Oliveira e Sá",
        "Christopher John Warmoth",
        "Anna Cecilia Gunnarsson Lundgren",
        "Andreas Bernhard Kirk",
        "Rui Manuel Rego Lopes Ferreira",
        "Carlos César de Morais Teixeira",
        "Luís César Bernardes da Costa Moreira",
        "Cláudio Rodrigues Mateus",
        "Nuno Ramiro da Fonte Fernandes Salgado Bernardo",
    ],

    "Sagres / SCC": [
        "Nuno Francisco Ribeiro Pinto de Magalhães",
        "Julien Haex",
        "Alfonso Auñon",
    ],

    "Sumol+Compal": [
        "António Sérgio Brito Pires Eusébio",
        "Duarte Pinto",
        "Diogo Dias",
    ],

    "Lactogal": [
        "José Marques",
        "Bruno Baldeante da Costa",
        "Daniela Brandão",
        "Jacinto Rui",
    ],

    "Multicare": [
        "Rogério Miguel Antunes Campos Henriques",
        "Maria João Vellez Caroço Honório Paulino de Sales Luís",
        "Ana Rita Guia Gomes",
        "Filipe Santos Martins",
    ],

    "OK Teleseguros": [
        "Miguel Barroso Abecasis",
        "Paulo Francisco Baião Figueiredo",
        "Rui Alexandre Silva Esteves",
        "Nuno Miguel Pombeiro Gomes Diniz Clemente",
        "Gonçalo José Graça Santos",
        "Sérgio Pereira Carvalho",
        "Tomás Mira Vaz Sérvulo Rodrigues",
    ],

    "Trofa Saúde": [
        "António Vila Nova",
        "José Vila Nova",
        "Bruno Gomes",
    ],

    "BIAL": [
        "António Mota de Sousa Horta Osório",
        "António Portela",
        "Miguel Portela",
        "Joerg Holenz",
        "Max Bricchi",
        "Jasmine Zhong",
        "Richard Pilnik",
        "Melanie Lee",
        "Pierluigi Antonelli",
        "José Redondo",
        "Pedro Pereira Gonçalves",
    ],

    "Caixa Geral de Depósitos": [
        "António Farinha Morais",
        "Paulo Moita de Macedo",
        "Francisco Ravara Cary",
        "João Paulo Tudela Martins",
        "Madalena Rocheta de Carvalho Talone",
        "Ana Maria Leça Rodrigues de Sousa Carvalho",
        "António José Alves Valente",
        "Bárbara Miranda Dinis Costa Pinto",
        "Luís Maria França de Castro Pereira Coutinho",
        "António Alberto Henriques Assis",
        "José António da Silva de Brito",
        "María del Carmen Gil Marín",
        "Eduardo José Stock da Cunha",
        "Luísa Marta Santos Soares da Silva Amaro de Matos",
        "Arlindo Manuel Limede de Oliveira",
        "João Moreira Rato",
        "Monique Eugénie Hemerijck",
    ],

    "Banco Invest": [
        "Afonso Ribeiro Pereira de Sousa",
        "António Miguel Rendeiro Ramalho Branco Amaral",
        "Luís Miguel Soares da Rocha Barradas Ferreira",
        "Marília Boavida Correia Cabral",
        "Carlos António Antolin da Cunha Ramalho",
        "José Manuel Lopes Neves de Almeida",
        "Maria Paula Toscano Figueiredo Marcelino",
        "Jorge Manuel Vieira Jordão",
        "Sara Eusébio da Fonseca",
    ],

    "Banco Carregosa": [
        "Maria Cândida Rocha e Silva",
        "Helena Catarina Gomes Soares de Moura Costa Pina",
        "José Sousa Lopes",
        "José Alves Coelho",
    ],

    "Banco Finantia": [
        "António Vila-Cova",
        "David Guerreiro",
        "Ricardo Caldeira",
        "Telma Oliveira",
        "Manuel de Faria Blanc",
        "José Archer",
        "Alzira Cabrita",
    ],

    "ABANCA": [
        "Javier Etcheverría de la Muela",
        "Juan Carlos Escotet Rodríguez",
        "Francisco Botas Ratera",
        "Inês Oom Ferreira de Sousa",
        "Ana Barros",
        "Rosa María Sánchez-Yebra Alonso",
    ],

    "Grupo Pestana": [
        "Dionísio Fernandes Pestana",
        "Paulo Prada",
        "José Roquette",
    ],

    "Grupo Solverde": [
        "Manuel Soares de Oliveira Violas",
        "Celeste Violas",
        "Ana Marta Violas",
    ],

    "Grupo Vila Galé": [
        "Jorge Rebelo de Almeida",
        "Gonçalo Rebelo de Almeida",
    ],

    "MEO / Altice Portugal": [
        "Ana Figueiredo",
        "Gonçalo Camolino",
        "José Pedro Nascimento",
        "Sofia Aguiar",
        "João Epifânio",
        "Nuno Nunes",
        "Alexander Freese",
        "Natacha Marty",
    ],

    "Media Livre": [
        "Domingos José Vieira de Matos",
        "Luís Santana",
        "Ana Dias",
        "Octávio Ribeiro",
        "Isabel Rodrigues",
        "Mário Silva",
        "Miguel Paixão",
        "Paulo Fernandes",
        "Filipa Alarcão",
    ],

    "TAP": [
        "Carlos Oliveira",
        "Luís Rodrigues",
    ],

    "PLMJ": [
        "Bruno Ferreira",
        "André Figueiredo",
        "Bárbara Godinho Correia",
        "Duarte Schmidt Lino",
        "Eduardo Nogueira Pinto",
        "Miguel C. Reis",
        "Ricardo Oliveira",
        "Rita Samoreno Gomes",
        "Joaquim Shearman de Macedo",
        "Nuno Ferreira Morgado",
    ],

    "VdA - Vieira de Almeida": [
        "Paula Gomes Freire",
        "João Vieira de Almeida",
    ],

    "OCP Portugal": [
        "Rui Carrington",
    ],

    "Grupo Azevedos": [
        "Thebar Miranda",
    ],
}

# ── Fuzzy-name matching helpers ───────────────────────────────────────────────
_SKIP = {'de', 'da', 'do', 'dos', 'das', 'e', 'a', 'di', 'del', 'van', 'von', 'bin'}

def _normalize(name: str) -> str:
    n = name.strip().lower()
    n = ''.join(c for c in unicodedata.normalize('NFD', n)
                if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', n)

def _tokens(name: str):
    return [w for w in _normalize(name).split() if w not in _SKIP]

def find_existing_name(doc_name: str, existing_names: list[str]) -> str | None:
    """Return the canonical dataset name if doc_name is clearly the same person."""
    dt = set(_tokens(doc_name))
    if len(dt) < 2:
        return None
    for ex in existing_names:
        et = set(_tokens(ex))
        shared = dt & et
        shorter = min(len(dt), len(et))
        # All tokens of the shorter name are in the longer → same person
        if len(shared) >= 2 and len(shared) == shorter:
            return ex
    return None


# ── Main ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(CSV)

# Step 0: rename company labels
df["company"] = df["company"].map(lambda c: COMPANY_RENAMES.get(c, c))
df = df.drop_duplicates(subset=["name", "company"])

# Build lookup: normalized name → original canonical name (from current dataset)
existing_names = df["name"].tolist()
norm_to_canon = {_normalize(n): n for n in existing_names}

new_rows = []
stats = []

for company, members in DOCUMENT_DATA.items():
    current_members_norm = set(
        _normalize(r["name"])
        for _, r in df[df["company"] == company].iterrows()
    )
    added = []
    for doc_member in members:
        doc_norm = _normalize(doc_member)
        # Already in dataset for this company? (exact normalised match)
        if doc_norm in current_members_norm:
            continue
        # Does this person exist in the dataset under a different name?
        matched = find_existing_name(doc_member, existing_names)
        use_name = matched if matched else doc_member
        use_norm = _normalize(use_name)
        # Skip if, after resolving, the name is already there
        if use_norm in current_members_norm:
            continue
        new_rows.append({"name": use_name, "company": company})
        current_members_norm.add(use_norm)
        added.append(use_name)
    if added:
        stats.append((company, added))

# Append and save
if new_rows:
    additions = pd.DataFrame(new_rows)
    df = pd.concat([df, additions], ignore_index=True)
    df = df.drop_duplicates(subset=["name", "company"])

df.to_csv(CSV, index=False)

# Report
print(f"boardmembers_2024.csv saved — {len(df)} rows, {df['company'].nunique()} companies\n")
for company, added in stats:
    print(f"  [{company}] +{len(added)} members:")
    for n in added:
        print(f"    {n}")
print(f"\nTotal new rows added: {len(new_rows)}")
print("\nAll companies now in dataset:")
for c in sorted(df["company"].unique()):
    print(f"  {len(df[df['company']==c]):3d}  {c}")
