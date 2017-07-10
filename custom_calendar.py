# -*- coding: utf-8 -*-
##############################################################################
#    
# Module : custom_calendar_event
# Créé le : 2016-08-06 par Maxime LEPILLIEZ
#
# Module permettant de customiser le calendrier
#
##############################################################################

import openerp
from openerp import models, fields, api, tools
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, orm, expression
from datetime import datetime, date, timedelta
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser
from openerp.exceptions import Warning, UserError
from openerp.osv.expression import get_unaccent_wrapper
from openerp.tools.translate import _
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


GRP_SANG_SELECTION = [
    ('O+', 'O+'), ('O-', 'O-'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-')
]

SEXE_SELECTION = [
    ('masculin', 'Masc.'), ('feminin', 'Fem.')
]

DEFAULT_x_bebe_mesures = """Taille (cm) : 

Poids (kg) : 

PC (cm) : 
"""
    
DEFAULT_x_bebe_mobilite = """Tonus : 

Motricité : 
"""

DEFAULT_x_bebe_exam = """Teint : 

Exam. cardio-vasc. : 

Abdomen : 

Transit : 

Dents : 

Alimentation : 
"""

DEFAULT_x_gyneco_1 = """DDR : 

Cycle : 

Contraception : 
"""

DEFAULT_x_gyneco_2 = """TA : 

pls : 
"""

DEFAULT_x_gyneco_3 = """Date dernier FCU : 

Nombre lames : 

Aspect col : 

Résultat : 
"""

DEFAULT_x_gyneco_4 = """TV : 

Pertes : 
"""

DEFAULT_x_gyneco_5 = """Examen abdominal : 

Examen des seins : 
"""

DEFAULT_x_gyneco_6 = """Conduite à tenir : 

Traitement : 

Bilan bio : 
"""

DEFAULT_x_gross_1 = """TA : 

pls : 
"""

DEFAULT_x_gross_2 = """Urinaires : 

Digestifs : 

Hypertenion : 
"""

DEFAULT_x_gross_3 = """RCF : 

CU : 

MFA : 
"""

DEFAULT_x_gross_4 = """Conduite à tenir : 

Traitement : 

Bilan bio : 
"""





class custom_calendar_event_type(osv.osv):
    _name = 'calendar.event.type'
    _inherit = 'calendar.event.type'
    _columns = {
        'x_code_acte': fields.char('Code acte', size=8),
        'x_price_acte': fields.float('Prix acte', digits=(4,0)),
        
    }



class custom_calendar_event(osv.osv):
    _name = "calendar.event"
    _inherit = 'calendar.event'

    # @api.one  
    @api.depends('x_event_ddr', 'start_datetime')
    def _compute_ag(self):
        ddr = self.x_event_ddr
        event_date = self.start_datetime
        if ddr:
            x_ddr = datetime.strptime(ddr, "%Y-%m-%d")
            x_event_date = datetime.strptime(event_date, "%Y-%m-%d %H:%M:%S")
            # r = relativedelta.relativedelta(x_event_date, x_ddr)
            # self.x_event_ag = r.weeks
            x_nb_weeks = (abs((x_event_date - x_ddr).days))/7
            x_nb_days = abs((x_event_date - x_ddr).days) - (x_nb_weeks*7)
            if x_nb_weeks!=0 and x_nb_days!=0:
                self.x_event_ag = str(x_nb_weeks)+' semaine(s) et '+str(x_nb_days)+' jour(s)'
            elif x_nb_weeks!=0:
                self.x_event_ag = str(x_nb_weeks)+' semaine(s)'
            elif x_nb_days!=0:
                self.x_event_ag = str(x_nb_days)+' jour(s)'
            else:
                self.x_event_ag = ''
        else:
            self.x_event_ag = ''


    @api.depends('x_categ_id','x_partner_id')
    def _compute_categ_id_char(self):
        self.x_categ_id_char = self.x_categ_id.name
        if self.x_categ_id_char and self.x_partner_id.display_name and self.x_partner_id.phone:
            self.name = self.x_categ_id_char+' : '+self.x_partner_id.display_name+', '+self.x_partner_id.phone
        elif self.x_categ_id_char and self.x_partner_id.display_name:
            self.name = self.x_categ_id_char+' : '+self.x_partner_id.display_name
        elif self.x_partner_id.display_name:
            self.name = self.x_partner_id.display_name
        elif self.x_categ_id_char:
            self.name = self.x_categ_id_char
        else:
            self.name = ''

    @api.one
    @api.depends('x_event_ddr')
    def _get_dg_tp(self):
        x_ddr = self.x_event_ddr
        if x_ddr:
            ddr = datetime.strptime(x_ddr, "%Y-%m-%d")#"%m/%d/%y")
            self.x_event_dg = ddr + timedelta(days=14)
            self.x_event_tp = ddr + timedelta(days=287)
            
    _columns = {
        'x_domicile': fields.boolean('A domicile'),
        'x_partner_id': fields.many2one('res.partner', 'Attendee', default=''),
        # 'x_name': fields.char("Titre de l'évènement2", size=64),
        'x_categ_id': fields.many2one('calendar.event.type', 'Tags'),
        'x_categ_id_char': fields.char(compute='_compute_categ_id_char', default=''),
        'x_event_is_billed': fields.boolean('is_billed'),
        'x_event_is_printed': fields.boolean('is_printed'),
        # 'x_partner_id_2': fields.function(_function_x_partner_id, type='many2one', relation='res.partner', string='Attendee', store=True),

        # Consult. Prepa
        # -------------------------
        'x_prepa_note': fields.text('Prépa'),

        # Consult. RP
        # -------------------------
        'x_rp_methode': fields.text('Méthode'),
        'x_rp_progression': fields.text('Progression'),


        # Consult. Bébé
        # -------------------------
        'x_bebe_mesures': fields.text('Mesures', default=DEFAULT_x_bebe_mesures),
        'x_bebe_mobilite': fields.text('Mobilité', default=DEFAULT_x_bebe_mobilite),
        'x_bebe_exam': fields.text('Examen', default=DEFAULT_x_bebe_exam),
        'x_event_conduite': fields.text('Consuite à tenir'),
        'x_event_traitement': fields.text('Examen'),
        'x_event_bilanbio': fields.text('Bilan bio.'),


        # Consult. Gynéco
        # -------------------------
        'x_gyneco_motif': fields.char('Motif de consult.', size=64),
        'x_gyneco_1': fields.text('x_gyneco_1', default=DEFAULT_x_gyneco_1),
        'x_gyneco_2': fields.text('x_gyneco_2', default=DEFAULT_x_gyneco_2),
        'x_gyneco_3': fields.text('x_gyneco_3', default=DEFAULT_x_gyneco_3),
        'x_gyneco_4': fields.text('x_gyneco_4', default=DEFAULT_x_gyneco_4),
        'x_gyneco_5': fields.text('x_gyneco_5', default=DEFAULT_x_gyneco_5),
        'x_gyneco_6': fields.text('x_gyneco_6', default=DEFAULT_x_gyneco_6),


        # Consult. Grossesse
        # -------------------------
        'x_gross_motif': fields.char('Motif de consult.', size=64),
        'x_event_ag' : fields.char(string='AG', compute='_compute_ag'),
        'x_gross_1': fields.text('x_gross_1', default=DEFAULT_x_gross_1),
        'x_gross_2': fields.text('Signes fonctionnels', default=DEFAULT_x_gross_2),
        'x_gross_OMI': fields.char('OMI', size=64),
        'x_gross_tigette': fields.char('Tigette', size=64),
        'x_gross_h_uterine': fields.char('Haut. utérine', size=64),
        'x_gross_presentation': fields.char('Présentation', size=64),
        'x_gross_3': fields.text('Toucher vaginal', default=DEFAULT_x_gross_3),
        'x_gross_4': fields.text('x_gross_4', default=DEFAULT_x_gross_4),


        # related field res.partner 
        # -------------------------
        'x_event_display_name' : fields.related('x_partner_id', 'display_name', type="char"),
        'x_event_name' : fields.related('x_partner_id', 'name', type="char"),
        'x_event_phone' : fields.related('x_partner_id', 'phone', type="char", default=''),
        'x_event_patient_prenom': fields.related('x_partner_id', 'x_patient_prenom', type="char"),
        'x_event_patient_sexe': fields.related('x_partner_id', 'x_patient_sexe', type="selection", selection=SEXE_SELECTION),
        'x_event_patient_cafat': fields.related('x_partner_id', 'x_patient_cafat', type="char"),
        'x_event_dob': fields.date(related='x_partner_id.dob'),
        'x_event_age' : fields.integer(related='x_partner_id.age'),
        'x_event_src_avatar' : fields.binary(related='x_partner_id.x_src_avatar'),
        'x_event_medecin_traitant': fields.char(related='x_partner_id.x_medecin_traitant'),
        'x_event_groupe_sang': fields.related('x_partner_id', 'x_groupe_sang', type="selection", selection=GRP_SANG_SELECTION),
        'x_event_taille': fields.float(related='x_partner_id.x_taille'),
        'x_event_poids': fields.float(related='x_partner_id.x_poids'),
        'x_event_IMC': fields.float(related='x_partner_id.x_IMC'),
        'x_event_context': fields.text(related='x_partner_id.x_context'),
        'x_event_familiaux': fields.text(related='x_partner_id.x_familiaux'),
        'x_event_ant_obst_ids': fields.related('x_partner_id', 'x_ant_obst_ids', type="one2many"),
        'x_event_questionnaire_rp': fields.text(related='x_partner_id.x_questionnaire_rp'),
        'x_event_chirurgicaux': fields.text(related='x_partner_id.x_chirurgicaux'),
        'x_event_gyneco': fields.text(related='x_partner_id.x_gyneco'),
        'x_event_obstetrique': fields.text(related='x_partner_id.x_obstetrique'),
        'x_event_allergies': fields.text(related='x_partner_id.x_allergies'),
        'x_event_addictions': fields.text(related='x_partner_id.x_addictions'),
        'x_event_exam_rp': fields.text(related='x_partner_id.x_exam_rp'),
        'x_event_atcd_marquants': fields.text(related='x_partner_id.x_atcd_marquants'),
        'x_event_contexte_epp': fields.text(related='x_partner_id.x_contexte_epp'),
        'x_event_projet_naissance': fields.text(related='x_partner_id.x_projet_naissance'),
        'x_event_ressentis': fields.text(related='x_partner_id.x_ressentis'),
        'x_event_medicaux': fields.text(related='x_partner_id.x_medicaux'),
        'x_gross_ids': fields.related('x_partner_id', 'x_info_grossesse_ids', type="one2many"),
        'x_event_ddr' : fields.related('x_partner_id', 'x_partner_gross_ddr', type="date", string="DDR", help="Les grossesses doivent être enregistrées depuis l'onglet 'Grossesse(s)' de la vue Patiente"),
        'x_event_tp': fields.date(string='TP', readonly=True, compute=_get_dg_tp),
        'x_event_dg': fields.date(string='DG', readonly=True, compute=_get_dg_tp),
        # Vaccins BCG
        'x_event_BCG_N': fields.boolean(related='x_partner_id.x_BCG_N'),
        # Vaccins DTP
        'x_event_DTP_2m': fields.boolean(related='x_partner_id.x_DTP_2m'),
        'x_event_DTP_4m': fields.boolean(related='x_partner_id.x_DTP_4m'),
        'x_event_DTP_11m': fields.boolean(related='x_partner_id.x_DTP_11m'),
        'x_event_DTP_6a': fields.boolean(related='x_partner_id.x_DTP_6a'),
        'x_event_DTP_1113a': fields.boolean(related='x_partner_id.x_DTP_1113a'),
        'x_event_DTP_25': fields.boolean(related='x_partner_id.x_DTP_25'),
        'x_event_DTP_45': fields.boolean(related='x_partner_id.x_DTP_45'),
        # Vaccins Coqueluche
        'x_event_coq_2m': fields.boolean(related='x_partner_id.x_coq_2m'),
        'x_event_coq_4m': fields.boolean(related='x_partner_id.x_coq_4m'),
        'x_event_coq_11m': fields.boolean(related='x_partner_id.x_coq_11m'),
        'x_event_coq_6a': fields.boolean(related='x_partner_id.x_coq_6a'),
        'x_event_coq_1113a': fields.boolean(related='x_partner_id.x_coq_1113a'),
        'x_event_coq_25': fields.boolean(related='x_partner_id.x_coq_25'),
        'x_event_coq_45': fields.boolean(related='x_partner_id.x_coq_45'),
        # Vaccins HIB
        'x_event_HIB_2m': fields.boolean(related='x_partner_id.x_HIB_2m'),
        'x_event_HIB_4m': fields.boolean(related='x_partner_id.x_HIB_4m'),
        'x_event_HIB_11m': fields.boolean(related='x_partner_id.x_HIB_11m'),
        # Vaccins HepB
        'x_event_HepB_2m': fields.boolean(related='x_partner_id.x_HepB_2m'),
        'x_event_HepB_4m': fields.boolean(related='x_partner_id.x_HepB_4m'),
        'x_event_HepB_11m': fields.boolean(related='x_partner_id.x_HepB_11m'),
        # Vaccins Pneumocoque
        'x_event_pneumo_2m': fields.boolean(related='x_partner_id.x_pneumo_2m'),
        'x_event_pneumo_4m': fields.boolean(related='x_partner_id.x_pneumo_4m'),
        'x_event_pneumo_11m': fields.boolean(related='x_partner_id.x_pneumo_11m'),
        # Vaccins Meningocoque C
        'x_event_meningo_11m': fields.boolean(related='x_partner_id.x_meningo_11m'),
        # Vaccins ROR
        'x_event_ROR_12m': fields.boolean(related='x_partner_id.x_ROR_12m'),
        'x_event_ROR_1618m': fields.boolean(related='x_partner_id.x_ROR_1618m'),
        # Vaccins HPV
        'x_event_HPV_1113m': fields.boolean(related='x_partner_id.x_HPV_1113m'),
        'x_event_HPV_14m': fields.boolean(related='x_partner_id.x_HPV_14m'),
        # Vaccins Grippe
        
        # related field calendar_event_type 
        # -------------------------
        'x_event_codeActe': fields.char(related='x_categ_id.x_code_acte', size=8),
        'x_event_priceActe': fields.float(related='x_categ_id.x_price_acte', digits=(4,0)),
        # 'x_gross_ids': fields.one2many(related='x_partner_id.x_info_grossesse_ids', string = "Grossesse(s)")
        # -------------------------
    }
    _default = {
        'x_domicile': False,
    }

    @api.multi
    def write(self, vals):

        vals['x_event_ag'] = self.x_event_ag
        result = super(custom_calendar_event, self).write(vals)
        vals['x_event_ag'] = self.x_event_ag
        result = super(custom_calendar_event, self).write(vals)
        
        return result

custom_calendar_event()