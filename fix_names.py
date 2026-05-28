# -*- coding: utf-8 -*-
"""Standardise board-member names across all boardmembers_YYYY.csv files."""

import pandas as pd

NAME_CORRECTIONS = {
    # Particle-only differences
    "Ana Rebelo Carvalho Menéres de Mendonça":      "Ana Rebelo de Carvalho Menéres de Mendonça",
    "Carlos António Rocha Moreira da Silva":         "Carlos António da Rocha Moreira da Silva",
    "Ana Filipa Mendes Magalhães Saraiva Mendes":    "Ana Filipa Mendes de Magalhães Saraiva Mendes",
    "Carla Maria Araújo Gonçalves Borges Norte":     "Carla Maria de Araújo Gonçalves Borges Norte",
    "Pedro Miguel Quinteiro Marques Carvalho":       "Pedro Miguel Quinteiro Marques de Carvalho",
    "Manuel Menéndez":                               "Manuel Menéndez Menéndez",
    "Lequan Li":                                     "Li Lequan",
    "Nuno Miguel Ferreira Assunção Barra":           "Nuno Miguel Ferreira de Assunção Barra",

    # Cristina Rios Amorim
    "Cristina Rios de Amorim":    "Cristina Rios de Amorim Baptista",
    "Cristina Rios Amorim":       "Cristina Rios de Amorim Baptista",

    # António Lobo Xavier
    "António Lobo Xavier":                      "António Bernardo Aranha da Gama Lobo Xavier",
    "António Bernardo A. da Gama Lobo Xavier":  "António Bernardo Aranha da Gama Lobo Xavier",

    # Navigator / Semapa
    "Vítor Manuel Rocha Novais Gonçalves":      "Vítor Manuel Galvão Rocha Novais Gonçalves",
    "Filipa Queiroz Pereira":                   "Filipa Mendes de Almeida de Queiroz Pereira",
    "Lua Queiroz Pereira":                      "Lua Mónica Mendes de Almeida de Queiroz Pereira",
    "Mafalda Queiroz Pereira":                  "Mafalda Mendes de Almeida de Queiroz Pereira",
    "Vítor Paranhos Pereira":                   "Vítor Paulo Paranhos Pereira",
    "Paulo Lameiras Martins":                   "Paulo José Lameiras Martins",
    "Mariana Rita Antunes Marques dos Santos":  "Mariana Rita Antunes Marques dos Santos Belmar da Costa",
    "José Miguel Gens Paredes":                 "José Miguel Pereira Gens Paredes",

    # REN / BCP
    "Jorge Magalhães Correia":  "Jorge Manuel Baptista Magalhães Correia",

    # NOS board members
    "Miguel Almeida":               "Miguel Nuno Santos Almeida",
    "Jorge Graça":                  "Jorge Filipe Pinto Sequeira dos Santos Graça",
    "Luis Nascimento":              "Luís Moutinho do Nascimento",
    "Ângelo Paupério":              "Ângelo Gabriel Ribeirinho dos Santos Paupério",
    "Catarina Tavira Van-Dúnem":    "Catarina Eufémia Amorim da Luz Tavira Van-Dúnem",
    "Maria Cláudia Azevedo":        "Maria Cláudia Teixeira de Azevedo",
    "Cláudia Azevedo":              "Maria Cláudia Teixeira de Azevedo",
    "Filipa Santos Carvalho":       "Filipa de Sousa Taveira da Gama Santos Carvalho",
    "Ana Rita Rodrigues":           "Ana Rita Ferreira Rodrigues",
    "Rita Rodrigues":               "Ana Rita Ferreira Rodrigues",
    "Cristina Marques":             "Cristina Maria de Jesus Marques",
    "Daniel Beato":                 "Daniel Lopes Beato",
    "João Dolores":                 "João Pedro Magalhães da Silva Torres Dolores",
    "Manuel Ramalho Eanes":         "Manuel António Neto Portugal Ramalho Eanes",
    "Ana Paula Marques":            "Ana Paula Garrido de Pina Marques",
    "José Pedro Pereira da Costa":  "José Pedro Faria Pereira da Costa",

    # Greenvolt / ALTRI family
    "João Borges de Oliveira":  "João Manuel Matos Borges de Oliveira",
    "Pedro Borges de Oliveira": "Pedro Miguel Matos Borges de Oliveira",

    # EDP Renováveis
    "Francisco Seixas da Costa":  "Francisco Manuel Seixas da Costa",
    "Acácio Piloto":              "Acácio Liberado Mota Piloto",
    "Vera Pinto":                 "Vera de Morais Pinto Pereira Carneiro",
    "José Félix Morgado":         "José Manuel Félix Morgado",
    "Kay Mc Call":                "Cynthia Kay Mc Call",

    # Media Capital
    "Miguel Maria Bragança Cunha Osório": "Miguel Maria Bragança Cunha Osório Araújo",
    "Luis Manuel da Cunha Velho":         "Luis Manuel de Oliveira da Cunha Velho",

    # Impresa / Grupo José de Mello
    "António Horta Osório":  "António Mota de Sousa Horta Osório",

    # CGD / BCP
    "Altina Sebastian Gonzalez":    "Altina de Fátima Sebastian Gonzalez Villamarin",
    "João Nuno de Oliveira Palma":  "João Nuno de Oliveira Jorge Palma",

    # Banco Montepio
    "Maria Lúcia Bica":    "Maria Lúcia Ramos Bica",
    "Jorge Almeida Baião": "Jorge Paulo Almeida e Silva Baião",
    "José Carlos Mateus":  "José Carlos Sequeira Mateus",

    # Galp
    "Maria João Carioca":  "Maria João Borges Carioca Rodrigues",

    # CTT
    "Céline Abecassis-Moedas":  "Céline Dora Judith Abecassis-Moedas",
}

FILES = [
    "boardmembers_2018.csv",
    "boardmembers_2019.csv",
    "boardmembers_2020.csv",
    "boardmembers_2021.csv",
    "boardmembers_2022.csv",
    "boardmembers_2023.csv",
    "boardmembers_2024.csv",
]

total_fixes = 0
for fname in FILES:
    df = pd.read_csv(fname)
    fixed = 0
    for old, new in NAME_CORRECTIONS.items():
        mask = df["name"] == old
        count = int(mask.sum())
        if count > 0:
            df.loc[mask, "name"] = new
            print(f"  [{fname}] {repr(old)} -> {repr(new)}  ({count} row(s))")
            fixed += count
    df.to_csv(fname, index=False)
    if fixed:
        print(f"  -> {fname}: {fixed} corrections applied\n")
    total_fixes += fixed

print(f"\nTotal corrections across all files: {total_fixes}")
