from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import re


class DuePayments(models.Model):
    _name = 'due.payments'
    _description = 'Due Payments'

    name = fields.Char(string='Periodo')
    d_miscellaneous_income = fields.Integer(string='D. inscripcion')
    d_regulation_cup = fields.Float(string='D. tasa de regulacion')
    d_mandatory_contribution = fields.Float(string='D. aporte obligatorio')
    d_voluntary_contribution = fields.Float(string='Aporte voluntario')
    d_post_mortem = fields.Float(string='D. post morte')
    gestion = fields.Integer(string='Gestion')
    due_partner_payroll_id = fields.Many2one('partner.payroll', string='Pagos adelantados')
