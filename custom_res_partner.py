# -*- coding: utf-8 -*-
##############################################################################
#    
# Module : custom_res_partner
# Créé le : 2016-08-06 par Maxime LEPILLIEZ
#
# Module permettant de gérer les Users
#
##############################################################################

from __future__ import division
import openerp
from openerp import models, fields, api, tools
from openerp.osv import fields, osv, orm, expression
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser
from openerp.exceptions import Warning, UserError
from openerp.osv.expression import get_unaccent_wrapper
from openerp.tools.translate import _
from lxml import etree
import math
import pytz
import threading
import urlparse

GRP_SANG_SELECTION = [
    ('O+', 'O+'), ('O-', 'O-'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-')
]
GROSS_NUM_SELECTION = [
    ('1', '1ère gross.'), ('2', '2ème gross.'), ('3', '3ème gross.'), ('4', '4ème gross.'), ('5', '5ème gross.'), ('6', '6ème gross.'), ('7', '7ème gross.'), ('8', '8ème gross.'), ('9', '9ème gross.'), ('10', '10ème gross.')
]
SEXE_SELECTION = [
    ('masculin', 'Masc.'), ('feminin', 'Fem.')
]

CONVENTION_SELECTION = [
    ('cafat', 'CAFAT'), ('am_sud', 'AM Sud'), ('am_nord', 'AM Nord'), ('am_iles', 'AM Iles'), ('autre','Autre')
]

DEFAULT_x_questionnaire_rp = """Sport : 

Algies dorsales : 

Sciatiques : 

ATCD rééduc. : 

Incontinence urinaire : 

Algies pelviennes : 

Pesanteur : 

Incontinence anale : 

Rapports sexuels : 

Contraception : 

Perte de poids : 

Retour de couche : 
"""

DEFAULT_x_obstetrique = """Gestité : 

Parité : 

FCS : 

IVG : 
"""

DEFAULT_x_addictions = """Tabac : 

Alcool : 

Drogues : 
"""

DEFAULT_x_exam_rp = """TV : 

Vulve : 

Cicatrice : 

Bassin : 

Abdominaux : 

Tonus : 
"""

DEFAULT_x_medicaux = """Hep B : 

Hep C : 

TPHA / VDRL : 

HIV : 

Toxoplasmose : 

Raï : 

Rubéole : 

Test OMS : 

HT21 : 
"""



class antecedent_obst(osv.osv):
    _name = "antecedent.obst"
    _description = 'Antécédents obstrétriques'
    _columns = {
        'id': fields.integer('ID'),
        'partner_id': fields.many2one('res.partner', 'Partner ID', ondelete='cascade'),
        'x_obst_date': fields.date('Date'),
        'x_obst_lieu': fields.char('Lieu', size=16),
        'x_obst_gross': fields.char('Gross.', size=16),
        'x_obst_acc': fields.char('Acc.', size=16),
        'x_obst_sexe': fields.char('Sexe', size=8),
        'x_obst_poids': fields.char('Poids', size=8),
        'x_obst_allait': fields.char('Allait.', size=8),
        'x_obst_etat': fields.char('Etat', size=16),
    }
antecedent_obst()


class info_grossesse(osv.osv):
    _name = "info.grossesse"
    _description = 'Grossesse(s)'

    @api.one
    @api.depends('x_gross_tp')
    def _get_dg_ddr(self):
        x_tp = self.x_gross_tp
        tp = datetime.strptime(x_tp, "%Y-%m-%d")#"%m/%d/%y")
        self.x_gross_dg = tp - timedelta(days=273)
        self.x_gross_ddr = tp - timedelta(days=287)

    _columns = {
        'id': fields.integer('ID'),
        'partner_id': fields.many2one('res.partner', 'Partner ID', ondelete='cascade'),
        'x_gross_num': fields.selection(GROSS_NUM_SELECTION, string='Gross.'),
        'x_gross_tp': fields.date(string='TP', default=datetime.now()),
        'x_gross_dg': fields.date(string='DG', readonly=True, compute=_get_dg_ddr),
        'x_gross_ddr': fields.date(string='DDR', readonly=True, compute=_get_dg_ddr),
    }

    _default = {
    }
info_grossesse()

class custom_res_partner(osv.osv):
    _name = "res.partner"
    _inherit = 'res.partner'

    def _x_opportunity_meeting_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x,{'x_opportunity_count': 0, 'x_meeting_count': 0}), ids))
        # the user may not have access rights for opportunities or meetings
        try:
            for partner in self.browse(cr, uid, ids, context):
                if partner.is_company:
                    operator = 'child_of'
                else:
                    operator = '='
                opp_ids = self.pool['crm.lead'].search(cr, uid, [('partner_id', operator, partner.id), ('type', '=', 'opportunity'), ('probability', '<', '100')], context=context)
                res[partner.id] = {
                    'x_opportunity_count': len(opp_ids),
                    'x_meeting_count': len(partner.x_meeting_ids),
                }
        except:
            pass
        return res

    # @api.multi
    # def _compute_IMC(self):
    #     for record in self: 
    #         # record.x_IMC= ((record.x_poids) / (record.x_taille / 100)*(record.x_taille / 100))
    #         record.x_IMC= '1'
    @api.one
    @api.depends('x_poids','x_taille') 
    def _compute_IMC(self):
        if self.x_taille == 0:
            self.x_IMC = '0'
        else:
            self.x_IMC = self.x_poids / ((self.x_taille / 100) * (self.x_taille / 100))
  
    @api.one
    @api.depends('name', 'x_patient_prenom')
    def _compute_display_name(self):
        if self.x_patient_prenom == '':
            names = [self.name]
        else:
            names = [self.name, self.x_patient_prenom]
        self.display_name = ' '.join(filter(None, names))


    _columns = {
        'partner_id' : fields.many2one('res.partner','Customer', default=lambda self: self.env.user.partner_id),
        'display_name' : fields.char(string='Name', compute='_compute_display_name'),
        'x_patient_prenom': fields.char('Prénom', size=16),
        'x_patient_sexe': fields.selection(SEXE_SELECTION, string='Sexe'),
        'x_convention_type': fields.selection(CONVENTION_SELECTION, string='Protection'),
        'x_patient_cafat': fields.char(string='Numéro assuré', size=8, help='Numéro CAFAT du patient'),
        'x_is_pro': fields.boolean('is_pro_bool', help="Check if the contact is a professional, otherwise it is a patient"),
        'x_compte_type': fields.selection(selection=[('patient', 'Patient'), ('pro', 'Pro')], string='Type compte'),
        'dob': fields.date('Date de naissance'),
        'age' : fields.integer('Age'),
        'x_src_avatar' : fields.binary("x_src_avatar", attachment=True,
            help="This field holds the image used as avatar for this contact, limited to 1024x1024px"),
        'x_medecin_traitant': fields.char('Médecin traitant', size=32),
        'x_groupe_sang': fields.selection(GRP_SANG_SELECTION, string='Groupe sang.'),
        'x_taille': fields.float('Taille (cm)',digits=(4,6)),
        'x_poids': fields.float('Poids (kg)',digits=(4,6)),
        'x_IMC': fields.float(string='IMC', compute='_compute_IMC',digits=(4,6)),
        'x_context': fields.text('Contexte social'),
        'x_familiaux': fields.text('Antécédents familiaux'),
        'x_info_grossesse_ids': fields.one2many('info.grossesse', 'partner_id', 'Grossesse(s)', auto_join=True),
        'x_ant_obst_ids': fields.one2many('antecedent.obst', 'partner_id', 'Antécédents obtsétricaux', auto_join=True),
        'x_questionnaire_rp': fields.text('Questionnaire RP', default=DEFAULT_x_questionnaire_rp),
        'x_chirurgicaux': fields.text('Antécédents chirurgicaux'),
        'x_gyneco': fields.text('Antécédents gyneco'),
        'x_obstetrique': fields.text('Antécédents obstétricaux', default=DEFAULT_x_obstetrique),
        'x_allergies': fields.text('Allergies'),
        'x_addictions': fields.text('Addictions', default=DEFAULT_x_addictions),
        'x_exam_rp': fields.text('Examen RP', default=DEFAULT_x_exam_rp),
        'x_atcd_marquants': fields.text('Antécédents marquants', default="Antécédents marquants :"),
        'x_contexte_epp': fields.text('Contexte social & familial', default="Contexte social & familial :"),
        'x_projet_naissance': fields.text('Projet de naissance', default="Projet de naissance :"),
        'x_ressentis': fields.text('Ressentis', default="Ressentis :"),
        'x_medicaux': fields.text('Antécédents médicaux', default=DEFAULT_x_medicaux),
        'x_partner_gross_ddr': fields.date('DDR gross. actuelle'),
        # Vaccins BCG
        'x_BCG_N': fields.boolean('x_BCG_N'),
        # Vaccins DTP
        'x_DTP_2m': fields.boolean('x_DTP_2m'),
        'x_DTP_4m': fields.boolean('x_DTP_4m'),
        'x_DTP_11m': fields.boolean('x_DTP_11m'),
        'x_DTP_6a': fields.boolean('x_DTP_6a'),
        'x_DTP_1113a': fields.boolean('x_DTP_1113a'),
        'x_DTP_25': fields.boolean('x_DTP_25'),
        'x_DTP_45': fields.boolean('x_DTP_45'),
        # Vaccins Coqueluche
        'x_coq_2m': fields.boolean('x_coq_2m'),
        'x_coq_4m': fields.boolean('x_coq_4m'),
        'x_coq_11m': fields.boolean('x_coq_11m'),
        'x_coq_6a': fields.boolean('x_coq_6a'),
        'x_coq_1113a': fields.boolean('x_coq_1113a'),
        'x_coq_25': fields.boolean('x_coq_25'),
        'x_coq_45': fields.boolean('x_coq_45'),
        # Vaccins HIB
        'x_HIB_2m': fields.boolean('x_HIB_2m'),
        'x_HIB_4m': fields.boolean('x_HIB_4m'),
        'x_HIB_11m': fields.boolean('x_HIB_11m'),
        # Vaccins HepB
        'x_HepB_2m': fields.boolean('x_HepB_2m'),
        'x_HepB_4m': fields.boolean('x_HepB_4m'),
        'x_HepB_11m': fields.boolean('x_HepB_11m'),
        # Vaccins Pneumocoque
        'x_pneumo_2m': fields.boolean('x_pneumo_2m'),
        'x_pneumo_4m': fields.boolean('x_pneumo_4m'),
        'x_pneumo_11m': fields.boolean('x_pneumo_11m'),
        # Vaccins Meningocoque C
        'x_meningo_11m': fields.boolean('x_meningo_11m'),
        # Vaccins ROR
        'x_ROR_12m': fields.boolean('x_ROR_12m'),
        'x_ROR_1618m': fields.boolean('x_ROR_1618m'),
        # Vaccins HPV
        'x_HPV_1113m': fields.boolean('x_HPV_1113m'),
        'x_HPV_14m': fields.boolean('x_HPV_14m'),
        # Vaccins Grippe


        # Reprise de CRM 
        'x_opportunity_ids': fields.one2many('crm.lead', 'partner_id',\
            'Opportunities', domain=[('type', '=', 'opportunity')]),
        'x_meeting_ids': fields.one2many('calendar.event', 'x_partner_id',
            'Meetings'),
        'x_opportunity_count': fields.function(_x_opportunity_meeting_count, string="Opportunity", type='integer', multi='opp_meet'),
        'x_meeting_count': fields.function(_x_opportunity_meeting_count, string="# Meetings", type='integer', multi='opp_meet'),
    }

    def redirect_partner_form(self, cr, uid, partner_id, context=None):
        search_view = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'base', 'view_res_partner_filter')



    _order = 'name, x_patient_prenom'

    _default = {
        'x_patient_sexe': 'masculin',
        'x_patient_cafat': '',
        'x_is_pro': False,
        'x_compte_type': 'pro',
        'x_medecin_traitant': ' ',
        'x_groupe_sang': '',
        'x_taille': '0,1',
        'x_poids': '0,1',
        'x_context': '',
    }

    _sql_constraints = [
    ]

   

    #############            Changement Praticien <-> Patient            #############
    @api.multi
    def _on_change_compte_type(self, x_compte_type):
        return {'value': {'x_is_pro': x_compte_type == 'pro'}}

    
    #############            Changement de date de naissance            #############
    @api.onchange('dob')
    def _onchange_getage_id(self,cr,uid,ids,dob,context=None):
        current_date=datetime.now()
        current_year=current_date.year
        birth_date = parser.parse(dob)
        current_age=current_year-birth_date.year

        val = {
            'age':current_age
        }
        return {'value': val}



    #############            Donne l'image a utiliser comme avatar            #############
    @api.model
    def _get_default_avatar(self, vals):
        if getattr(threading.currentThread(), 'testing', False) or self.env.context.get('install_mode'):
            return False
        # ------------------ CABINET
        if self.is_company == True:
            img_path = openerp.modules.get_module_resource('AlloDoc', 'static/src/img', 'company_image.png')
        elif self.x_compte_type == 'pro':
            if self.x_patient_sexe == 'feminin':
                img_path = openerp.modules.get_module_resource('AlloDoc', 'static/src/img', 'avatar_medecin_femme.png')
            else:
                img_path = openerp.modules.get_module_resource('AlloDoc', 'static/src/img', 'avatar_medecin_homme.png')
        # ------------------ PATIENTS
        #----------------------- Adultes
        elif self.age > 18:
            if self.x_patient_sexe == 'feminin':
                img_path = openerp.modules.get_module_resource('AlloDoc', 'static/src/img', 'avatar_femme.png')
            else:
                img_path = openerp.modules.get_module_resource('AlloDoc', 'static/src/img', 'avatar_homme.png')
        #----------------------- Enfants        
        elif self.age > 2:
            if self.x_patient_sexe == 'feminin':
                img_path = openerp.modules.get_module_resource('AlloDoc', 'static/src/img', 'avatar_fille.png')
            else:
                img_path = openerp.modules.get_module_resource('AlloDoc', 'static/src/img', 'avatar_garcon.png')
        #----------------------- Bebes
        elif self.age <= 2:
            if self.x_patient_sexe == 'feminin':
                img_path = openerp.modules.get_module_resource('AlloDoc', 'static/src/img', 'avatar_bebe_f.png')
            else:
                img_path = openerp.modules.get_module_resource('AlloDoc', 'static/src/img', 'avatar_bebe_g.png')
        #----------------------- Default
        else:
            img_path = openerp.modules.get_module_resource('AlloDoc', 'static/src/img', 'avatar_default.png')


        with open(img_path, 'rb') as f:
            x_src_avatar = f.read()

        # return img_avatar
        return tools.image_resize_image_big(x_src_avatar.encode('base64'))



    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.display_name or ''
            if record.parent_id and not record.is_company:
                if not name and record.type in ['invoice', 'delivery', 'other']:
                    name = dict(self.fields_get(cr, uid, ['type'], context=context)['type']['selection'])[record.type]
                name = "%s, %s" % (record.parent_name, name)
            if context.get('show_address_only'):
                name = self._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
            name = name.replace('\n\n','\n')
            name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            if context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((record.id, name))
        return res



    @api.multi
    def write(self, vals):

        vals['x_src_avatar'] = self._get_default_avatar(vals)
        result = super(custom_res_partner, self).write(vals)
        vals['x_src_avatar'] = self._get_default_avatar(vals)
        vals['x_ant_obst_ids'] = self.x_ant_obst_ids
        vals['x_info_grossesse_ids'] = self.x_info_grossesse_ids
        result = super(custom_res_partner, self).write(vals)
        
        return result


custom_res_partner()