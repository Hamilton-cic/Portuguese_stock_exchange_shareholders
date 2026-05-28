# -*- coding: utf-8 -*-
"""Rename garbled/slugified company names in boardmembers_2018-2023.csv."""

import pandas as pd

# Maps every garbled slug -> clean company name
COMPANY_MAP = {

    # ── 2018 slugs (URL-encoded Portuguese chars) ────────────────────────────
    "altri":                        "ALTRI SGPS",
    "cofina":                       "Cofina SGPS",
    "compta":                       "Compta",
    "corticeira_amorim":            "Corticeira Amorim",
    "ctt":                          "CTT Correios de Portugal",
    "edp_renov_c3_a1veis":          "EDP Renováveis",
    "galp_energia":                 "Galp Energia",
    "glintt":                       "Glintt",
    "grupo_media_capital":          "Media Capital",
    "ibersol":                      "Ibersol",
    "impresa":                      "Impresa",
    "inapa":                        "Inapa",
    "jer_c3_b3nimo_martins":        "Jerónimo Martins",
    "lisgr_c3_a1fica":              "Lisgráfica",
    "martifer":                     "Martifer",
    "mota_engil":                   "Mota-Engil",
    "nos":                          "NOS SGPS",
    "novabase":                     "Novabase",
    "pharol":                       "Pharol",
    "ramada":                       "Ramada",
    "ren":                          "REN",
    "sag_gest":                     "SAG Gest",
    "semapa":                       "Semapa",
    "sonae_capital":                "Sonae Capital",
    "sonae_ind_c3_bastria":         "Sonae Indústria",
    "sonae_sgps":                   "Sonae SGPS",
    "sonaecom":                     "Sonaecom",
    "teixeira_duarte":              "Teixeira Duarte",
    "the_navigator_company":        "The Navigator Company",
    "vista_alegre":                 "Vista Alegre Atlantis",

    # ── 2019 slugs (same companies + _s/_sgps_s/_sa suffixes) ───────────────
    "altri_sgps_s":                         "ALTRI SGPS",
    "caixa_geral_de_dep_c3_b3sitos_s":      "Caixa Geral de Depósitos",
    "cofina_sgps_s":                        "Cofina SGPS",
    "corticeira_amorim_sgps_s":             "Corticeira Amorim",
    "ctt_correios_de_portugal_s":           "CTT Correios de Portugal",
    "edp_renov_c3_a1veis_s":               "EDP Renováveis",
    "estoril_sol_sgps_s":                   "Estoril Sol",
    "flexdeal_simfe_sa":                    "Flexdeal",
    "galp_energia_sgps_s":                  "Galp Energia",
    "glintt_sa":                            "Glintt",
    "grupo_media_capital_sgps_s":           "Media Capital",
    "ibersol_sgps_s":                       "Ibersol",
    "impresa_sgps_s":                       "Impresa",
    "inapa_sgps_s":                         "Inapa",
    "jer_c3_b3nimo_martins_s":             "Jerónimo Martins",
    "lisgr_c3_a1fica_s":                   "Lisgráfica",
    "martifer_sgps_s":                      "Martifer",
    "mota_engil_sgps_s":                    "Mota-Engil",
    "nos_sgps_s":                           "NOS SGPS",
    "novabase_sgps_s":                      "Novabase",
    "pharol_sgps_s":                        "Pharol",
    "ramada_s":                             "Ramada",
    "ren_sgps_s":                           "REN",
    "semapa_sgps_s":                        "Semapa",
    "sonae_capital_sgps_s":                 "Sonae Capital",
    "sonae_ind_c3_bastria_sgps_s":          "Sonae Indústria",
    "sonae_sgps_s":                         "Sonae SGPS",
    "teixeira_duarte_s":                    "Teixeira Duarte",
    "the_navigator_company_s":              "The Navigator Company",
    "vaa_vista_alegre_atlantis_sgps_s":     "Vista Alegre Atlantis",

    # ── 2020 document IDs ────────────────────────────────────────────────────
    "0589065acaae0f3e91c7fbd084bdc5a8":     "FC Porto",
    "af_sporting_rc_20192020_v10":          "Sporting CP",
    "pc78375":                              "Flexdeal",
    "pc78487":                              "Jerónimo Martins",
    "pc78544":                              "CTT Correios de Portugal",
    "pc78843":                              "Cofina SGPS",
    "pc79133":                              "Glintt",
    "pc79165":                              "Estoril Sol",
    "pc79176":                              "Lisgráfica",
    "pc79209":                              "Vista Alegre Atlantis",
    "pc79236":                              "Inapa",
    "pc79244":                              "Ibersol",
    "pc79606":                              "Media Capital",
    "rgs78414":                             "EDP Renováveis",
    "rgs78478":                             "EDP",
    "rgs78508":                             "Pharol",
    "rgs78642":                             "REN",
    "rgs78694":                             "NOS SGPS",
    "rgs78707":                             "Sonae Indústria",
    "rgs78736":                             "Corticeira Amorim",
    "rgs78751":                             "Sonae SGPS",
    "rgs78770":                             "Mota-Engil",
    "rgs78822":                             "Semapa",
    "rgs78839":                             "ALTRI SGPS",
    "rgs79094":                             "Martifer",
    "rgs79120":                             "Novabase",
    "rgs79135":                             "Caixa Geral de Depósitos",
    "rgs79155":                             "Impresa",
    "rgs79206":                             "Toyota Caetano Portugal",
    "rgs_the_navigator_c":                  "The Navigator Company",

    # ── 2021 short slugs ─────────────────────────────────────────────────────
    # "altri", "ctt", "ibersol", etc. already covered above
    "bcp":                          "Banco Comercial Português",
    "benfic1":                      "SL Benfica",
    "confina":                      "Cofina SGPS",   # typo in source
    "cortic1":                      "Corticeira Amorim",
    "edp":                          "EDP",
    "edp_r":                        "EDP Renováveis",
    "estoril_sol":                  "Estoril Sol",
    "fcport1":                      "FC Porto",
    "flexdeal":                     "Flexdeal",
    "galp":                         "Galp Energia",
    "glintt1":                      "Glintt",
    "greenv1":                      "Greenvolt",
    # "ibersol", "impresa", "martifer", "mota_engil" covered above
    "jernim1":                      "Jerónimo Martins",
    # "lisgr_c3_a1fica" covered above
    "mdiaca1":                      "Media Capital",
    # "nos", "novabase", "pharol", "ramada", "ren", "semapa" covered above
    "sonae":                        "Sonae SGPS",
    "vaa":                          "Vista Alegre Atlantis",

    # ── 2022 document IDs ────────────────────────────────────────────────────
    "2023_04_30_tcap_relatorio_anual_2022_pt_vf_compressed_1": "Toyota Caetano Portugal",
    "8f4ffec2c9291b78657f350ec51a47cc":     "FC Porto",
    "airgalp2022pt3book3corporategovernance": "Galp Energia",
    "pc85186":                              "The Navigator Company",
    "pc8554":                               "Estoril Sol",
    "pc85549":                              "Glintt",
    "pc85615":                              "Vista Alegre Atlantis",
    "pc85715":                              "Inapa",
    "pc85863":                              "Lisgráfica",
    "relat_c3_b3rio":                       "NOS SGPS",
    "rgs83":                                "Sporting CP",
    "rgs83672":                             "SL Benfica",
    "rgs84606":                             "Flexdeal",
    "rgs848":                               "Pharol",
    "rgs84853":                             "EDP Renováveis",
    "rgs84975":                             "EDP",
    "rgs85110":                             "REN",
    "rgs85200":                             "Sonaecom",
    "rgs8522":                              "Corticeira Amorim",
    "rgs85257":                             "ALTRI SGPS",
    "rgs85264":                             "Cofina SGPS",
    "rgs8527":                              "Ramada",
    "rgs85284":                             "Greenvolt",
    "rgs85311":                             "Mota-Engil",
    "rgs85329":                             "Semapa",
    "rgs85366":                             "Jerónimo Martins",
    "rgs854":                               "Media Capital",
    "rgs85587":                             "Martifer",
    "rgs85610":                             "Novabase",
    "rgs85668":                             "Impresa",
    "rgs85713":                             "Ibersol",
    "rgsbcp2022_pt":                        "Banco Comercial Português",
    "tdsa_rc_2022_pt_versao_nao_esef":      "Teixeira Duarte",

    # ── 2023 slugs and file names ────────────────────────────────────────────
    "altri_pt":                             "ALTRI SGPS",
    # "bcp" covered above
    "benfica":                              "SL Benfica",
    # "cofina" covered above
    "corticeira_amorim1":                   "Corticeira Amorim",
    # "edp" covered above
    "edpr":                                 "EDP Renováveis",
    # "estoril_sol" covered above
    "fcp":                                  "FC Porto",
    # "flexdeal", "glintt" covered above
    "greenvolt1":                           "Greenvolt",
    # "ibersol", "impresa" covered above
    "jeronimo_martins":                     "Jerónimo Martins",
    # "martifer", "mota_engil", "nos", "novabase", "pharol", "ramada" covered
    "rcfinalvaa20231":                      "Vista Alegre Atlantis",
    "rel_anu":                              "Inapa",
    "relatoorio_integrado_2023_pt":         "CTT Correios de Portugal",
    "relatorio_contas_anual_banco_montepio_20231": "Banco Montepio",
    "relatorio_contas_cgd":                 "Caixa Geral de Depósitos",
    "relatorio_e_contas_tdsa_20231":        "Teixeira Duarte",
    "relatoriodogovernosocietario1":        "Galp Energia",
    "scp":                                  "Sporting CP",
    # "semapa", "sonae", "sonaecom" covered above
    "the_navigator":                        "The Navigator Company",
    "toyota":                               "Toyota Caetano Portugal",
    "media_capital1":                       "Media Capital",
}

FILES = [
    ("boardmembers_2018.csv", 2018),
    ("boardmembers_2019.csv", 2019),
    ("boardmembers_2020.csv", 2020),
    ("boardmembers_2021.csv", 2021),
    ("boardmembers_2022.csv", 2022),
    ("boardmembers_2023.csv", 2023),
]

for fname, year in FILES:
    df = pd.read_csv(fname)
    before = sorted(df["company"].unique())
    df["company"] = df["company"].map(lambda c: COMPANY_MAP.get(c, c))
    after = sorted(df["company"].unique())
    unmapped = [c for c in after if c not in COMPANY_MAP.values() and c not in COMPANY_MAP]
    df = df.drop_duplicates(subset=["name", "company"])
    df.to_csv(fname, index=False)
    print(f"\n{year}: {fname}  ({len(df)} rows)")
    print(f"  Companies: {after}")
    if unmapped:
        print(f"  STILL UNMAPPED: {unmapped}")
