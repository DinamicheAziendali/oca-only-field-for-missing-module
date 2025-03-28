# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# @author: Marco Calcagni <mcalcagni@dinamicheaziendali.it>
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import base64

from odoo import _, fields, models
from odoo.exceptions import UserError

global_cu_number = 0
global_total_record_b = 0
global_total_record_d = 0
global_total_record_h = 0


class CUFileExport2023(models.TransientModel):
    """
    Questa classe genera il file per la trasmissione telematica delle CU
    """
    _name = "cu.file.export.2023"
    _description = "CU File Export 2023 Wizard"
    _end_line = "\r\n"
    _len_rec = 16

    def _record_a(self, statement):
        # record A testa
        a1_tipo_record = "A"
        a2_filler = " " * 14
        a3_codice_fornitura = statement["supply_code"]
        a4_tipo_fornitore = "01"
        a5_codice_fiscale_del_fornitore = (
            statement["delegate_fiscalcode"].ljust(16)[:16]
        )
        a6_filler = " " * 483
        a7_filler = " " * 4
        a8_filler = " " * 4
        a9_campo_utente = " " * 100
        a10_filler = " " * 1068
        a11_servizio_telematico = " " * 200
        a12_filler = "A"
        return (
            a1_tipo_record
            + a2_filler
            + a3_codice_fornitura
            + a4_tipo_fornitore
            + a5_codice_fiscale_del_fornitore
            + a6_filler
            + a7_filler
            + a8_filler
            + a9_campo_utente
            + a10_filler
            + a11_servizio_telematico
            + a12_filler
            + self._end_line
        )

    def _record_b(self, statement):
        # record B
        global global_total_record_b, global_cu_number
        global_total_record_b += 1

        b1_tipo_record = "B"
        b2_cf_sostituto_di_imposta = statement["employer_fiscalcode"].ljust(16)[:16]
        b3_progressivo_modulo = str("1").rjust(8, "0")
        b4_filler = " "
        b5_filler = " " * 8
        b6_filler = " " * 25
        b7_filler = " " * 14
        b8_filler = " " * 16
        b9_filler = " "
        b10_certificazioni_da_annullare = statement["cancelled"]
        b11_certificazioni_da_sostituire = statement["substitution"]
        if (
            not statement["employer_firstname"]
            or statement["employer_firstname"] == ""
        ):
            b12_cognome = " " * 24
            b13_nome = " " * 20
            b14_denominazione = statement["employer_lastname"].ljust(60)[:60]
        else:
            b12_cognome = statement["employer_lastname"].ljust(24)[:24]
            b13_nome = statement["employer_firstname"].ljust(20)[:20]
            b14_denominazione = " " * 60
        b15_email = statement["employer_email"].ljust(100)[:100]
        b16_tel_fax = statement["employer_phone"].ljust(12)[:12]
        b17_eventi_eccezzionali = "00"
        b18_cf_rappresentante_firmatario = (
            statement["taxpayer_fiscalcode"].ljust(16)[:16]
        )
        b19_codice_carica_rappresentante = "01"
        b20_cognome_rappresentante = statement["taxpayer_lastname"].ljust(24)[:24]
        b21_nome_rappresentante = statement["taxpayer_firstname"].ljust(20)[:20]
        b22_cf_societa_dichiarante = "0" * 11
        b23_filler = " " * 18
        b24_cu_number = str(int(global_cu_number)).rjust(8, "0")
        b25_quadro_ct = "0"
        b26_firma = "1"
        b27_cf_intermediario = statement["delegate_fiscalcode"].ljust(16)[:16]
        b28_impegno_a_trasmettere = statement["delegate_commitment"][:1]
        b29_data_impegno = statement["delegate_date"].strftime("%d%m%Y")
        b30_firma_intermediario = "1"
        b31_filler = " "
        b32_filler = " " * 40
        b33_filler = " " * 2
        b34_filler = " " * 5
        b35_filler = " " * 35
        b36_filler = " " * 6
        b37_casi_particolari = "0"
        b38_filler = " " * 11
        b39_filler = " " * 16
        b40_filler = " " * 1289
        b41_servizio_telematico = " " * 20
        b42_filler = " " * 7
        b43_filler = " " * 3
        b44_filler = " " * 3
        b45_filler = " "
        b46_filler = " "
        b47_filler = " "
        b48_filler = " "
        b49_filler = " "
        b50_filler = " "
        b51_filler = " " * 15
        b52_filler = "A"
        return (
            b1_tipo_record
            + b2_cf_sostituto_di_imposta
            + b3_progressivo_modulo
            + b4_filler
            + b5_filler
            + b6_filler
            + b7_filler
            + b8_filler
            + b9_filler
            + b10_certificazioni_da_annullare
            + b11_certificazioni_da_sostituire
            + b12_cognome
            + b13_nome
            + b14_denominazione
            + b15_email
            + b16_tel_fax
            + b17_eventi_eccezzionali
            + b18_cf_rappresentante_firmatario
            + b19_codice_carica_rappresentante
            + b20_cognome_rappresentante
            + b21_nome_rappresentante
            + b22_cf_societa_dichiarante
            + b23_filler
            + b24_cu_number
            + b25_quadro_ct
            + b26_firma
            + b27_cf_intermediario
            + b28_impegno_a_trasmettere
            + b29_data_impegno
            + b30_firma_intermediario
            + b31_filler
            + b32_filler
            + b33_filler
            + b34_filler
            + b35_filler
            + b36_filler
            + b37_casi_particolari
            + b38_filler
            + b39_filler
            + b40_filler
            + b41_servizio_telematico
            + b42_filler
            + b43_filler
            + b44_filler
            + b45_filler
            + b46_filler
            + b47_filler
            + b48_filler
            + b49_filler
            + b50_filler
            + b51_filler
            + b52_filler
            + self._end_line
        )

    def compose_val(self, val_rec, val_code, rec_type):
        """
        Questa funzione serve per compilare in modo corretto i campi
        non posizionali
        """
        # se il valore è vuoto allora scarto
        if val_rec == "" or val_rec == 0:
            return ""

        # Campo alfanumerico
        if rec_type == "AN":
            # aggiunta gestione del carattere + se val_code è maggiore di 16
            val_rec_n = val_rec[1:]
            val_rec_1 = val_rec[:1]
            len_rec_n = self._len_rec - 1
            val_list = [
                val_rec_n[i: i + len_rec_n]
                for i in range(0, len(val_rec_n), len_rec_n)
            ]
            code = ""
            i = 0
            if val_list:
                for val in val_list:
                    i += 1
                    if i == 1:
                        val_pref = val_rec_1
                    else:
                        val_pref = "+"
                    code += val_code + val_pref + val.ljust(len_rec_n)[:len_rec_n]
            else:
                code += val_code + val_rec_1.ljust(self._len_rec)[:self._len_rec]
            return code

        # Data nel formato AAAA
        if rec_type == "DA":
            code = val_code + str(int(val_rec)).rjust(self._len_rec, " ")
            return code

        # Data nel formato GGMMAAAA
        if rec_type == "DT":
            date = str(int(val_rec)).zfill(8)
            code = val_code + date.rjust(self._len_rec, " ")
            return code

        # Casella barrata
        if rec_type == "CB":
            code = val_code + str(int(val_rec)).rjust(self._len_rec, " ")
            return code

        # Codice fiscale
        if rec_type == "CF":
            code = val_code + val_rec.ljust(self._len_rec)[: self._len_rec]
            return code

        # Codice fiscale numerico
        if rec_type == "CN":
            code = val_code + val_rec[:11].ljust(self._len_rec)[: self._len_rec]
            return code

        # Sigla delle province italiane
        if rec_type == "PR" or rec_type == "PN":
            code = val_code + val_rec[:2].ljust(self._len_rec)[: self._len_rec]
            return code

        # Campo numerico positivo o negativo con due cifre decimali
        if rec_type == "VP" or rec_type == "VN":
            val_rec_formatted = (
                format(val_rec, ".2f").rjust(self._len_rec, " ").replace(".", ",")
            )
            code = val_code + val_rec_formatted
            return code

        # Campo numerico positivo
        if rec_type == "NP":
            val_rec_formatted = (
                format(val_rec, ".0f").rjust(self._len_rec, " ").replace(".", ",")
            )
            code = val_code + val_rec_formatted
            return code

        # Campo numerico al massimo di 1 cifra
        if rec_type == "N1":
            val_rec_formatted = (
                format(val_rec, ".1f").rjust(self._len_rec, " ").replace(".", ",")
            )
            code = val_code + val_rec_formatted
            return code

        # Campo numerico al massimo di 1 cifra
        if rec_type == "N3":
            val_rec_formatted = (
                format(val_rec, ".3f").rjust(self._len_rec, " ").replace(".", ",")
            )
            code = val_code + val_rec_formatted
            return code
        return ""

    def _record_d(self, statement, se_partner, progressivo):
        # record D
        global global_total_record_d
        global_total_record_d += 1

        d1_tipo_record = "D"
        d2_cf_sostituto_di_imposta = statement["employer_fiscalcode"].ljust(16)[:16]
        d3_progressivo_modulo = str("1").rjust(8, "0")
        d4_cf_percipiente = se_partner["fiscalcode"].ljust(16)[:16]
        d5_progressivo = str(int(progressivo)).rjust(5, "0")
        d6_identificativo_invio = se_partner["ade_protocol"]
        d7_progressivo_attribuito = se_partner["ade_sequence"]
        d8_spazio_utente = " " * 14
        d9_annullamento_sostituzione = se_partner["ade_operation"]
        d10_filler = " " * 4
        d11_conferma_singola = "0"

        da001 = ""
        da001 += self.compose_val(
            statement["employer_fiscalcode"], "DA001001", "AN"
        )
        da001 += self.compose_val(
            statement["employer_lastname"], "DA001002", "AN"
        )
        da001 += self.compose_val(
            statement["employer_firstname"], "DA001003", "AN"
        )
        da001 += self.compose_val(
            statement["employer_city"], "DA001004", "AN"
        )
        da001 += self.compose_val(
            statement["employer_province"], "DA001005", "PR"
        )
        da001 += self.compose_val(
            statement["employer_zip"], "DA001006", "AN"
        )
        da001 += self.compose_val(
            statement["employer_address"], "DA001007", "AN"
        )
        da001 += self.compose_val(
            statement["employer_phone"], "DA001008", "AN"
        )
        da001 += self.compose_val(
            statement["employer_email"], "DA001009", "AN"
        )
        da001 += self.compose_val(
            statement["employer_ateco_id"], "DA001010", "AN"
        )
        da001 += self.compose_val(
            statement["employer_headquarters"], "DA001011", "AN"
        )
        da001 += self.compose_val(
            "", "DA001012", "CN"
        )

        codice_stato_estero = 0.000
        comune_estero = ""
        provincia_estero = ""
        # dati del percipiente
        da002 = ""
        da002 += self.compose_val(
            se_partner["fiscalcode"], "DA002001", "CF"
        )
        da002 += self.compose_val(
            se_partner["lastname"], "DA002002", "AN"
        )
        da002 += self.compose_val(
            se_partner["firstname"], "DA002003", "AN"
        )
        if "gender" in se_partner.keys():
            da002 += self.compose_val(
                se_partner["gender"], "DA002004", "AN"
            )
        if "birth_date" in se_partner.keys():
            da002 += self.compose_val(
                se_partner["birth_date"].strftime("%d%m%Y"), "DA002005", "DT"
            )
        if "birth_city" in se_partner.keys():
            da002 += self.compose_val(
                se_partner["birth_city"], "DA002006", "AN"
            )
        if "birth_province" in se_partner.keys():
            da002 += self.compose_val(
                se_partner["birth_province"], "DA002007", "PN"
            )
        da002 += self.compose_val(
            se_partner["special_categories"], "DA002008", "AN"
        )
        da002 += self.compose_val(
            se_partner["exceptional_events"], "DA002009", "NP"
        )
        da002 += self.compose_val(
            se_partner["exclusion_cases"], "DA002010", "N1"
        )
        da002 += self.compose_val(
            codice_stato_estero, "DA002011", "N3"
        )
        da002 += self.compose_val(
            comune_estero, "DA002020", "AN"
        )
        da002 += self.compose_val(
            provincia_estero, "DA002021", "PR"
        )
        da002 += self.compose_val(
            se_partner["domicile_1_city_code"], "DA002023", "AN"
        )
        da002 += self.compose_val(
            se_partner["domicile_1_city_merge_code"], "DA002023", "AN"
        )

        # domicilio_fiscale df
        da002 += self.compose_val(
            se_partner["domicile_2_city"], "DA002024", "AN"
        )
        da002 += self.compose_val(
            se_partner["domicile_2_province"], "DA002025", "AN"
        )
        da002 += self.compose_val(
            se_partner["domicile_2_city_code"], "DA002026", "AN"
        )
        da002 += self.compose_val(
            se_partner["domicile_2_city_merge_code"], "DA002027", "AN"
        )

        cf_rappresentante = ""
        codice_identificazione_fiscale_estero = ""
        localita_residenza_estera = ""
        via_estera = ""
        non_residenti_shumaker = False
        # dati relativi al rappresentante
        da002 += self.compose_val(
            cf_rappresentante, "DA002030", "CF"
        )
        da002 += self.compose_val(
            codice_identificazione_fiscale_estero, "DA002040", "AN"
        )
        da002 += self.compose_val(
            localita_residenza_estera, "DA002041", "AN"
        )
        da002 += self.compose_val(
            via_estera, "DA002042", "AN"
        )
        da002 += self.compose_val(
            non_residenti_shumaker, "DA002043", "CB"
        )
        da002 += self.compose_val(
            codice_stato_estero, "DA002044", "N3"
        )

        firma = True
        statement_date = (
            statement["statement_date"].strftime("%d%m%Y")
            if statement["statement_date"]
            else ""
        )
        da003 = ""
        da003 += self.compose_val(
            statement_date, "DA003001", "DT"
        )
        da003 += self.compose_val(
            firma, "DA003002", "CB"
        )

        da000 = da001 + da002 + da003
        da000 = da000.ljust(1800)[:1800]
        dx10_filler = " " * 8
        dx11_filler = "A"
        return (
            d1_tipo_record
            + d2_cf_sostituto_di_imposta
            + d3_progressivo_modulo
            + d4_cf_percipiente
            + d5_progressivo
            + d6_identificativo_invio
            + d7_progressivo_attribuito
            + d8_spazio_utente
            + d9_annullamento_sostituzione
            + d10_filler
            + d11_conferma_singola
            + da000
            + dx10_filler
            + dx11_filler
            + self._end_line
        )

    def _record_h(self, statement, se_partner, progressivo):
        # record H
        global global_total_record_h
        global_total_record_h += 1

        accumulatore = ""
        progressivo_modulo = 0
        for se_partner_line in se_partner["lines"]:
            progressivo_modulo += 1

            h1_tipo_record = "H"
            h2_cf_sostituto_di_imposta = (
                statement["employer_fiscalcode"].ljust(16)[:16]
            )
            h3_progressivo_modulo = str(int(progressivo_modulo)).rjust(8, "0")
            h4_cf_percipiente = se_partner["fiscalcode"].ljust(16)[:16]
            h5_progressivo = str(int(progressivo)).rjust(5, "0")
            h6_filler = "0" * 17
            h7_spazio = "0" * 6
            h8_filler = " " * 14
            h9_filler = " "
            h10_filler = " " * 4
            h11_filler = "0"

            somme_restituite_al_netto_della_ritenuta_subita = 0.00
            # record H con i rispettivi numeri del modello
            au001 = ""
            au001 += self.compose_val(
                se_partner_line["income_type_code"], "AU001001", "AN"
            )  # causale
            au001 += self.compose_val(
                se_partner_line["year"], "AU001002", "DA"
            )  # anno
            au001 += self.compose_val(
                se_partner_line["anticipation"], "AU001003", "CB"
            )  # anticipazione
            au001 += self.compose_val(
                se_partner_line["amount_total"], "AU001004", "VP"
            )  # ammontare lordo corrisposto
            au001 += self.compose_val(
                se_partner_line["amount_ns_withholding_tax_agreement"],
                "AU001005",
                "VP"
            )  # somme_non_soggette_a_ritenuta_per_regime convenzionale
            au001 += self.compose_val(
                se_partner_line["code"], "AU001006", "NP"
            )  # codice
            au001 += self.compose_val(
                se_partner_line["amount_ns_withholding_tax_other"],
                "AU001007",
                "VP"
            )  # altre somme non soggette a ritenute
            au001 += self.compose_val(
                se_partner_line["amount_untaxed"], "AU001008", "VP"
            )  # imponibile
            au001 += self.compose_val(
                se_partner_line["amount_withholding_tax_deposit"],
                "AU001009",
                "VP"
            )  # ritenute a titolo di acconto
            au001 += self.compose_val(
                se_partner_line["amount_withholding_tax"], "AU001010", "VP"
            )  # ritenute a titolo di imposta
            au001 += self.compose_val(
                se_partner_line["amount_withholding_tax_suspended"],
                "AU001011",
                "VP"
            )  # ritenute sospese
            au001 += self.compose_val(
                se_partner_line["amount_withholding_regional_deposit"],
                "AU001012",
                "VP"
            )  # addizionale regionale a titolo di acconto
            au001 += self.compose_val(
                se_partner_line["amount_withholding_regional"],
                "AU001013",
                "VP"
            )  # addizionale regionale a titolo di imposta
            au001 += self.compose_val(
                se_partner_line["amount_withholding_regional_suspended"],
                "AU001014",
                "VP"
            )  # addizionale regionale sospesa
            au001 += self.compose_val(
                se_partner_line["amount_withholding_municipal_deposit"],
                "AU001015",
                "VP"
            )  # addizionale comunale a titolo di acconto
            au001 += self.compose_val(
                se_partner_line["amount_withholding_municipal"],
                "AU001016",
                "VP"
            )  # addizionale comunale a titolo di imposta
            au001 += self.compose_val(
                se_partner_line["amount_withholding_municipal_suspended"],
                "AU001017",
                "VP",
            )  # addizionale comunale sospesa
            au001 += self.compose_val(
                se_partner_line["amount_untaxed_previous_years"],
                "AU001018",
                "VP"
            )  # imponibile anni precedenti
            au001 += self.compose_val(
                se_partner_line["amount_withholding_previous_years"],
                "AU001019",
                "VP"
            )  # ritenute operate anni precedenti
            au001 += self.compose_val(
                se_partner_line["amount_expenses_refunded"], "AU001020", "VP"
            )  # spese rimborsate
            au001 += self.compose_val(
                se_partner_line["amount_withholding_refunded"],
                "AU001021",
                "VP"
            )  # ritenute rimborsate
            au001 += self.compose_val(
                somme_restituite_al_netto_della_ritenuta_subita,
                "AU001022",
                "VP"
            )
            au001 += self.compose_val(
                se_partner_line["social_security_office_fiscalcode"],
                "AU001029",
                "CN"
            )  # codice fiscale ente previdenziale
            au001 += self.compose_val(
                se_partner_line["social_security_office_name"],
                "AU001030",
                "AN"
            )  # denominazione ente previdenziale
            au001 += self.compose_val(
                se_partner_line["company_code"], "AU001032", "AN"
            )  # codice azienda
            au001 += self.compose_val(
                se_partner_line["category"], "AU001033", "AN"
            )  # categoria
            au001 += self.compose_val(
                se_partner_line[
                    "employer_contributions_social_security_payments"
                ],
                "AU001034",
                "VN"
            )  # contributi previdenziali a carico del soggetto erogante
            au001 += self.compose_val(
                se_partner_line[
                    "partner_contributions_social_security_payments"
                ],
                "AU001035",
                "VN"
            )  # contributi previdenziali a carico del percipiente
            au001 += self.compose_val(
                se_partner_line["other_contributions"], "AU001036", "CB"
            )  # altri contributi
            au001 += self.compose_val(
                se_partner_line["other_contributions_amount"], "AU001037", "VN"
            )  # importo altri contributi
            au001 += self.compose_val(
                se_partner_line["contributions_due"], "AU001038", "VN"
            )  # contributi dovuti
            au001 += self.compose_val(
                se_partner_line["contributions_paid"], "AU001039", "VN"
            )  # contributi versati

            au001 = au001.ljust(1800)[:1800]
            hx10_filler = " " * 8
            hx11_filler = "A"
            accumulatore += (
                h1_tipo_record
                + h2_cf_sostituto_di_imposta
                + h3_progressivo_modulo
                + h4_cf_percipiente
                + h5_progressivo
                + h6_filler
                + h7_spazio
                + h8_filler
                + h9_filler
                + h10_filler
                + h11_filler
                + au001
                + hx10_filler
                + hx11_filler
                + self._end_line
            )
        return accumulatore

    def _record_z(self):
        # record Z
        global global_total_record_b, global_total_record_d, global_total_record_h

        z1_tipo_record = "Z"
        z2_filler = " " * 14
        z3_numero_record_b = str(global_total_record_b).rjust(9, "0")
        z4_numero_record_c = str("0").rjust(9, "0")
        z5_numero_record_d = str(global_total_record_d).rjust(9, "0")
        z6_numero_record_g = str("0").rjust(9, "0")
        z7_numero_record_h = str(global_total_record_h).rjust(9, "0")
        z8_numero_record_l = str("0").rjust(9, "0")
        z9_filler = " " * 9
        z10_filler = " " * 9
        z11_filler = " " * 1810
        zx11_filler = "A"
        return (
            z1_tipo_record
            + z2_filler
            + z3_numero_record_b
            + z4_numero_record_c
            + z5_numero_record_d
            + z6_numero_record_g
            + z7_numero_record_h
            + z8_numero_record_l
            + z9_filler
            + z10_filler
            + z11_filler
            + zx11_filler
            + self._end_line
        )

    def _crea_file(self, statement, se_partners):
        accumulatore = self._record_a(statement)
        accumulatore += self._record_b(statement)
        if all(
            se_partner["id"].state not in ["cancelled", "substitution"]
            for se_partner in se_partners
        ):
            statement["id"].record_ab_txt = accumulatore.upper()
        progressivo = 0
        for se_partner in se_partners:
            progressivo += 1
            record_d = self._record_d(statement, se_partner, progressivo)
            record_h = ""
            if se_partner["id"].state not in ["cancelled", "substitution"]:
                record_h = self._record_h(statement, se_partner, progressivo)
                se_partner["id"].record_dh_txt = record_d.upper() + record_h.upper()
            accumulatore += record_d + record_h
        accumulatore += self._record_z()
        return accumulatore.upper()

    def action_export_cu_2023(self):
        global global_cu_number

        active_ids = self.env.context.get("active_ids", [])
        statement_id = self.env["account.cu.statement"].browse(active_ids)[0]
        global_cu_number = len(statement_id.certification_se_lines_ids)
        if len(statement_id.delegate_commitment) > 1:
            raise UserError(
                _("Commitment to submit statement electronically not valid!")
            )
        if not statement_id.delegate_fiscalcode:
            raise UserError(_("Delegate Fiscalcode missing!"))
        if not statement_id.employer_fiscalcode:
            raise UserError(_("Employer Fiscalcode missing!"))
        if not statement_id.employer_lastname:
            raise UserError(_("Employer Lastname missing!"))
        if any(
            se_partner.state == "draft"
            for se_partner in statement_id.certification_se_lines_ids
        ):
            raise UserError(_("Any certification line are in 'draft' state!"))

        statement = {
            "id": statement_id,
            "employer_address": statement_id.employer_address or "",
            "employer_ateco_id": statement_id.employer_ateco_id.code or "",
            "employer_city": statement_id.employer_city or "",
            "employer_email": statement_id.employer_email or "",
            "employer_firstname": statement_id.employer_firstname or "",
            "employer_fiscalcode": statement_id.employer_fiscalcode,
            "employer_headquarters": statement_id.employer_headquarters or "",
            "employer_lastname": statement_id.employer_lastname,
            "employer_phone": statement_id.employer_phone or "",
            "employer_province": statement_id.employer_province or "",
            "employer_zip": statement_id.employer_zip or "",
            "statement_date": statement_id.statement_date or "",
            "taxpayer_sign": statement_id.taxpayer_sign or "",
            "taxpayer_lastname": statement_id.taxpayer_lastname or "",
            "taxpayer_firstname": statement_id.taxpayer_firstname or "",
            "taxpayer_fiscalcode": statement_id.taxpayer_fiscalcode or "",
            "delegate_sign": statement_id.delegate_sign or "",
            "delegate_fiscalcode": statement_id.delegate_fiscalcode,
            "delegate_date": statement_id.delegate_date or "",
            "delegate_commitment": statement_id.delegate_commitment or "1",
            "name": statement_id.name or "",
            "supply_code": statement_id.statement_type_id.supply_code or "",
            "cancelled": (
                "1"
                if any(
                    se_partner.state == "cancelled"
                    for se_partner in statement_id.certification_se_lines_ids
                )
                else "0"
            ),
            "substitution": (
                "1"
                if any(
                    se_partner.state == "substitution"
                    for se_partner in statement_id.certification_se_lines_ids
                )
                else "0"
            ),
        }
        se_partners_list = []
        for se_partner in statement_id.certification_se_lines_ids:
            try:
                exceptional_events = int(se_partner.exceptional_events)
            except BaseException:
                raise UserError(
                    _(
                        "Exceptional events not valid! %s",
                        se_partner.partner_id.display_name
                    )
                )
            try:
                exclusion_cases = float(se_partner.exclusion_cases)
            except BaseException:
                raise UserError(
                    _(
                        "Exclusion Cases not valid! %s",
                        se_partner.partner_id.display_name
                    )
                )
            se_partner_dict = {
                "id": se_partner,
                "amount_total": se_partner.amount_total or 0.00,
                "amount_ns_withholding_tax_other": (
                    se_partner.amount_ns_withholding_tax_other or 0.0
                ),
                "amount_untaxed": se_partner.amount_untaxed or 0.0,
                "amount_withholding_tax_deposit": (
                    se_partner.amount_withholding_tax_deposit or 0.0
                ),
                "exceptional_events": exceptional_events or 0,
                "domicile_1_city": se_partner.domicile_1_city or "",
                "domicile_1_city_code": se_partner.domicile_1_city_code or "",
                "domicile_1_city_merge_code": (
                    se_partner.domicile_1_city_merge_code or ""
                ),
                "domicile_1_province": se_partner.domicile_1_province or "",
                "domicile_2_city": se_partner.domicile_2_city or "",
                "domicile_2_city_code": se_partner.domicile_2_city_code or "",
                "domicile_2_city_merge_code": (
                    se_partner.domicile_2_city_merge_code or ""
                ),
                "domicile_2_province": se_partner.domicile_2_province or "",
                "exclusion_cases": exclusion_cases or 0.0,
                "firstname": se_partner.firstname or "",
                "fiscalcode": se_partner.fiscalcode or "",
                "lastname": se_partner.lastname or "",
                "special_categories": se_partner.special_categories or "",
                "ade_protocol": se_partner.ade_protocol or "0" * 17,
                "ade_sequence": se_partner.ade_sequence or "0" * 6,
                "ade_operation": (
                    se_partner.ade_operation
                    if se_partner.ade_operation in ["A", "S"]
                    else " "
                ),
            }
            if (
                se_partner.gender
                or se_partner.birth_date
                or se_partner.birth_city
                or se_partner.birth_province
            ):
                if se_partner.gender:
                    if se_partner.gender == "male":
                        se_partner_dict["gender"] = "M"
                    elif se_partner.gender == "female":
                        se_partner_dict["gender"] = "F"
                    else:
                        raise UserError(
                            _(
                                "Gender not valid! %s",
                                se_partner.partner_id.display_name
                            )
                        )
                else:
                    raise UserError(
                        _("Gender missing! %s" % se_partner.partner_id.display_name)
                    )
                if se_partner.birth_date:
                    se_partner_dict["birth_date"] = se_partner.birth_date
                else:
                    raise UserError(
                        _(
                            "Birth Date missing! %s",
                            se_partner.partner_id.display_name
                        )
                    )
                if se_partner.birth_city:
                    se_partner_dict["birth_city"] = se_partner.birth_city
                else:
                    raise UserError(
                        _(
                            "Birth City missing! %s",
                            se_partner.partner_id.display_name
                        )
                    )
                if se_partner.birth_province:
                    se_partner_dict["birth_province"] = se_partner.birth_province
                else:
                    raise UserError(
                        _(
                            "Birth Province missing! %s",
                            se_partner.partner_id.display_name
                        )
                    )
            se_partner_lines_list = []
            for se_partner_line in se_partner.line_ids:
                try:
                    code = int(se_partner_line.code if se_partner_line.code else 0)
                except BaseException:
                    raise UserError(
                        _("Code not valid! %s" % se_partner.partner_id.display_name)
                    )
                se_partner_line_dict = {
                    "income_type_code": se_partner_line.income_type_code or "",
                    "year": (
                        se_partner_line.year
                        or se_partner.statement_id.statement_type_id.income_year
                    ),
                    "anticipation": se_partner_line.anticipation or False,
                    "amount_total": se_partner_line.amount_total or 0.0,
                    "amount_ns_withholding_tax_agreement": (
                        se_partner_line.amount_ns_withholding_tax_agreement or 0.00
                    ),
                    "code": code or 0,
                    "amount_ns_withholding_tax_other": (
                        se_partner_line.amount_ns_withholding_tax_other or 0.00
                    ),
                    "amount_untaxed": se_partner_line.amount_untaxed or 0.00,
                    "amount_withholding_tax_deposit": (
                        se_partner_line.amount_withholding_tax_deposit or 0.00
                    ),
                    "amount_withholding_tax": (
                        se_partner_line.amount_withholding_tax or 0.00
                    ),
                    "amount_withholding_tax_suspended": (
                        se_partner_line.amount_withholding_tax_suspended or 0.00
                    ),
                    "amount_withholding_regional_deposit": (
                        se_partner_line.amount_withholding_regional_deposit or 0.00
                    ),
                    "amount_withholding_regional": (
                        se_partner_line.amount_withholding_regional or 0.00
                    ),
                    "amount_withholding_regional_suspended": (
                        se_partner_line.amount_withholding_regional_suspended or 0.00
                    ),
                    "amount_withholding_municipal_deposit": (
                        se_partner_line.amount_withholding_municipal_deposit or 0.00
                    ),
                    "amount_withholding_municipal": (
                        se_partner_line.amount_withholding_municipal or 0.00
                    ),
                    "amount_withholding_municipal_suspended": (
                        se_partner_line.amount_withholding_municipal_suspended or 0.00
                    ),
                    "amount_untaxed_previous_years": (
                        se_partner_line.amount_untaxed_previous_years or 0.00
                    ),
                    "amount_withholding_previous_years": (
                        se_partner_line.amount_withholding_previous_years or 0.00
                    ),
                    "amount_expenses_refunded": (
                        se_partner_line.amount_expenses_refunded or 0.00
                    ),
                    "amount_withholding_refunded": (
                        se_partner_line.amount_withholding_refunded or 0.00
                    ),
                    "social_security_office_fiscalcode": (
                        se_partner_line.social_security_office_fiscalcode or ""
                    ),
                    "social_security_office_name": (
                        se_partner_line.social_security_office_name or ""
                    ),
                    "company_code": se_partner_line.company_code or "",
                    "category": (
                        se_partner_line.category_id
                        and se_partner_line.category_id.name
                        or ""
                    ),
                    "employer_contributions_social_security_payments": (
                        se_partner_line.employer_contributions_social_security_payments
                        or 0.00
                    ),
                    "partner_contributions_social_security_payments": (
                        se_partner_line.partner_contributions_social_security_payments
                        or 0.00
                    ),
                    "other_contributions": (
                        se_partner_line.other_contributions or False
                    ),
                    "other_contributions_amount": (
                        se_partner_line.other_contributions_amount or 0.00
                    ),
                    "contributions_due": se_partner_line.contributions_due or 0.00,
                    "contributions_paid": se_partner_line.contributions_paid or 0.00,
                }
                se_partner_lines_list.append(se_partner_line_dict)
            se_partner_dict["lines"] = se_partner_lines_list
            se_partners_list.append(se_partner_dict)

        out = base64.encodebytes(
            self._crea_file(
                statement, se_partners_list
            ).encode("ascii", errors="replace")
        )

        self.write(
            {
                "state": "get",
                "cu_txt": out,
                "file_name": "TC_%s_000001.txt" % fields.Datetime.now().strftime("%Y%m%d"),
            }
        )

        view_id = self.env.ref("l10n_it_cu_report_2023.wizard_cu_file_export_2023_view")
        return {
            "view_type": "form",
            "view_id": view_id.id,
            "view_mode": "form",
            "res_model": "cu.file.export.2023",
            "res_id": self.id,
            "type": "ir.actions.act_window",
            "target": "new",
        }

    state = fields.Selection(
        [
            ("choose", "choose"),  # choose accounts
            ("get", "get"),  # get the file
        ],
        default="choose",
    )
    cu_txt = fields.Binary("File", readonly=True)
    file_name = fields.Char("File Name", readonly=True)
