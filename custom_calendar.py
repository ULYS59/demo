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

##########           MEDICAL INFO ???
# GRP_SANG_SELECTION = [
#     ('O+', 'O+'), ('O-', 'O-'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-')
# ]
##########

SEXE_SELECTION = [
    ('masculin', 'Masc.'), ('feminin', 'Fem.')
]


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
  
            
    _columns = {
        'x_domicile': fields.boolean('A domicile'),
        'x_partner_id': fields.many2one('res.partner', 'Attendee', default=''),
        'x_categ_id': fields.many2one('calendar.event.type', 'Tags'),
        'x_categ_id_char': fields.char(compute='_compute_categ_id_char', default=''),
        'x_event_is_billed': fields.boolean('is_billed'),
        'x_event_is_printed': fields.boolean('is_printed'),

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
        ########## MEDICAL INFO ???
        # 'x_event_groupe_sang': fields.related('x_partner_id', 'x_groupe_sang', type="selection", selection=GRP_SANG_SELECTION),
        # 'x_event_taille': fields.float(related='x_partner_id.x_taille'),
        # 'x_event_poids': fields.float(related='x_partner_id.x_poids'),
        # 'x_event_IMC': fields.float(related='x_partner_id.x_IMC'),
        ##########
        
        
        # related field calendar_event_type 
        # -------------------------
        'x_event_codeActe': fields.char(related='x_categ_id.x_code_acte', size=8),
        'x_event_priceActe': fields.float(related='x_categ_id.x_price_acte', digits=(4,0)),
        # -------------------------
    }
    _default = {
        'x_domicile': False,
    }


    # KEEP ???
    # @api.multi
    # def write(self, vals):
    #     vals['x_event_ag'] = self.x_event_ag
    #     result = super(custom_calendar_event, self).write(vals)
        
    #     return result

custom_calendar_event()